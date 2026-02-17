from datetime import datetime
from sqlmodel import SQLModel, Field, Column, ARRAY, BigInteger


class NewsOrganize(SQLModel, table=True):
    """뉴스 일일 정리"""

    __tablename__ = "news_organize"

    id: int | None = Field(default=None, primary_key=True)
    summary_date: str
    category: str | None = None
    content: str
    source_news_ids: list[int] | None = Field(default=None, sa_column=Column(ARRAY(BigInteger)))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
