from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from config.env_setting import settings
import logging

logger = logging.getLogger(__name__)

_engine = None


def get_engine():
    """비동기 데이터베이스 엔진을 반환합니다."""
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        _engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args={
                "timeout": settings.DB_CONNECT_TIMEOUT,
                "command_timeout": settings.DB_COMMAND_TIMEOUT,
            },
        )
    return _engine


async def init_db():
    """데이터베이스 연결을 초기화하고 검증합니다."""
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        raise


async def close_db():
    """데이터베이스 연결을 종료합니다."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("데이터베이스 연결 종료")


async def check_db_health() -> dict:
    """데이터베이스 상태를 확인합니다."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"데이터베이스 헬스체크 실패: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


def get_session() -> async_sessionmaker[AsyncSession]:
    """세션 팩토리를 반환합니다."""
    engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


from .transaction import transactional

__all__ = ["init_db", "close_db", "get_session", "check_db_health", "transactional", "AsyncSession"]
