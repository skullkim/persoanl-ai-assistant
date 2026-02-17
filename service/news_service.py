import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from external.gmail_client import fetch_emails
from external.db.model import News, NewsSource
from external.db.repository import NewsRepository, NewsSourceRepository


def _parse_date(date_str: str) -> tuple[str, datetime | None]:
    """이메일 날짜를 YYYY.MM.DD 형식으로 변환하고 datetime 객체도 반환합니다."""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y.%m.%d"), dt
    except Exception:
        return date_str, None


def _extract_sender_email(from_header: str) -> str:
    """From 헤더에서 이메일 주소만 추출합니다."""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).lower()
    return from_header.lower().strip()


def _email_to_news_item(email: dict, source: NewsSource) -> tuple[dict, datetime | None]:
    """이메일을 뉴스 아이템으로 변환합니다."""
    date_str, dt = _parse_date(email.get("date", ""))

    news_item = {
        "id": email["id"],
        "title": email.get("subject", "(제목 없음)"),
        "content": email.get("body", ""),
        "category": source.category,
        "date": date_str,
        "source": source.source_name,
    }
    return news_item, dt


def _is_in_date_range(dt: datetime | None, start_date: datetime, end_date: datetime) -> bool:
    """날짜가 지정된 범위 내에 있는지 확인합니다."""
    if dt is None:
        return False
    return start_date <= dt < end_date


async def get_news_from_emails(session: AsyncSession, offset_days: int = 0, count_days: int = 3) -> list[dict]:
    """설정된 발신자들로부터 뉴스를 가져옵니다.

    Args:
        session: DB 세션
        offset_days: 오늘로부터의 과거 오프셋 (0 = 오늘, 1 = 어제...)
        count_days: 가져올 날짜 범위 (예: 3이면 3일치)
    """
    sources = await NewsSourceRepository.find_active_by_type("email", session)
    if not sources:
        return []

    # identifier(이메일) → NewsSource 매핑
    source_map = {s.identifier: s for s in sources}

    # 날짜 범위 계산 (timezone-aware)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today - timedelta(days=offset_days) + timedelta(days=1)  # 해당 날짜 끝까지 포함
    start_date = end_date - timedelta(days=count_days)

    # Gmail 검색용 날짜 (YYYY/MM/DD 형식)
    after_str = start_date.strftime("%Y/%m/%d")
    before_str = end_date.strftime("%Y/%m/%d")

    all_news = []

    for source in sources:
        try:
            emails = fetch_emails(source.identifier, max_results=20,
                                  after_date=after_str, before_date=before_str)
            for email in emails:
                sender_email = _extract_sender_email(email.get("sender", ""))
                matched_source = source_map.get(sender_email, source)
                news_item, dt = _email_to_news_item(email, matched_source)
                if _is_in_date_range(dt, start_date, end_date):
                    all_news.append(news_item)
        except Exception as e:
            print(f"Failed to fetch emails from {source.identifier}: {e}")
            continue

    # 날짜 기준 정렬 (최신순)
    all_news.sort(key=lambda x: x["date"], reverse=True)

    return all_news


async def save_news_if_not_exists(news_items: list[dict], session: AsyncSession) -> int:
    """중복되지 않는 뉴스만 저장합니다."""
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
        print(f"[뉴스] 중복 {skipped}개 건너뜀")

    return saved
