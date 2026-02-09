from pydantic import BaseModel
from typing import Optional


class EmailResponse(BaseModel):
    id: str
    thread_id: Optional[str] = None
    subject: str
    sender: str
    date: str
    snippet: str
    body: Optional[str] = None
