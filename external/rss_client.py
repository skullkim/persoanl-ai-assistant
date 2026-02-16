import logging

import httpx
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RSS_TIMEOUT = 15
ARTICLE_TIMEOUT = 15

# 도메인별 본문 CSS 클래스 매핑
CONTENT_SELECTORS = {
    "techcrunch.com": "entry-content",
    "arstechnica.com": "post-content",
}


def _get_content_class(url: str) -> str | None:
    """URL 도메인에 매칭되는 본문 CSS 클래스를 반환합니다."""
    for domain, css_class in CONTENT_SELECTORS.items():
        if domain in url:
            return css_class
    return None


def fetch_article_content(article_url: str) -> str:
    """기사 페이지에서 본문 텍스트를 추출합니다.

    Args:
        article_url: 기사 URL

    Returns:
        본문 텍스트. 실패 시 빈 문자열.
    """
    content_class = _get_content_class(article_url)
    if not content_class:
        return ""

    try:
        with httpx.Client(timeout=ARTICLE_TIMEOUT, follow_redirects=True) as client:
            response = client.get(article_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find(class_=content_class)
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        return ""

    except Exception as e:
        logger.error(f"기사 본문 크롤링 실패 ({article_url}): {e}")
        return ""


def fetch_rss_feed(feed_url: str) -> list[dict]:
    """RSS 피드를 파싱하여 기사 목록을 반환합니다.

    Args:
        feed_url: RSS 피드 URL

    Returns:
        [{"title": ..., "link": ..., "published": ..., "summary": ..., "content": ...}]
    """
    try:
        with httpx.Client(timeout=RSS_TIMEOUT, follow_redirects=True) as client:
            response = client.get(feed_url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)

        articles = []
        for entry in feed.entries:
            link = entry.get("link", "")
            content = fetch_article_content(link) if link else ""

            articles.append({
                "title": entry.get("title", ""),
                "link": link,
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "content": content,
            })

        return articles

    except httpx.HTTPStatusError as e:
        logger.error(f"RSS 피드 HTTP 오류 ({feed_url}): {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"RSS 피드 파싱 실패 ({feed_url}): {e}")
        return []
