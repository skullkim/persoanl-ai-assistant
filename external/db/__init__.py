from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config.env_setting import settings


_engine = None


def get_engine():
    """비동기 데이터베이스 엔진을 반환합니다."""
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        _engine = create_async_engine(db_url, echo=False)
    return _engine


async def init_db():
    """데이터베이스 연결을 초기화합니다."""
    get_engine()


async def close_db():
    """데이터베이스 연결을 종료합니다."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


def get_session() -> async_sessionmaker[AsyncSession]:
    """세션 팩토리를 반환합니다."""
    engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


from .transaction import transactional

__all__ = ["init_db", "close_db", "get_session", "transactional", "AsyncSession"]
