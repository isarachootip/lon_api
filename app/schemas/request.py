from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Any, Optional
import re

class SendMessageRequest(BaseModel):
    env: str = Field("test", description="Target environment: 'test' or 'prod'")
    phone: str = Field(..., description="Recipient phone number (e.g., 0812345678 or 66812345678)")
    template_type: str = Field(..., description="LINE template type, e.g. DELIVERY, PAYMENT_COMPLETE, etc.")
    data: Dict[str, Any] = Field(..., description="Key-value pairs matching the EGG LON template requirements")
    sms_fallback_text: Optional[str] = Field(None, description="Optional SMS fallback message text")

    @field_validator("env")
    def validate_env(cls, v):
        v_low = v.lower()
        if v_low not in ["test", "prod"]:
            raise ValueError("Environment must be either 'test' or 'prod'")
        return v_low

    @field_validator("phone")
    def normalize_phone(cls, v):
        # Remove spaces, dashes, or parentheses
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        # Handle +66 prefix
        if cleaned.startswith("+66"):
            cleaned = cleaned[1:]
        elif cleaned.startswith("0"):
            cleaned = "66" + cleaned[1:]
            
        if not re.match(r"^66\d{9}$", cleaned):
            raise ValueError("Phone number must be a valid Thai mobile number (e.g., 0812345678 or 66812345678)")
        return cleaned

    @field_validator("template_type")
    def validate_template_type(cls, v):
        v_upper = v.upper()
        valid_types = [
            "DELIVERY",
            "SHIPMENT_COMPLETE",
            "ORDER_CONFIRMATION",
            "PAYMENT_COMPLETE",
            "PAYMENT_FAILURE",
            "PAYMENT_REMINDER",
            "APPLICATION_STATUS",
            "RESERVATION"
        ]
        if v_upper not in valid_types:
            raise ValueError(f"Template type must be one of: {', '.join(valid_types)}")
        return v_upper

    @model_validator(mode="after")
    def validate_template_fields(self):
        t_type = self.template_type
        fields = self.data

        required_fields = {
            "DELIVERY": ["deliveryDate"],
            "SHIPMENT_COMPLETE": ["productName"],
            "ORDER_CONFIRMATION": ["productName"],
            "PAYMENT_COMPLETE": ["methodOfPayment"],
            "PAYMENT_FAILURE": ["methodOfPayment", "orderId"],
            "PAYMENT_REMINDER": ["contractContents", "paymentDate"],
            "APPLICATION_STATUS": ["productName", "timeReceived"],
            "RESERVATION": ["reservationDate", "reservationDetails"],
        }

        req = required_fields.get(t_type, [])
        missing = [f for f in req if f not in fields or not str(fields[f]).strip()]
        if missing:
            raise ValueError(f"Template '{t_type}' requires fields: {', '.join(req)}. Missing: {', '.join(missing)}")
            
        return self
