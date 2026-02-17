from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from external.rss_client import fetch_rss_feed
from external.db.model import News, NewsSource
from external.db.repository import NewsRepository, NewsSourceRepository


def _parse_rss_date(date_str: str) -> tuple[str, datetime | None]:
    """RSS 날짜를 YYYY.MM.DD 형식으로 변환합니다."""
    if not date_str:
        return "", None
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y.%m.%d"), dt
    except Exception:
        return date_str, None


def _is_in_date_range(dt: datetime | None, start_date: datetime, end_date: datetime) -> bool:
    """날짜가 지정된 범위 내에 있는지 확인합니다."""
    if dt is None:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return start_date <= dt < end_date


async def get_news_from_rss(session: AsyncSession, offset_days: int = 0, count_days: int = 1) -> list[dict]:
    """설정된 RSS 피드들에서 뉴스를 가져옵니다.

    Args:
        session: DB 세션
        offset_days: 오늘로부터의 과거 오프셋 (0 = 오늘, 1 = 어제...)
        count_days: 가져올 날짜 범위 (예: 1이면 1일치)
    """
    sources = await NewsSourceRepository.find_active_by_type("rss", session)
    if not sources:
        return []

    # 날짜 범위 계산 (timezone-aware)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today - timedelta(days=offset_days) + timedelta(days=1)
    start_date = end_date - timedelta(days=count_days)

    all_news = []

    for source in sources:
        try:
            articles = fetch_rss_feed(source.identifier)
            for article in articles:
                date_str, dt = _parse_rss_date(article.get("published", ""))
                if not _is_in_date_range(dt, start_date, end_date):
                    continue

                content = article.get("content", "") or article.get("summary", "")
                all_news.append({
                    "title": article.get("title", ""),
                    "content": content,
                    "category": source.category,
                    "date": date_str,
                    "source": source.source_name,
                })
        except Exception as e:
            print(f"RSS 피드 수집 실패 ({source.identifier}): {e}")
            continue

    # 날짜 기준 정렬 (최신순)
    all_news.sort(key=lambda x: x["date"], reverse=True)

    return all_news


async def save_rss_news_if_not_exists(news_items: list[dict], session: AsyncSession) -> int:
    """중복되지 않는 RSS 뉴스만 저장합니다."""
    if not news_items:
        return 0

    saved = 0
    skipped = 0
    for item in news_items:
        title = item["title"]
        upload_date = item.get("date", "")

        if await NewsRepository.exists_by_title_and_upload_date(title, upload_date, session):
            skipped += 1
            continue

        news = News(
            title=title,
            content=item.get("content", ""),
            category=item.get("category", ""),
            upload_date=upload_date,
            source=item.get("source", ""),
        )
        await NewsRepository.save(news, session)
        saved += 1

    if skipped > 0:
        print(f"[RSS] 중복 {skipped}개 건너뜀")

    return saved
