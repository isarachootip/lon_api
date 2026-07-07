from pydantic import BaseModel, Field
from typing import List, Optional

class DlrStatus(BaseModel):
    groupId: int
    groupName: str
    name: Optional[str] = None
    description: Optional[str] = None

class DlrError(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permanent: Optional[bool] = None

class DlrResultItem(BaseModel):
    messageId: str = Field(..., alias="messageId")
    status: DlrStatus
    error: Optional[DlrError] = None
    sentAt: Optional[str] = None
    doneAt: Optional[str] = None
    to: Optional[str] = None

    class Config:
        populate_by_name = True

class EggDlrWebhookPayload(BaseModel):
    results: List[DlrResultItem]
