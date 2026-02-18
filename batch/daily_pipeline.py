"""
일일 배치 파이프라인

모든 일일 배치를 순차 실행합니다. 각 단계가 끝나면 즉시 다음 단계로 넘어갑니다.
DB 연결은 파이프라인 시작 시 1회만 수행합니다.

실행 순서:
    1. 데이터 수집 (뉴스/유튜브/RSS)
    2. 뉴스 임베딩
    3. PDF 임베딩
    4. 뉴스 요약 → Slack
    5. 섹터 추천 리포트 → Slack

사용법:
    python -m batch.daily_pipeline

배치 실행:
    APP_ENV=dev python -m batch.daily_pipeline

cron 설정 (매일 오전 6시 30분):
    30 6 * * * cd /path/to/project && APP_ENV=dev python -m batch.daily_pipeline
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from external.db import init_db, close_db, transactional
from service.slack_notification_service import notify_batch_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_DIR = Path("./data/pdf")


# ──────────────────────────────────────────────
# Step 1: 데이터 수집
# ──────────────────────────────────────────────
@transactional
async def step_collect(session=None) -> dict:
    """뉴스, 유튜브, RSS 데이터를 수집합니다."""
    from service.news_service import get_news_from_emails, save_news_if_not_exists
    from service.youtube_service import get_youtube_videos, save_videos_if_not_exists
    from service.rss_news_service import get_news_from_rss, save_rss_news_if_not_exists

    # 뉴스
    print("[수집] 뉴스 수집 시작...")
    news_items = await get_news_from_emails(session, offset_days=0, count_days=1)
    news_count = 0
    if news_items:
        news_count = await save_news_if_not_exists(news_items, session)
    print(f"[수집] 뉴스 {news_count}개 저장")

    # 유튜브
    print("[수집] 유튜브 수집 시작...")
    videos = await get_youtube_videos(session, offset_days=0, count_days=1)
    youtube_count = 0
    if videos:
        youtube_count = await save_videos_if_not_exists(videos, session)
    print(f"[수집] 유튜브 {youtube_count}개 저장")

    # RSS
    print("[수집] RSS 수집 시작...")
    rss_items = await get_news_from_rss(session, offset_days=0, count_days=3)
    rss_count = 0
    if rss_items:
        rss_count = await save_rss_news_if_not_exists(rss_items, session)
    print(f"[수집] RSS {rss_count}개 저장")

    # 환율
    from service.market_data_service import collect_exchange_rate, collect_fear_greed_index

    print("[수집] 환율 수집 시작...")
    exchange_count = await collect_exchange_rate(session)
    print(f"[수집] 환율 {exchange_count}건 저장")

    # 공포/탐욕 지수
    print("[수집] 공포/탐욕 지수 수집 시작...")
    fear_greed_count = await collect_fear_greed_index(session)
    print(f"[수집] 공포/탐욕 지수 {fear_greed_count}건 저장")

    return {
        "news": news_count, "youtube": youtube_count, "rss": rss_count,
        "exchange_rate": exchange_count, "fear_greed": fear_greed_count,
    }


# ──────────────────────────────────────────────
# Step 2: 뉴스 임베딩
# ──────────────────────────────────────────────
@transactional
async def step_embed_news(session=None) -> int:
    """신규 뉴스를 임베딩합니다."""
    from service.embedding_service import embed_all_news

    print("[임베딩] 뉴스 임베딩 시작...")
    count = await embed_all_news(session)
    print(f"[임베딩] 뉴스 {count}건 임베딩 완료")
    return count


# ──────────────────────────────────────────────
# Step 3: PDF 임베딩
# ──────────────────────────────────────────────
@transactional
async def step_embed_single_pdf(file_path: str, session=None) -> int:
    """단일 PDF를 파싱 → 청크 → 임베딩합니다."""
    from external.pdf_parser import extract_text_from_pdf, extract_pages_text
    from service.text_chunker import chunk_pages
    from service.embedding_service import embed_pdf_chunks
    from external.db.model import PdfDocument, PdfChunk
    from external.db.repository import PdfDocumentRepository, PdfChunkRepository

    _, metadata = extract_text_from_pdf(file_path)

    existing = await PdfDocumentRepository.find_by_hash(metadata["file_hash"], session)
    if existing:
        print(f"  [스킵] 이미 처리됨: {metadata['title']}")
        return 0

    pdf_doc = PdfDocument(
        title=metadata["title"],
        author=metadata["author"],
        file_hash=metadata["file_hash"],
        total_pages=metadata["total_pages"],
    )
    pdf_doc = await PdfDocumentRepository.save(pdf_doc, session)

    pages = extract_pages_text(file_path)
    chunk_dicts = chunk_pages(pages, chunk_size=1000, overlap=200)
    if not chunk_dicts:
        print(f"  [경고] 텍스트 추출 실패: {metadata['title']}")
        return 0

    chunks = []
    for cd in chunk_dicts:
        chunks.append(PdfChunk(
            document_id=pdf_doc.id,
            chunk_index=cd["chunk_index"],
            content=cd["content"],
            page_start=cd["page_start"],
            page_end=cd["page_end"],
            token_count=len(cd["content"]),
        ))
    await PdfChunkRepository.save_all(chunks, session)

    embedded = await embed_pdf_chunks(pdf_doc.id, session)
    print(f"  [완료] {metadata['title']}: {len(chunks)}청크, {embedded}임베딩")
    return embedded


async def step_embed_pdf() -> int:
    """./data/pdf/ 폴더의 모든 PDF를 임베딩합니다."""
    print("[임베딩] PDF 임베딩 시작...")

    if not PDF_DIR.exists():
        PDF_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("[임베딩] PDF 파일 없음")
        return 0

    print(f"[임베딩] {len(pdf_files)}개 PDF 발견")
    total = 0
    for pdf_path in pdf_files:
        try:
            count = await step_embed_single_pdf(str(pdf_path))
            total += count
        except Exception as e:
            print(f"  [오류] {pdf_path.name}: {e}")

    print(f"[임베딩] PDF {total}건 임베딩 완료")
    return total


# ──────────────────────────────────────────────
# Step 4: 뉴스 정리
# ──────────────────────────────────────────────
@transactional
async def step_organize_news(session=None):
    """당일 뉴스를 주제별로 통합 정리하고 Slack으로 발송합니다."""
    from service.news_organize_service import organize_news, send_news_briefing_to_slack
    from external.db.repository import NewsOrganizeRepository

    print("[정리] 뉴스 통합 정리 시작...")
    today_str = datetime.now().strftime("%Y.%m.%d")

    existing = await NewsOrganizeRepository.find_by_date(today_str, session)
    if existing:
        print(f"[정리] 기존 정리 {len(existing)}건 발견")
        summary_text = "\n\n".join(s.content for s in existing)
        article_count = sum(len(s.source_news_ids or []) for s in existing)
    else:
        summary_text, article_count = await organize_news(today_str, session)
        if not summary_text:
            print("[정리] 정리할 뉴스가 없습니다.")
            return
        print(f"[정리] {article_count}건 정리 완료")

    try:
        await send_news_briefing_to_slack(summary_text, article_count, today_str)
        print("[정리] Slack 발송 완료")
    except Exception as e:
        print(f"[경고] 정리 Slack 발송 실패: {e}")


# ──────────────────────────────────────────────
# Step 5: 섹터 추천 리포트
# ──────────────────────────────────────────────
@transactional
async def step_daily_report(session=None):
    """섹터 추천 리포트를 생성하고 Slack으로 발송합니다."""
    from service.daily_report_service import generate_daily_report, send_report_to_slack
    from external.db.repository import DailyReportRepository

    print("[리포트] 섹터 추천 리포트 시작...")
    today_str = datetime.now().strftime("%Y.%m.%d")

    existing = await DailyReportRepository.find_by_date(today_str, session)
    if existing:
        print(f"[리포트] 기존 리포트 발견 (id={existing.id})")
        report_text = existing.content
        article_count = existing.source_count
    else:
        report_text, article_count = await generate_daily_report(session)
        if not report_text:
            print("[리포트] 분석할 뉴스가 없습니다.")
            return
        print(f"[리포트] {article_count}건 분석 완료")

    try:
        await send_report_to_slack(report_text, article_count)
        print("[리포트] Slack 발송 완료")
    except Exception as e:
        print(f"[경고] 리포트 Slack 발송 실패: {e}")


# ──────────────────────────────────────────────
# 파이프라인 실행
# ──────────────────────────────────────────────
STEPS = [
    ("1/5 데이터 수집", step_collect),
    ("2/5 뉴스 임베딩", step_embed_news),
    ("3/5 PDF 임베딩", step_embed_pdf),
    ("4/5 뉴스 정리", step_organize_news),
    ("5/5 섹터 추천 리포트", step_daily_report),
]


async def run_pipeline():
    """전체 파이프라인을 순차 실행합니다."""
    pipeline_start = datetime.now()
    print(f"{'='*50}")
    print(f"  일일 배치 파이프라인 시작")
    print(f"  {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    try:
        await init_db()

        results = {}
        for step_name, step_fn in STEPS:
            step_start = datetime.now()
            print(f"\n--- [{step_name}] 시작 ---")

            try:
                result = await step_fn()
                duration = (datetime.now() - step_start).total_seconds()
                results[step_name] = {"status": "성공", "duration": duration, "result": result}
                print(f"--- [{step_name}] 완료 ({duration:.1f}초) ---")
            except Exception as e:
                duration = (datetime.now() - step_start).total_seconds()
                results[step_name] = {"status": "실패", "duration": duration, "error": str(e)}
                print(f"--- [{step_name}] 실패 ({duration:.1f}초): {e} ---")

        # 결과 요약
        total_duration = (datetime.now() - pipeline_start).total_seconds()
        print(f"\n{'='*50}")
        print(f"  파이프라인 완료 (총 {total_duration:.1f}초)")
        print(f"{'='*50}")
        for name, info in results.items():
            status = info["status"]
            dur = info["duration"]
            print(f"  [{status}] {name} ({dur:.1f}초)")
        print()

        # 수집 결과 Slack 알림
        collect_result = results.get("1/5 데이터 수집", {}).get("result")
        if isinstance(collect_result, dict):
            try:
                await notify_batch_result(
                    collect_result.get("news", 0),
                    collect_result.get("youtube", 0),
                    total_duration,
                    collect_result.get("rss", 0),
                )
            except Exception as e:
                print(f"[경고] Slack 알림 실패: {e}")

    except Exception as e:
        print(f"\n[치명적 오류] 파이프라인 중단: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
