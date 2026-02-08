from datetime import datetime
from sqlmodel import SQLModel, Field


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
    highlights: list[str] = Field(default_factory=list, sa_type_kwargs={"as_array": True})
    source: str | None = None
    sentiment: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
