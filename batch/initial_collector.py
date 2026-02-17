"""
초기 데이터 수집 배치

한 달 이전부터 오늘까지의 뉴스 피드를 수집하여 데이터베이스에 저장합니다.
최초 1회만 실행합니다.

사용법:
    APP_ENV=dev python -m batch.initial_collector

옵션:
    APP_ENV=dev python -m batch.initial_collector --days 60  # 60일 이전부터 수집
"""
import asyncio
import argparse
from datetime import datetime

from service.news_service import get_news_from_emails, save_news_if_not_exists
from external.db import init_db, close_db, transactional


@transactional
async def collect_news_for_day(offset_days: int, session=None) -> int:
    """특정 일자의 뉴스 피드를 수집하여 저장합니다."""
    news_items = await get_news_from_emails(session, offset_days=offset_days, count_days=1)

    if news_items:
        saved = await save_news_if_not_exists(news_items, session)
        return saved
    return 0


async def run_initial_batch(days: int = 30):
    """초기 데이터 수집 배치를 실행합니다."""
    start_time = datetime.now()
    print(f"=== 초기 데이터 수집 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"=== {days}일 전부터 오늘까지 수집 ===\n")

    total_news = 0

    try:
        await init_db()

        # 과거부터 오늘까지 순차적으로 수집 (days-1일 전 ~ 0일 전)
        for offset in range(days - 1, -1, -1):
            print(f"[Day -{offset}] 수집 중...")

            news_count = await collect_news_for_day(offset)
            total_news += news_count

            print(f"[Day -{offset}] 뉴스: {news_count}개")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n=== 초기 데이터 수집 완료 ===")
        print(f"  - 총 뉴스: {total_news}개")
        print(f"  - 소요시간: {duration:.2f}초")

    except Exception as e:
        print(f"[오류] 배치 실행 중 오류 발생: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    parser = argparse.ArgumentParser(description="초기 데이터 수집 배치")
    parser.add_argument("--days", type=int, default=30, help="수집할 일수 (기본: 30일)")
    args = parser.parse_args()

    asyncio.run(run_initial_batch(days=args.days))


if __name__ == "__main__":
    main()
