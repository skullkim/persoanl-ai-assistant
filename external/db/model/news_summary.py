from datetime import datetime
from sqlmodel import SQLModel, Field, Column, ARRAY, BigInteger


class NewsSummary(SQLModel, table=True):
    """뉴스 일일 요약"""

    __tablename__ = "news_summary"

    id: int | None = Field(default=None, primary_key=True)
    summary_date: str
    category: str | None = None
    summary: str
    source_news_ids: list[int] | None = Field(default=None, sa_column=Column(ARRAY(BigInteger)))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
