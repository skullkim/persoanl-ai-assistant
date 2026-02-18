"""
일일 뉴스 정리 배치

당일 수집된 뉴스레터를 Ollama LLM으로 주제별 통합 정리하고 Slack으로 발송합니다.

사용법:
    python -m batch.daily_summary

배치 실행:
    APP_ENV=dev python -m batch.daily_summary

특정 날짜 정리:
    APP_ENV=dev SUMMARY_DATE=2026-02-15 python -m batch.daily_summary

cron 설정 (매일 오전 10시 실행 예시):
    0 10 * * * cd /path/to/project && APP_ENV=dev python -m batch.daily_summary
"""
import asyncio
import os
from datetime import datetime

from service.news_organize_service import organize_news, send_news_briefing_to_slack
from external.db import init_db, close_db, transactional
from external.db.repository import NewsOrganizeRepository


def _resolve_target_date() -> str:
    """환경변수 SUMMARY_DATE에서 대상 날짜를 결정합니다.

    Returns:
        YYYY.MM.DD 형식의 날짜 문자열
    """
    env_date = os.environ.get("SUMMARY_DATE", "").strip()
    if env_date:
        parsed = datetime.strptime(env_date, "%Y-%m-%d")
        return parsed.strftime("%Y.%m.%d")
    return datetime.now().strftime("%Y.%m.%d")


@transactional
async def organize_and_notify(target_date: str, session=None):
    """뉴스 정리를 확인하고 Slack으로 발송합니다.

    이미 해당 날짜의 정리가 존재하면 그대로 발송하고,
    없으면 LLM으로 정리를 생성한 뒤 발송합니다.
    """
    existing = await NewsOrganizeRepository.find_by_date(target_date, session)
    if existing:
        print(f"[정리] 기존 정리 {len(existing)}건 발견, Slack 발송 중...")
        summary_text = "\n\n".join(s.content for s in existing)
        article_count = sum(len(s.source_news_ids or []) for s in existing)
    else:
        print("[정리] 기존 정리 없음, LLM 통합 정리 시작...")
        summary_text, article_count = await organize_news(target_date, session)

        if not summary_text:
            print("[정리] 정리할 뉴스가 없습니다.")
            return

        print(f"[정리] {article_count}건 정리 완료")

    try:
        await send_news_briefing_to_slack(summary_text, article_count, target_date)
        print("[정리] Slack 발송 완료")
    except Exception as e:
        print(f"[경고] 정리 Slack 발송 실패: {e}")


async def run_daily_organize():
    """일일 뉴스 정리 배치를 실행합니다."""
    start_time = datetime.now()
    target_date = _resolve_target_date()
    print(f"=== 일일 뉴스 정리 배치 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (대상 날짜: {target_date}) ===")

    try:
        await init_db()
        await organize_and_notify(target_date)

        duration = (datetime.now() - start_time).total_seconds()
        print(f"=== 일일 뉴스 정리 배치 완료 (소요시간: {duration:.2f}초) ===")

    except Exception as e:
        print(f"[오류] 정리 배치 실행 중 오류 발생: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_daily_organize())


if __name__ == "__main__":
    main()
