from functools import wraps
from external.db import get_session


def transactional(func):
    """
    트랜잭션 데코레이터

    함수 실행 전 세션을 생성하고, 성공 시 commit, 실패 시 rollback 합니다.
    session 파라미터가 없으면 새 세션을 생성하고,
    이미 session이 전달되면 기존 세션을 사용합니다 (중첩 트랜잭션 지원).

    사용법:
        @transactional
        async def save(news: News, session: AsyncSession) -> News:
            session.add(news)
            return news
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 이미 세션이 전달된 경우 기존 세션 사용
        if "session" in kwargs and kwargs["session"] is not None:
            return await func(*args, **kwargs)

        # 새 세션 생성
        session_factory = get_session()
        async with session_factory() as session:
            try:
                kwargs["session"] = session
                result = await func(*args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise e

    return wrapper
