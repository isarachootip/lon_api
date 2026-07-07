import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./lon_database.db")
    
    # EGG Digital Settings
    EGG_LON_API_URL: str = os.getenv("EGG_LON_API_URL", "https://smsapi-smscloud.eggdigital.com/lon/v2/send")
    EGG_WEBHOOK_FORWARD_URL: str = os.getenv("EGG_WEBHOOK_FORWARD_URL", "https://dr-smscloud.eggdigital.com/line/webhook")
    INTERNAL_AUTH_TOKEN: str = os.getenv("INTERNAL_AUTH_TOKEN", "super-secret-thai-watsadu-token")
    
    # TEST Env Settings
    EGG_LON_TEST_API_KEY: str = os.getenv("EGG_LON_TEST_API_KEY", "test_api_key_here")
    EGG_LON_TEST_SENDER_ID: str = os.getenv("EGG_LON_TEST_SENDER_ID", "ThaiWatsaduTest")
    EGG_LON_TEST_TEMPLATE_ID_DELIVERY: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_DELIVERY", "111bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_SHIPMENT_COMPLETE: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_SHIPMENT_COMPLETE", "222bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_ORDER_CONFIRMATION: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_ORDER_CONFIRMATION", "333bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_PAYMENT_COMPLETE: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_PAYMENT_COMPLETE", "444bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_PAYMENT_FAILURE: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_PAYMENT_FAILURE", "555bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_PAYMENT_REMINDER: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_PAYMENT_REMINDER", "666bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_APPLICATION_STATUS: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_APPLICATION_STATUS", "777bb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_TEST_TEMPLATE_ID_RESERVATION: str = os.getenv("EGG_LON_TEST_TEMPLATE_ID_RESERVATION", "888bb086-3ebd-4e37-b5a9-aea536220526")
    
    # PROD Env Settings
    EGG_LON_PROD_API_KEY: str = os.getenv("EGG_LON_PROD_API_KEY", "prod_api_key_here")
    EGG_LON_PROD_SENDER_ID: str = os.getenv("EGG_LON_PROD_SENDER_ID", "ThaiWatsadu")
    EGG_LON_PROD_TEMPLATE_ID_DELIVERY: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_DELIVERY", "aaaab086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_SHIPMENT_COMPLETE: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_SHIPMENT_COMPLETE", "bbbbb086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_ORDER_CONFIRMATION: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_ORDER_CONFIRMATION", "ccccc086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_PAYMENT_COMPLETE: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_PAYMENT_COMPLETE", "ddddd086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_PAYMENT_FAILURE: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_PAYMENT_FAILURE", "eeeee086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_PAYMENT_REMINDER: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_PAYMENT_REMINDER", "fffff086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_APPLICATION_STATUS: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_APPLICATION_STATUS", "00000086-3ebd-4e37-b5a9-aea536220526")
    EGG_LON_PROD_TEMPLATE_ID_RESERVATION: str = os.getenv("EGG_LON_PROD_TEMPLATE_ID_RESERVATION", "99999086-3ebd-4e37-b5a9-aea536220526")

    # SMS Gateway Settings
    SMS_GATEWAY_URL: str = os.getenv("SMS_GATEWAY_URL", "https://smsapi-smscloud.eggdigital.com/sms/v1/send")
    SMS_GATEWAY_API_KEY: str = os.getenv("SMS_GATEWAY_API_KEY", "sms_api_key_here")
    SMS_GATEWAY_SENDER_ID: str = os.getenv("SMS_GATEWAY_SENDER_ID", "ThaiWatsadu")

    def get_credentials(self, env: str) -> Dict[str, str]:
        """Returns API Key and Sender ID for the specified environment ('test' or 'prod')"""
        env = env.lower()
        if env == "prod":
            return {
                "api_key": self.EGG_LON_PROD_API_KEY,
                "sender_id": self.EGG_LON_PROD_SENDER_ID
            }
        else:
            return {
                "api_key": self.EGG_LON_TEST_API_KEY,
                "sender_id": self.EGG_LON_TEST_SENDER_ID
            }

    def get_template_id(self, env: str, template_type: str) -> Optional[str]:
        """Returns the Template UUID based on environment and template type"""
        env = env.lower()
        t_type = template_type.upper()
        
        mapping = {
            "DELIVERY": "TEMPLATE_ID_DELIVERY",
            "SHIPMENT_COMPLETE": "TEMPLATE_ID_SHIPMENT_COMPLETE",
            "ORDER_CONFIRMATION": "TEMPLATE_ID_ORDER_CONFIRMATION",
            "PAYMENT_COMPLETE": "TEMPLATE_ID_PAYMENT_COMPLETE",
            "PAYMENT_FAILURE": "TEMPLATE_ID_PAYMENT_FAILURE",
            "PAYMENT_REMINDER": "TEMPLATE_ID_PAYMENT_REMINDER",
            "APPLICATION_STATUS": "TEMPLATE_ID_APPLICATION_STATUS",
            "RESERVATION": "TEMPLATE_ID_RESERVATION",
        }
        
        suffix = mapping.get(t_type)
        if not suffix:
            return None
            
        attr_name = f"EGG_LON_{env.upper()}_{suffix}"
        return getattr(self, attr_name, None)

settings = Settings()
