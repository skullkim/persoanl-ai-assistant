import asyncio
import logging

from ddgs import DDGS

from external.ollama_client import get_llm

logger = logging.getLogger(__name__)

TRANSLATE_PROMPT = (
    "Translate the following Korean investment question into concise English search keywords.\n"
    "Return ONLY the keywords, nothing else.\n"
    "Question: {question}"
)


async def _translate_query(question: str) -> str:
    """LLM을 사용하여 한국어 질문을 영어 검색 키워드로 변환합니다."""
    try:
        llm = get_llm()
        response = await llm.ainvoke(TRANSLATE_PROMPT.format(question=question))
        keywords = " ".join(response.content.strip().split())
        logger.info(f"[웹 검색] 영어 키워드: {keywords}")
        return keywords
    except Exception as e:
        logger.warning(f"[웹 검색] 키워드 변환 실패, 원본 쿼리 사용: {e}")
        return question


async def search(query: str, limit: int = 5) -> list[dict]:
    """DuckDuckGo로 웹 검색을 수행합니다.

    Args:
        query: 검색 쿼리 (한국어 가능, 내부에서 영어로 변환)
        limit: 최대 결과 수

    Returns:
        [{"title": str, "link": str, "snippet": str}, ...]
    """
    try:
        english_query = await _translate_query(query)

        raw_results = await asyncio.to_thread(
            DDGS().text, english_query, max_results=limit
        )

        results = [
            {
                "title": r.get("title", ""),
                "link": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in raw_results
        ]

        logger.info(f"[웹 검색] '{english_query[:50]}' → 결과 {len(results)}건")
        return results

    except Exception as e:
        logger.error(f"[웹 검색] 검색 실패: {e}")
        return []
