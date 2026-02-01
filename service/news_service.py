import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from config.env_setting import settings
from external.gmail_client import fetch_emails


# 발신자별 소스 이름 및 카테고리 매핑
SENDER_CONFIG = {
    "moneyletter@uppity.co.kr": {"source": "머니레터", "category": "Economy"},
    "byteteam365@mydailybyte.com": {"source": "Daily Byte", "category": "Tech"},
    "miraklelab@mk.co.kr": {"source": "미라클레터", "category": "Economy"},
    "morning@ilbuntok.com": {"source": "일분톡", "category": "Economy"},
    "thecapitaledge+weeklyedge@substack.com": {"source": "The Capital Edge", "category": "Economy"},
}


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


def _email_to_news_item(email: dict) -> tuple[dict, datetime | None]:
    """이메일을 뉴스 아이템으로 변환합니다."""
    sender_email = _extract_sender_email(email.get("sender", ""))
    config = SENDER_CONFIG.get(sender_email, {"source": "뉴스레터", "category": "General"})
    date_str, dt = _parse_date(email.get("date", ""))

    news_item = {
        "id": email["id"],
        "title": email.get("subject", "(제목 없음)"),
        "summary": email.get("snippet", ""),
        "content": email.get("body", ""),
        "category": config["category"],
        "date": date_str,
        "source": config["source"],
    }
    return news_item, dt


def _is_in_date_range(dt: datetime | None, start_date: datetime, end_date: datetime) -> bool:
    """날짜가 지정된 범위 내에 있는지 확인합니다."""
    if dt is None:
        return False
    return start_date <= dt < end_date


def get_news_from_emails(offset_days: int = 0, count_days: int = 3) -> list[dict]:
    """설정된 발신자들로부터 뉴스를 가져옵니다.

    Args:
        offset_days: 오늘로부터의 과거 오프셋 (0 = 오늘, 1 = 어제...)
        count_days: 가져올 날짜 범위 (예: 3이면 3일치)
    """
    sender_emails = settings.NEWS_SENDER_EMAILS
    if not sender_emails:
        return []

    # 날짜 범위 계산 (timezone-aware)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today - timedelta(days=offset_days) + timedelta(days=1)  # 해당 날짜 끝까지 포함
    start_date = end_date - timedelta(days=count_days)

    senders = [s.strip() for s in sender_emails.split(",") if s.strip()]
    all_news = []

    for sender in senders:
        try:
            # 충분한 이메일을 가져와서 필터링
            emails = fetch_emails(sender, max_results=20)
            for email in emails:
                news_item, dt = _email_to_news_item(email)
                if _is_in_date_range(dt, start_date, end_date):
                    all_news.append(news_item)
        except Exception as e:
            print(f"Failed to fetch emails from {sender}: {e}")
            continue

    # 날짜 기준 정렬 (최신순)
    all_news.sort(key=lambda x: x["date"], reverse=True)

    return all_news
