from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import NewsSummary


class NewsSummaryRepository:
    """뉴스 일일 요약 CRUD 레포지토리"""

    @staticmethod
    async def exists_by_date_and_category(summary_date: str, category: str, session: AsyncSession) -> bool:
        """날짜와 카테고리로 중복 여부를 확인합니다."""
        stmt = select(NewsSummary.id).where(
            NewsSummary.summary_date == summary_date,
            NewsSummary.category == category
        ).limit(1)
        result = await session.exec(stmt)
        return result.first() is not None

    @staticmethod
    async def save(news_summary: NewsSummary, session: AsyncSession) -> NewsSummary:
        """뉴스 요약을 저장합니다."""
        session.add(news_summary)
        await session.flush()
        await session.refresh(news_summary)
        return news_summary

    @staticmethod
    async def find_by_date(summary_date: str, session: AsyncSession) -> list[NewsSummary]:
        """날짜별 뉴스 요약을 조회합니다."""
        stmt = (
            select(NewsSummary)
            .where(NewsSummary.summary_date == summary_date)
            .order_by(NewsSummary.category)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_id(summary_id: int, session: AsyncSession) -> NewsSummary | None:
        """ID로 뉴스 요약을 조회합니다."""
        return await session.get(NewsSummary, summary_id)
