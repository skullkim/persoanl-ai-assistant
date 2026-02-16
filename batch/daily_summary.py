"""
일일 뉴스 요약 배치

당일 수집된 뉴스를 Ollama LLM으로 요약하고 Slack으로 발송합니다.
daily_collector 배치 실행 후 별도로 실행합니다.

사용법:
    python -m batch.daily_summary

배치 실행:
    APP_ENV=dev python -m batch.daily_summary

cron 설정 (매일 오전 10시 실행 예시):
    0 10 * * * cd /path/to/project && APP_ENV=dev python -m batch.daily_summary
"""
import asyncio
from datetime import datetime

from service.news_summary_service import summarize_today_news, send_news_summary_to_slack
from external.db import init_db, close_db, transactional
from external.db.repository import NewsSummaryRepository


@transactional
async def summarize_and_notify(session=None):
    """당일 뉴스 요약을 확인하고 Slack으로 발송합니다.

    이미 오늘 요약이 존재하면 그대로 발송하고,
    없으면 LLM으로 요약을 생성한 뒤 발송합니다.
    """
    today_str = datetime.now().strftime("%Y.%m.%d")

    existing = await NewsSummaryRepository.find_by_date(today_str, session)
    if existing:
        print(f"[요약] 기존 요약 {len(existing)}건 발견, Slack 발송 중...")
        summary_text = "\n\n".join(s.summary for s in existing)
        article_count = sum(len(s.source_news_ids or []) for s in existing)
    else:
        print("[요약] 기존 요약 없음, LLM 요약 시작...")
        summary_text, article_count = await summarize_today_news(session)

        if not summary_text:
            print("[요약] 요약할 뉴스가 없습니다.")
            return

        print(f"[요약] {article_count}건 요약 완료")

    try:
        await send_news_summary_to_slack(summary_text, article_count)
        print("[요약] Slack 발송 완료")
    except Exception as e:
        print(f"[경고] 요약 Slack 발송 실패: {e}")


async def run_daily_summary():
    """일일 요약 배치를 실행합니다."""
    start_time = datetime.now()
    print(f"=== 일일 요약 배치 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    try:
        await init_db()
        await summarize_and_notify()

        duration = (datetime.now() - start_time).total_seconds()
        print(f"=== 일일 요약 배치 완료 (소요시간: {duration:.2f}초) ===")

    except Exception as e:
        print(f"[오류] 요약 배치 실행 중 오류 발생: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_daily_summary())


if __name__ == "__main__":
    main()
