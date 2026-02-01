from typing import List
from pydantic import BaseModel

class YouTubeVideoResponse(BaseModel):
    id: str
    title: str
    channelName: str
    thumbnailUrl: str
    videoUrl: str
    date: str
    summary: str
    highlights: List[str]
    sentiment: str
