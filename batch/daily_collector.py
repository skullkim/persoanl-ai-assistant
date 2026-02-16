"""
일일 데이터 수집 배치

뉴스 피드와 유튜브 요약본을 수집하여 데이터베이스에 저장합니다.
cron 또는 스케줄러를 통해 하루에 한 번 실행됩니다.

사용법:
    python -m batch.daily_collector

배치 실행:
    APP_ENV=dev python -m batch.daily_collector그

cron 설정 (매일 오전 9시 실행 예시):
    0 9 * * * cd /path/to/project && APP_ENV=dev python -m batch.daily_collector
"""
import asyncio
from datetime import datetime

from service.news_service import get_news_from_emails, save_news_if_not_exists
from service.youtube_service import get_youtube_videos, save_videos_if_not_exists
from service.rss_news_service import get_news_from_rss, save_rss_news_if_not_exists
from service.slack_notification_service import notify_batch_result
from external.db import init_db, close_db, transactional


@transactional
async def collect_news(session=None) -> int:
    """오늘의 뉴스 피드를 수집하여 저장합니다."""
    print("[뉴스] 수집 시작...")

    news_items = get_news_from_emails(offset_days=0, count_days=1)
    print(f"[뉴스] {len(news_items)}개 조회됨")

    if news_items:
        saved = await save_news_if_not_exists(news_items, session)
        print(f"[뉴스] {saved}개 저장됨")
        return saved
    return 0


@transactional
async def collect_youtube(session=None) -> int:
    """오늘의 유튜브 영상을 수집하여 저장합니다."""
    print("[유튜브] 수집 시작...")

    videos = get_youtube_videos(offset_days=0, count_days=1)
    print(f"[유튜브] {len(videos)}개 조회됨")

    if videos:
        saved = await save_videos_if_not_exists(videos, session)
        print(f"[유튜브] {saved}개 저장됨")
        return saved
    return 0


@transactional
async def collect_rss_news(session=None) -> int:
    """RSS 피드에서 뉴스를 수집하여 저장합니다."""
    print("[RSS] 수집 시작...")

    news_items = get_news_from_rss(offset_days=0, count_days=3)
    print(f"[RSS] {len(news_items)}개 조회됨")

    if news_items:
        saved = await save_rss_news_if_not_exists(news_items, session)
        print(f"[RSS] {saved}개 저장됨")
        return saved
    return 0


async def run_daily_batch():
    """일일 배치를 실행합니다."""
    start_time = datetime.now()
    print(f"=== 일일 배치 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    try:
        await init_db()

        news_count = await collect_news()
        youtube_count = await collect_youtube()
        rss_count = await collect_rss_news()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"=== 일일 배치 완료 ===")
        print(f"  - 뉴스: {news_count}개")
        print(f"  - 유튜브: {youtube_count}개")
        print(f"  - RSS: {rss_count}개")
        print(f"  - 소요시간: {duration:.2f}초")

        try:
            await notify_batch_result(news_count, youtube_count, duration, rss_count)
        except Exception as e:
            print(f"[경고] Slack 알림 전송 실패 (무시): {e}")

    except Exception as e:
        print(f"[오류] 배치 실행 중 오류 발생: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_daily_batch())


if __name__ == "__main__":
    main()
