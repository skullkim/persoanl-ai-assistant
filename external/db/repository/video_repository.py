from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import Video


class VideoRepository:
    """유튜브 영상 CRUD 레포지토리"""

    @staticmethod
    async def save(video: Video, session: AsyncSession) -> Video:
        """영상을 저장합니다."""
        session.add(video)
        await session.flush()
        await session.refresh(video)
        return video

    @staticmethod
    async def save_all(videos: list[dict], session: AsyncSession) -> int:
        """영상 목록을 저장합니다."""
        if not videos:
            return 0

        saved = 0
        for video in videos:
            try:
                v = Video(
                    title=video["title"],
                    channel_name=video.get("channelName", ""),
                    thumbnail_url=video.get("thumbnailUrl", ""),
                    video_url=video.get("videoUrl", ""),
                    upload_date=video.get("date", ""),
                    subtitle=video.get("subtitle"),
                    summary=video.get("summary"),
                    highlights=video.get("highlights", []),
                )
                session.add(v)
                saved += 1
            except Exception as e:
                print(f"유튜브 저장 실패: {e}")

        return saved

    @staticmethod
    async def find_by_id(video_id: int, session: AsyncSession) -> Video | None:
        """ID로 영상을 조회합니다."""
        return await session.get(Video, video_id)

    @staticmethod
    async def find_all(session: AsyncSession, limit: int = 100) -> list[Video]:
        """영상 목록을 조회합니다."""
        stmt = select(Video).order_by(Video.created_at.desc()).limit(limit)
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_channel(channel_name: str, session: AsyncSession, limit: int = 100) -> list[Video]:
        """채널별 영상을 조회합니다."""
        stmt = (
            select(Video)
            .where(Video.channel_name == channel_name)
            .order_by(Video.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def delete(video_id: int, session: AsyncSession) -> bool:
        """영상을 삭제합니다."""
        video = await session.get(Video, video_id)
        if video:
            await session.delete(video)
            return True
        return False
