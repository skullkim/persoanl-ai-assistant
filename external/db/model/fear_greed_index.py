from datetime import datetime
from sqlmodel import SQLModel, Field


class FearGreedIndex(SQLModel, table=True):
    """공포/탐욕 지수 이력 데이터"""

    __tablename__ = "fear_greed_index"

    id: int | None = Field(default=None, primary_key=True)
    record_date: str
    value: int
    label: str
    source: str = "CNN"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
