import httpx
import uuid
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class EggLonClient:
    def __init__(self):
        self.api_url = settings.EGG_LON_API_URL

    async def send_notification(
        self,
        env: str,
        phone: str,
        template_type: str,
        template_data: Dict[str, Any],
        notify_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends a notification request to EGG Digital's LON API.
        If using default mock credentials, simulates a successful response.
        """
        creds = settings.get_credentials(env)
        api_key = creds["api_key"]
        sender_id = creds["sender_id"]
        
        template_id = settings.get_template_id(env, template_type)
        if not template_id:
            raise ValueError(f"No template ID configured for env '{env}' and template type '{template_type}'")

        # Construct the payload
        template_payload = {
            "id": template_id,
            "type": template_type,
            **template_data
        }

        destination_item = {
            "to": phone,
            "messageId": str(uuid.uuid4())  # Client side transaction ID mapped to this destination
        }

        payload = {
            "template": template_payload,
            "destinations": [destination_item],
            "from": sender_id
        }

        # Optional: Add webhook URL for delivery reports (DLR)
        if notify_url:
            payload["notifyUrl"] = notify_url
            payload["notifyContentType"] = "application/json"

        # Mock implementation for test/development
        if api_key == "test_api_key_here" or api_key == "prod_api_key_here":
            logger.info(f"[MOCK] Sending to EGG LON ({env.upper()}): {payload}")
            mock_msg_id = str(uuid.uuid4())
            return {
                "mocked": True,
                "messages": [
                    {
                        "messageId": mock_msg_id,
                        "status": {
                            "groupId": 1,
                            "groupName": "PENDING",
                            "id": 26,
                            "name": "PENDING_ACCEPTED",
                            "description": "Message sent to next instance (Simulated)"
                        },
                        "to": phone
                    }
                ]
            }

        # Real API Call
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"EGG LON API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"EGG LON API returned status {e.response.status_code}: {e.response.text}")
            except Exception as e:
                logger.error(f"EGG LON API connection failed: {str(e)}")
                raise Exception(f"Failed to connect to EGG LON API: {str(e)}")

egg_lon_client = EggLonClient()
