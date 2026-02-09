from fastapi import APIRouter
from typing import List

from controller.model.response.youtube_video_response import YouTubeVideoResponse
from service.youtube_service import get_youtube_videos as get_youtube_videos_service

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.get("/videos", response_model=List[YouTubeVideoResponse])
def get_youtube_videos(offsetDays: int = 0, countDays: int = 3):
    """유튜브 요약본 조회 - YouTube Data API에서 수집"""
    return get_youtube_videos_service(offset_days=offsetDays, count_days=countDays)
