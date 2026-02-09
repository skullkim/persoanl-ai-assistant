from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String


class Video(SQLModel, table=True):
    """유튜브 영상 및 요약 데이터"""

    __tablename__ = "video"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    channel_name: str | None = None
    thumbnail_url: str | None = None
    video_url: str | None = None
    upload_date: str | None = None
    summary: str | None = None
    highlights: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    source: str | None = None
    sentiment: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
