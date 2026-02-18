from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import VideoSource


class VideoSourceRepository:
    """유튜브 채널 소스 CRUD 레포지토리"""

    @staticmethod
    async def find_active(session: AsyncSession) -> list[VideoSource]:
        """활성화된 유튜브 채널 소스를 조회합니다."""
        stmt = (
            select(VideoSource)
            .where(VideoSource.is_active == True)
            .order_by(VideoSource.id)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_all(session: AsyncSession) -> list[VideoSource]:
        """모든 유튜브 채널 소스를 조회합니다."""
        stmt = select(VideoSource).order_by(VideoSource.id)
        result = await session.exec(stmt)
        return result.all()
