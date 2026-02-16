from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import News


class NewsRepository:
    """뉴스 CRUD 레포지토리"""

    @staticmethod
    async def exists_by_title_and_upload_date(title: str, upload_date: str, session: AsyncSession) -> bool:
        """title과 upload_date로 중복 여부를 확인합니다."""
        stmt = select(News.id).where(
            News.title == title,
            News.upload_date == upload_date
        ).limit(1)
        result = await session.exec(stmt)
        return result.first() is not None

    @staticmethod
    async def save(news: News, session: AsyncSession) -> News:
        """뉴스를 저장합니다."""
        session.add(news)
        await session.flush()
        await session.refresh(news)
        return news

    @staticmethod
    async def save_all(news_items: list[dict], session: AsyncSession) -> int:
        """뉴스 목록을 저장합니다."""
        if not news_items:
            return 0

        saved = 0
        for item in news_items:
            try:
                news = News(
                    title=item["title"],
                    summary=item.get("summary", ""),
                    content=item.get("content", ""),
                    category=item.get("category", ""),
                    upload_date=item.get("date", ""),
                    source=item.get("source", ""),
                )
                session.add(news)
                saved += 1
            except Exception as e:
                print(f"뉴스 저장 실패: {e}")

        return saved

    @staticmethod
    async def find_by_id(news_id: int, session: AsyncSession) -> News | None:
        """ID로 뉴스를 조회합니다."""
        return await session.get(News, news_id)

    @staticmethod
    async def find_all(session: AsyncSession, limit: int = 100) -> list[News]:
        """뉴스 목록을 조회합니다."""
        stmt = select(News).order_by(News.created_at.desc()).limit(limit)
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_category(category: str, session: AsyncSession, limit: int = 100) -> list[News]:
        """카테고리별 뉴스를 조회합니다."""
        stmt = (
            select(News)
            .where(News.category == category)
            .order_by(News.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def delete(news_id: int, session: AsyncSession) -> bool:
        """뉴스를 삭제합니다."""
        news = await session.get(News, news_id)
        if news:
            await session.delete(news)
            return True
        return False
