from fastapi import APIRouter, Depends, BackgroundTasks, Request, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MessageLog, DlrLog
from app.schemas.webhook import EggDlrWebhookPayload
from app.services.sms_service import sms_service
from app.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhook", tags=["Webhooks"])

async def send_sms_fallback_task(db_session: Session, log_id: str, phone: str, text: str):
    """Asynchronously triggers the SMS fallback gateway and updates DB log status"""
    try:
        sms_id = await sms_service.send_sms_fallback(phone, text)
        db = db_session
        log = db.query(MessageLog).filter(MessageLog.id == log_id).first()
        if log:
            log.status = "fallback_sms_sent"
            db.commit()
            logger.info(f"DLR fallback SMS sent for transaction {log_id}. SMS ID: {sms_id}")
    except Exception as e:
        logger.error(f"Failed to execute fallback SMS from webhook trigger: {str(e)}")

def process_dlr_results(payload: EggDlrWebhookPayload, db: Session, background_tasks: BackgroundTasks):
    for item in payload.results:
        # Find message log by external_msg_id
        log = db.query(MessageLog).filter(MessageLog.external_msg_id == item.messageId).first()
        if not log:
            logger.warning(f"Received DLR for unknown external message ID: {item.messageId}")
            continue

        # Save DlrLog
        dlr_log = DlrLog(
            message_log_id=log.id,
            status_group_id=item.status.groupId,
            status_group_name=item.status.groupName,
            status_name=item.status.name,
            status_description=item.status.description,
            error_id=item.error.id if item.error else None,
            error_name=item.error.name if item.error else None,
            sent_to=item.to,
            event_time=item.doneAt or item.sentAt
        )
        db.add(dlr_log)

        # Update MessageLog status based on groupId
        # 1: PENDING, 3: DELIVERED (success), 2: UNDELIVERABLE (fail), 4: EXPIRED (fail), 5: REJECTED (fail)
        group_id = item.status.groupId
        if group_id == 3:
            log.status = "delivered"
            logger.info(f"Transaction {log.id} successfully delivered to handset.")
        elif group_id in [2, 4, 5]:
            log.status = "undeliverable"
            logger.warning(f"Transaction {log.id} failed delivery. Status: {item.status.groupName}")
            
            # Trigger SMS fallback if it hasn't been triggered already
            if log.sms_fallback_text and log.status not in ["fallback_sms_sent", "api_failed_triggered_sms"]:
                background_tasks.add_task(
                    send_sms_fallback_task,
                    db,
                    log.id,
                    log.phone_number,
                    log.sms_fallback_text
                )
        db.commit()

@router.post("/egg-dlr")
async def receive_egg_dlr(
    payload: EggDlrWebhookPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint to receive EGG Digital LON Delivery Reports (DLR).
    Processes updates in the background to respond immediately.
    """
    logger.info(f"Received EGG DLR Webhook: {len(payload.results)} items")
    # For background task safety, we can process results, but background_tasks will run after response is sent.
    background_tasks.add_task(process_dlr_results, payload, db, background_tasks)
    return {"status": "accepted"}

@router.post("/line-center/{webhook_id}")
async def line_center_webhook(
    webhook_id: str,
    request: Request,
    response: Response
):
    """
    Forwards incoming customer LINE OA events from Thai Watsadu's webhook 
    to EGG Digital's LINE Webhook.
    """
    body = await request.body()
    
    # Target URL
    target_url = f"{settings.EGG_WEBHOOK_FORWARD_URL.rstrip('/')}/{webhook_id}"
    
    # Copy relevant headers
    headers = {}
    for h in ["x-line-signature", "content-type"]:
        val = request.headers.get(h)
        if val:
            headers[h] = val
            
    # Specifications say User-Agent must be LineBotWebhook/2.0
    headers["User-Agent"] = "LineBotWebhook/2.0"
    
    logger.info(f"Forwarding LINE OA event for webhook {webhook_id} to EGG Digital")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(target_url, content=body, headers=headers)
            response.status_code = res.status_code
            
            # Check content-type before trying to parse JSON
            res_content_type = res.headers.get("content-type", "")
            if "application/json" in res_content_type:
                return res.json()
            return res.text
        except Exception as e:
            logger.error(f"Failed to forward webhook to EGG: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to forward LINE event: {str(e)}"
            )
