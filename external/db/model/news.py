from datetime import datetime
from sqlmodel import SQLModel, Field


class News(SQLModel, table=True):
    """뉴스레터 원문 데이터"""

    __tablename__ = "news"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    summary: str | None = None
    content: str | None = None
    category: str | None = None
    upload_date: str | None = None
    source: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
