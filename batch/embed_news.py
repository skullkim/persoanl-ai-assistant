"""
뉴스 임베딩 배치

모든 뉴스를 임베딩하여 벡터 검색이 가능하도록 합니다.
이미 임베딩된 항목은 스킵합니다 (멱등성).

사용법:
    python -m batch.embed_news

배치 실행:
    APP_ENV=dev python -m batch.embed_news
"""
import asyncio
from datetime import datetime

from service.embedding_service import embed_all_news
from external.db import init_db, close_db, transactional


@transactional
async def run_embed_news(session=None) -> int:
    """뉴스 임베딩을 실행합니다."""
    return await embed_all_news(session)


async def run_batch():
    """뉴스 임베딩 배치를 실행합니다."""
    start_time = datetime.now()
    print(f"=== 뉴스 임베딩 배치 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    try:
        await init_db()
        count = await run_embed_news()

        duration = (datetime.now() - start_time).total_seconds()
        print(f"=== 뉴스 임베딩 배치 완료 ===")
        print(f"  - 신규 임베딩: {count}건")
        print(f"  - 소요시간: {duration:.2f}초")

    except Exception as e:
        print(f"[오류] 뉴스 임베딩 배치 실패: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_batch())


if __name__ == "__main__":
    main()
