from fastapi import APIRouter
from typing import List

from controller.model.response.news_item_response import NewsItemResponse
from service.news_service import get_news_from_emails

router = APIRouter(prefix="/api", tags=["news"])


@router.get("/news", response_model=List[NewsItemResponse])
def get_news(offsetDays: int = 0, countDays: int = 3):
    """뉴스 피드 조회 - Gmail 뉴스레터에서 수집"""
    return get_news_from_emails(offset_days=offsetDays, count_days=countDays)
