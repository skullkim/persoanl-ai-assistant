"""
일일 섹터 추천 리포트 배치

최근 3일 뉴스를 분석하여 섹터별 투자 추천 리포트를 생성하고 Slack으로 발송합니다.

사용법:
    python -m batch.daily_report

배치 실행:
    APP_ENV=dev python -m batch.daily_report

cron 설정 (매일 오전 11시 실행 예시):
    0 11 * * * cd /path/to/project && APP_ENV=dev python -m batch.daily_report
"""
import asyncio
from datetime import datetime

from service.daily_report_service import generate_daily_report, send_report_to_slack
from external.db import init_db, close_db, transactional
from external.db.repository import DailyReportRepository


@transactional
async def generate_and_notify(session=None):
    """리포트를 확인하고 Slack으로 발송합니다.

    이미 오늘 리포트가 존재하면 그대로 발송하고,
    없으면 LLM으로 리포트를 생성한 뒤 발송합니다.
    """
    today_str = datetime.now().strftime("%Y.%m.%d")

    existing = await DailyReportRepository.find_by_date(today_str, session)
    if existing:
        print(f"[리포트] 기존 리포트 발견 (id={existing.id}), Slack 발송 중...")
        report_text = existing.content
        article_count = existing.source_count
    else:
        print("[리포트] 기존 리포트 없음, LLM 분석 시작...")
        report_text, article_count = await generate_daily_report(session)

        if not report_text:
            print("[리포트] 분석할 뉴스가 없습니다.")
            return

        print(f"[리포트] {article_count}건 뉴스 분석 완료")

    try:
        await send_report_to_slack(report_text, article_count)
        print("[리포트] Slack 발송 완료")
    except Exception as e:
        print(f"[경고] 리포트 Slack 발송 실패: {e}")


async def run_daily_report():
    """일일 리포트 배치를 실행합니다."""
    start_time = datetime.now()
    print(f"=== 일일 리포트 배치 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    try:
        await init_db()
        await generate_and_notify()

        duration = (datetime.now() - start_time).total_seconds()
        print(f"=== 일일 리포트 배치 완료 (소요시간: {duration:.2f}초) ===")

    except Exception as e:
        print(f"[오류] 리포트 배치 실행 중 오류 발생: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_daily_report())


if __name__ == "__main__":
    main()
