from datetime import datetime
from sqlmodel import SQLModel, Field


class NewsSource(SQLModel, table=True):
    """뉴스 소스 관리 (이메일 발신자, RSS 피드)"""

    __tablename__ = "news_sources"

    id: int | None = Field(default=None, primary_key=True)
    type: str
    identifier: str
    source_name: str
    category: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
