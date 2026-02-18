import logging

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlmodel.ext.asyncio.session import AsyncSession

from config.env_setting import settings
from external.ollama_client import get_llm
from external import google_search_client
from service.embedding_service import search_similar_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
당신은 투자 분석 전문가입니다.
사용자의 질문에 대해 제공된 컨텍스트(뉴스, PDF 리포트, 웹 검색 결과)를 기반으로 답변합니다.

## 답변 규칙
1. 반드시 제공된 컨텍스트에 근거하여 답변하세요.
2. 컨텍스트에 없는 내용은 추측하지 말고, 정보가 부족하다고 솔직히 밝히세요.
3. 수치, 기업명, 날짜 등 구체적 팩트를 우선적으로 인용하세요.
4. 출처(뉴스/PDF/웹)를 언급하여 신뢰도를 높이세요. 웹 검색 결과를 인용할 때는 해당 URL을 함께 표기하세요.
5. 투자 판단은 사용자 본인의 책임임을 항상 상기시키세요.
6. 한국어로 답변하세요.
"""

USER_PROMPT_TEMPLATE = """\
## 참고 컨텍스트 ({context_count}건)

{context_text}

---

{web_search_section}

## 사용자 질문
{question}
"""


def _format_context(contexts: list[dict]) -> str:
    """검색된 컨텍스트를 프롬프트용 텍스트로 포맷합니다."""
    parts = []
    for i, ctx in enumerate(contexts, 1):
        source_label = "뉴스" if ctx["source_type"] == "news" else "PDF"
        meta = ctx.get("metadata", {})
        source_info = meta.get("source", "") or meta.get("document_id", "")
        date_info = meta.get("upload_date", "")

        header = f"[{source_label} #{i}]"
        if source_info:
            header += f" ({source_info})"
        if date_info:
            header += f" [{date_info}]"
        header += f" (유사도: {ctx['score']})"

        parts.append(f"{header}\n{ctx['content']}")

    return "\n\n---\n\n".join(parts)


def _format_web_results(web_results: list[dict]) -> str:
    """웹 검색 결과를 프롬프트용 텍스트로 포맷합니다."""
    if not web_results:
        return ""

    parts = []
    for i, result in enumerate(web_results, 1):
        parts.append(
            f"[웹 #{i}] {result['title']}\n"
            f"URL: {result['link']}\n"
            f"{result['snippet']}"
        )

    section = "## 웹 검색 결과 ({count}건)\n\n{content}\n\n---\n".format(
        count=len(web_results),
        content="\n\n---\n\n".join(parts),
    )
    return section


async def ask_advisor(
    question: str,
    session: AsyncSession,
    context_limit: int = 5,
    conversation_history: list[dict] | None = None,
) -> dict:
    """RAG 기반 투자 비서 답변을 생성합니다.

    Args:
        question: 사용자 질문
        session: DB 세션
        context_limit: 검색할 컨텍스트 수
        conversation_history: 스레드 대화 히스토리 [{"role": "user"|"assistant", "content": str}, ...]

    Returns:
        {"answer": str, "sources": list[dict], "context_count": int}
    """
    # 1. 유사 컨텍스트 검색
    contexts = await search_similar_context(
        query=question, session=session, limit=context_limit
    )

    # 2. 웹 검색 (GOOGLE_CSE_ID가 설정된 경우에만)
    web_results = []
    if settings.GOOGLE_CSE_ID:
        web_results = await google_search_client.search(query=question, limit=5)

    # 3. 프롬프트 생성
    context_text = _format_context(contexts) if contexts else "(관련 컨텍스트 없음)"
    web_search_section = _format_web_results(web_results)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        context_count=len(contexts),
        context_text=context_text,
        web_search_section=web_search_section,
        question=question,
    )

    # 4. LLM 호출 (대화 히스토리 포함)
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if conversation_history:
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_prompt))

    response = await llm.ainvoke(messages)
    answer = response.content

    # 5. 소스 정보 정리
    sources = [
        {
            "source_type": ctx["source_type"],
            "source_id": ctx["source_id"],
            "score": ctx["score"],
            "metadata": ctx["metadata"],
        }
        for ctx in contexts
    ]

    logger.info(
        f"[투자비서] 질문: '{question[:50]}...' → "
        f"컨텍스트 {len(contexts)}건, 웹 검색 {len(web_results)}건 사용"
    )

    return {
        "answer": answer,
        "sources": sources,
        "context_count": len(contexts),
        "web_results_count": len(web_results),
    }
