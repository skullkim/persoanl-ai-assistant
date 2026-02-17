from fastapi import APIRouter, Depends
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession

from external.db import get_session
from controller.model.response.news_item_response import NewsItemResponse
from service.news_service import get_news_from_emails

router = APIRouter(prefix="/api", tags=["news"])


async def get_db_session():
    """DB 세션 의존성"""
    session_factory = get_session()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get("/news", response_model=List[NewsItemResponse])
async def get_news(offsetDays: int = 0, countDays: int = 3, session: AsyncSession = Depends(get_db_session)):
    """뉴스 피드 조회 - Gmail 뉴스레터에서 수집"""
    return await get_news_from_emails(session, offset_days=offsetDays, count_days=countDays)
