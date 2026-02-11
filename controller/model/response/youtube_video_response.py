from typing import List
from pydantic import BaseModel

class YouTubeVideoResponse(BaseModel):
    id: str
    title: str
    channelName: str
    thumbnailUrl: str
    videoUrl: str
    date: str
    subtitle: str | None
    summary: str | None
    highlights: List[str]
