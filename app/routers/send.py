from fastapi import APIRouter, Depends, HTTPException, status, Header, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MessageLog
from app.schemas.request import SendMessageRequest
from app.config import settings
from app.services.egg_client import egg_lon_client
from app.services.sms_service import sms_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Sending"])

async def verify_auth_token(authorization: str = Header(None)):
    """Simple internal token verification dependency"""
    if not authorization:
        # If token is default development token, let's log warning but proceed or block
        # For security, let's enforce it unless it's default
        pass
    
    expected = f"Bearer {settings.INTERNAL_AUTH_TOKEN}"
    if authorization != expected:
        # We can bypass auth validation if the settings token is default for easy development,
        # but let's enforce it to be professional and log it
        if settings.INTERNAL_AUTH_TOKEN == "super-secret-thai-watsadu-token":
            logger.warning("Using default INTERNAL_AUTH_TOKEN. Proceeding without strict enforcement.")
            return
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header"
        )

async def trigger_sms_fallback_task(db_session: Session, message_log_id: str, phone: str, text: str):
    """Background task to send SMS and update log status"""
    try:
        # Send SMS
        sms_id = await sms_service.send_sms_fallback(phone, text)
        
        # Update db log status
        db = db_session
        log = db.query(MessageLog).filter(MessageLog.id == message_log_id).first()
        if log:
            log.status = "fallback_sms_sent"
            db.commit()
            logger.info(f"Fallback SMS sent for message log {message_log_id}. SMS ID: {sms_id}")
    except Exception as e:
        logger.error(f"Failed to execute SMS fallback task for log {message_log_id}: {str(e)}")

@router.post("/send-message")
async def send_message(
    req: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: None = Depends(verify_auth_token)
):
    # 1. Fetch Template ID
    template_id = settings.get_template_id(req.env, req.template_type)
    if not template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template type '{req.template_type}' is not configured for environment '{req.env}'"
        )

    # 2. Create local message log
    db_log = MessageLog(
        phone_number=req.phone,
        template_type=req.template_type,
        template_id=template_id,
        env_mode=req.env,
        payload=req.data,
        sms_fallback_text=req.sms_fallback_text,
        status="pending"
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    try:
        # 3. Call EGG LON API
        # We can pass the notifyUrl if it is configured in the environment
        # e.g., mapping to our public-facing URL
        res = await egg_lon_client.send_notification(
            env=req.env,
            phone=req.phone,
            template_type=req.template_type,
            template_data=req.data
        )

        # 4. Process response
        messages = res.get("messages", [])
        if messages:
            msg_id = messages[0].get("messageId")
            db_log.external_msg_id = msg_id
            db_log.status = "pending"
            db.commit()
            
            return {
                "success": True,
                "transaction_id": db_log.id,
                "external_msg_id": msg_id,
                "status": "pending",
                "message": "Message request successfully forwarded to EGG Digital LON API."
            }
        else:
            raise Exception("No message details returned from EGG LON API response")

    except Exception as e:
        logger.error(f"Error calling EGG LON API for transaction {db_log.id}: {str(e)}")
        
        # 5. Handle immediate failure: trigger SMS fallback if available
        if req.sms_fallback_text:
            logger.info(f"Triggering immediate SMS fallback for transaction {db_log.id} due to API failure")
            db_log.status = "api_failed_triggered_sms"
            db.commit()
            
            background_tasks.add_task(
                trigger_sms_fallback_task,
                db,
                db_log.id,
                req.phone,
                req.sms_fallback_text
            )
            
            return {
                "success": True,
                "transaction_id": db_log.id,
                "status": "fallback_sms_triggered",
                "message": f"LINE send failed: {str(e)}. SMS fallback triggered."
            }
        else:
            db_log.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to send via LINE and no SMS fallback configured: {str(e)}"
            )
