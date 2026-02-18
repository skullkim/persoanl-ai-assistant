from datetime import datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field


class ExchangeRateHistory(SQLModel, table=True):
    """환율 이력 데이터 (USD/KRW)"""

    __tablename__ = "exchange_rate_history"

    id: int | None = Field(default=None, primary_key=True)
    record_date: str
    rate: Decimal
    previous_rate: Decimal | None = None
    change_amount: Decimal | None = None
    change_percentage: Decimal | None = None
    source: str = "Yahoo Finance"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
