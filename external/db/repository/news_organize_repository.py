from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import NewsOrganize


class NewsOrganizeRepository:
    """뉴스 일일 정리 CRUD 레포지토리"""

    @staticmethod
    async def exists_by_date_and_category(summary_date: str, category: str, session: AsyncSession) -> bool:
        """날짜와 카테고리로 중복 여부를 확인합니다."""
        stmt = select(NewsOrganize.id).where(
            NewsOrganize.summary_date == summary_date,
            NewsOrganize.category == category
        ).limit(1)
        result = await session.exec(stmt)
        return result.first() is not None

    @staticmethod
    async def save(news_organize: NewsOrganize, session: AsyncSession) -> NewsOrganize:
        """뉴스 정리를 저장합니다."""
        session.add(news_organize)
        await session.flush()
        await session.refresh(news_organize)
        return news_organize

    @staticmethod
    async def find_by_date(summary_date: str, session: AsyncSession) -> list[NewsOrganize]:
        """날짜별 뉴스 정리를 조회합니다."""
        stmt = (
            select(NewsOrganize)
            .where(NewsOrganize.summary_date == summary_date)
            .order_by(NewsOrganize.category)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_id(organize_id: int, session: AsyncSession) -> NewsOrganize | None:
        """ID로 뉴스 정리를 조회합니다."""
        return await session.get(NewsOrganize, organize_id)
