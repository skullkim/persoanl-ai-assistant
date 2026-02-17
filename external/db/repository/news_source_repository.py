from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import NewsSource


class NewsSourceRepository:
    """뉴스 소스 CRUD 레포지토리"""

    @staticmethod
    async def find_active_by_type(source_type: str, session: AsyncSession) -> list[NewsSource]:
        """활성화된 소스를 타입별로 조회합니다."""
        stmt = (
            select(NewsSource)
            .where(NewsSource.type == source_type, NewsSource.is_active == True)
            .order_by(NewsSource.id)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_all(session: AsyncSession) -> list[NewsSource]:
        """모든 소스를 조회합니다."""
        stmt = select(NewsSource).order_by(NewsSource.id)
        result = await session.exec(stmt)
        return result.all()
