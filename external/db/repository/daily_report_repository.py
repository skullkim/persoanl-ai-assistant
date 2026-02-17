from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import DailyReport


class DailyReportRepository:
    """일일 리포트 CRUD 레포지토리"""

    @staticmethod
    async def save(report: DailyReport, session: AsyncSession) -> DailyReport:
        """리포트를 저장합니다."""
        session.add(report)
        await session.flush()
        await session.refresh(report)
        return report

    @staticmethod
    async def find_by_date(report_date: str, session: AsyncSession) -> DailyReport | None:
        """날짜로 리포트를 조회합니다."""
        stmt = select(DailyReport).where(DailyReport.report_date == report_date)
        result = await session.exec(stmt)
        return result.first()

    @staticmethod
    async def find_by_id(report_id: int, session: AsyncSession) -> DailyReport | None:
        """ID로 리포트를 조회합니다."""
        return await session.get(DailyReport, report_id)

    @staticmethod
    async def find_all(session: AsyncSession, limit: int = 30) -> list[DailyReport]:
        """리포트 목록을 조회합니다."""
        stmt = select(DailyReport).order_by(DailyReport.report_date.desc()).limit(limit)
        result = await session.exec(stmt)
        return result.all()
