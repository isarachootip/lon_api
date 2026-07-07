import httpx
import uuid
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class SmsService:
    def __init__(self):
        self.gateway_url = settings.SMS_GATEWAY_URL
        self.api_key = settings.SMS_GATEWAY_API_KEY
        self.sender_id = settings.SMS_GATEWAY_SENDER_ID

    async def send_sms_fallback(self, phone: str, text: str) -> str:
        """
        Sends an SMS fallback message using EGG Digital SMS API.
        If using mock credentials, simulates a successful response.
        Returns the SMS transaction ID.
        """
        payload = {
            "from": self.sender_id,
            "to": phone,
            "text": text
        }

        # Mock implementation for test/development
        if self.api_key == "sms_api_key_here":
            logger.info(f"[MOCK SMS FALLBACK] Sending SMS to {phone}: '{text}'")
            mock_sms_id = f"sms-{uuid.uuid4()}"
            return mock_sms_id

        # Real API Call
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.gateway_url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                # Assuming standard response returns some ID
                # Adjust key names based on actual SMS gateway specs if needed
                sms_id = res_data.get("smsId") or res_data.get("messageId") or str(uuid.uuid4())
                logger.info(f"SMS successfully sent to {phone}, gateway ID: {sms_id}")
                return sms_id
            except httpx.HTTPStatusError as e:
                logger.error(f"SMS API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"SMS API returned status {e.response.status_code}: {e.response.text}")
            except Exception as e:
                logger.error(f"SMS API connection failed: {str(e)}")
                raise Exception(f"Failed to connect to SMS API: {str(e)}")

sms_service = SmsService()
