from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import FearGreedIndex


class FearGreedIndexRepository:
    """공포/탐욕 지수 CRUD 레포지토리"""

    @staticmethod
    async def save(record: FearGreedIndex, session: AsyncSession) -> FearGreedIndex:
        """공포/탐욕 지수를 저장합니다."""
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record

    @staticmethod
    async def exists_by_date(record_date: str, session: AsyncSession) -> bool:
        """해당 날짜의 공포/탐욕 지수가 존재하는지 확인합니다."""
        stmt = select(FearGreedIndex.id).where(
            FearGreedIndex.record_date == record_date
        ).limit(1)
        result = await session.exec(stmt)
        return result.first() is not None

    @staticmethod
    async def find_by_date(record_date: str, session: AsyncSession) -> FearGreedIndex | None:
        """날짜로 공포/탐욕 지수를 조회합니다."""
        stmt = select(FearGreedIndex).where(
            FearGreedIndex.record_date == record_date
        )
        result = await session.exec(stmt)
        return result.first()

    @staticmethod
    async def find_recent(session: AsyncSession, limit: int = 30) -> list[FearGreedIndex]:
        """최근 공포/탐욕 지수를 조회합니다."""
        stmt = (
            select(FearGreedIndex)
            .order_by(FearGreedIndex.record_date.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()
