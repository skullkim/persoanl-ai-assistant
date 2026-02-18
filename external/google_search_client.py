import logging

from googleapiclient.discovery import build

from config.env_setting import settings

logger = logging.getLogger(__name__)


def _get_search_service():
    """Google Custom Search API 서비스 인스턴스를 반환합니다."""
    if not settings.YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
    if not settings.GOOGLE_CSE_ID:
        raise ValueError("GOOGLE_CSE_ID가 설정되지 않았습니다.")
    return build("customsearch", "v1", developerKey=settings.YOUTUBE_API_KEY)


async def search(query: str, limit: int = 5) -> list[dict]:
    """Google Custom Search API로 웹 검색을 수행합니다.

    Args:
        query: 검색 쿼리
        limit: 최대 결과 수 (최대 10)

    Returns:
        [{"title": str, "link": str, "snippet": str}, ...]
    """
    try:
        service = _get_search_service()
        response = service.cse().list(
            q=query,
            cx=settings.GOOGLE_CSE_ID,
            num=min(limit, 10),
        ).execute()

        results = []
        for item in response.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })

        logger.info(f"[Google 검색] '{query[:50]}' → {len(results)}건 반환")
        return results

    except Exception as e:
        logger.error(f"[Google 검색] 검색 실패: {e}")
        return []
