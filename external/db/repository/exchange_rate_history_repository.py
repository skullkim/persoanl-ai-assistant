from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import ExchangeRateHistory


class ExchangeRateHistoryRepository:
    """환율 이력 CRUD 레포지토리"""

    @staticmethod
    async def save(record: ExchangeRateHistory, session: AsyncSession) -> ExchangeRateHistory:
        """환율 이력을 저장합니다."""
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record

    @staticmethod
    async def exists_by_date(record_date: str, session: AsyncSession) -> bool:
        """해당 날짜의 환율 이력이 존재하는지 확인합니다."""
        stmt = select(ExchangeRateHistory.id).where(
            ExchangeRateHistory.record_date == record_date
        ).limit(1)
        result = await session.exec(stmt)
        return result.first() is not None

    @staticmethod
    async def find_by_date(record_date: str, session: AsyncSession) -> ExchangeRateHistory | None:
        """날짜로 환율 이력을 조회합니다."""
        stmt = select(ExchangeRateHistory).where(
            ExchangeRateHistory.record_date == record_date
        )
        result = await session.exec(stmt)
        return result.first()

    @staticmethod
    async def find_recent(session: AsyncSession, limit: int = 30) -> list[ExchangeRateHistory]:
        """최근 환율 이력을 조회합니다."""
        stmt = (
            select(ExchangeRateHistory)
            .order_by(ExchangeRateHistory.record_date.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()
