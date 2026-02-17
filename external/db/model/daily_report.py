from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class DailyReport(SQLModel, table=True):
    """일일 섹터 추천 리포트"""

    __tablename__ = "daily_reports"

    id: int | None = Field(default=None, primary_key=True)
    report_date: str
    content: str
    sectors: dict | None = Field(default=None, sa_column=Column(JSONB))
    source_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
