from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from config.env_setting import settings
import logging

logger = logging.getLogger(__name__)

_engine = None

# 연결 풀 설정
POOL_SIZE = 5  # 기본 연결 풀 크기
MAX_OVERFLOW = 10  # 풀 초과 시 추가 생성 가능한 연결 수
POOL_TIMEOUT = 30  # 연결 대기 타임아웃 (초)
POOL_RECYCLE = 1800  # 연결 재사용 주기 (초, 30분)
CONNECT_TIMEOUT = 10  # DB 연결 타임아웃 (초)


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
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=True,  # 연결 사용 전 유효성 검사
            connect_args={
                "timeout": CONNECT_TIMEOUT,
                "command_timeout": 60,  # 쿼리 실행 타임아웃 (초)
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
