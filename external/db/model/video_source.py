from datetime import datetime
from sqlmodel import SQLModel, Field


class VideoSource(SQLModel, table=True):
    """유튜브 채널 소스 관리"""

    __tablename__ = "video_sources"

    id: int | None = Field(default=None, primary_key=True)
    channel_handle: str
    channel_name: str
    category: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
