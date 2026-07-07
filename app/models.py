from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    phone_number = Column(String(20), nullable=False, index=True)
    template_type = Column(String(50), nullable=False)
    template_id = Column(String(50), nullable=False)
    env_mode = Column(String(10), nullable=False, index=True)  # test | prod
    payload = Column(JSON, nullable=True)                      # Raw data payload sent to EGG
    external_msg_id = Column(String(50), nullable=True, index=True)  # messageId from EGG
    status = Column(String(30), nullable=False, default="pending", index=True)  # pending | delivered | undeliverable | fallback_sms
    sms_fallback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dlr_logs = relationship("DlrLog", back_populates="message_log", cascade="all, delete-orphan")

class DlrLog(Base):
    __tablename__ = "dlr_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_log_id = Column(String(36), ForeignKey("message_logs.id", ondelete="CASCADE"), nullable=False)
    status_group_id = Column(Integer, nullable=False)
    status_group_name = Column(String(50), nullable=True)
    status_name = Column(String(50), nullable=True)
    status_description = Column(String(255), nullable=True)
    error_id = Column(Integer, nullable=True)
    error_name = Column(String(50), nullable=True)
    sent_to = Column(String(20), nullable=True)
    event_time = Column(String(50), nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)

    message_log = relationship("MessageLog", back_populates="dlr_logs")
