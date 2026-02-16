import logging
from datetime import datetime

import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from sqlmodel.ext.asyncio.session import AsyncSession

from config.env_setting import settings
from external.ollama_client import get_llm
from external.db.model import News, NewsSummary
from external.db.repository import NewsRepository, NewsSummaryRepository

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
당신은 뉴스 큐레이터입니다.
전달받은 뉴스 기사 데이터를 아래 규칙에 따라 요약해 주세요.

## 출력 포맷 (Slack mrkdwn)
각 기사마다 아래 형식을 따릅니다:

*{번호}. {기사 제목}*  ({날짜}, {출처})
{본문 핵심 내용 3~5문장 요약}

---

## 요약 규칙
1. 핵심 팩트 우선: 수치(금액·비율·건수), 인물명, 기업명을 반드시 포함할 것
2. "무슨 일이 일어났는지"를 먼저 쓰고, 배경·맥락은 그 뒤에 간결하게 덧붙일 것
3. 한 기사에 여러 소식이 있으면 메인 기사 위주로 요약하되, 중요한 부수 뉴스도 1~2줄로 언급할 것
4. 뉴스레터의 광고, 퀴즈, 구독 안내, 푸터(수신거부·주소 등) 등 부가 콘텐츠는 전부 무시할 것
5. 영문 기사도 한국어로 요약할 것
6. created_at 기준 최신순으로 정렬할 것
7. Slack mrkdwn 문법을 사용할 것 (*볼드*, _이탤릭_, `코드`, ~취소선~)
8. 마크다운의 # 헤더, ** 볼드 등은 사용하지 말 것 (Slack에서 렌더링되지 않음)
9. 전체 출력이 Slack 메시지 길이 제한(4,000자)을 초과하지 않도록 조절할 것
"""

USER_PROMPT_TEMPLATE = """\
아래는 오늘 수집된 뉴스 기사 {count}건입니다.
각 기사를 요약 규칙에 맞춰 요약해 주세요.

{articles_text}
"""

SLACK_MAX_LEN = 3900


def _format_articles_for_prompt(articles: list[News]) -> str:
    """기사 목록을 프롬프트용 텍스트로 변환합니다. 본문은 2000자로 제한."""
    parts = []
    for i, article in enumerate(articles, 1):
        content = (article.content or "")[:2000]
        parts.append(
            f"[기사 {i}]\n"
            f"제목: {article.title}\n"
            f"날짜: {article.upload_date}\n"
            f"출처: {article.source}\n"
            f"본문:\n{content}\n"
        )
    return "\n---\n".join(parts)


async def summarize_today_news(session: AsyncSession) -> tuple[str, int]:
    """당일 뉴스를 요약하고 DB에 저장합니다.

    Returns:
        (요약 텍스트, 기사 수) 튜플
    """
    today_str = datetime.now().strftime("%Y.%m.%d")
    articles = await NewsRepository.find_by_upload_date(today_str, session)

    if not articles:
        logger.info(f"[뉴스 요약] {today_str} 뉴스 없음")
        return "", 0

    logger.info(f"[뉴스 요약] {today_str} 뉴스 {len(articles)}건 요약 시작")

    articles_text = _format_articles_for_prompt(articles)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(articles),
        articles_text=articles_text,
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    response = await llm.ainvoke(messages)
    summary_text = response.content

    article_ids = [a.id for a in articles if a.id is not None]
    news_summary = NewsSummary(
        summary_date=today_str,
        category="Daily",
        summary=summary_text,
        source_news_ids=article_ids,
    )
    await NewsSummaryRepository.save(news_summary, session)

    logger.info(f"[뉴스 요약] 저장 완료 (id={news_summary.id})")
    return summary_text, len(articles)


def _split_slack_message(text: str) -> list[str]:
    """Slack 메시지 길이 제한에 맞게 텍스트를 분할합니다."""
    chunks = []
    while len(text) > SLACK_MAX_LEN:
        cut_point = text.rfind("\n---\n", 0, SLACK_MAX_LEN)
        if cut_point == -1:
            cut_point = SLACK_MAX_LEN
        chunks.append(text[:cut_point])
        text = text[cut_point:].lstrip("-\n ")
    chunks.append(text)
    return chunks


async def send_news_summary_to_slack(summary_text: str, article_count: int):
    """뉴스 요약을 Slack으로 발송합니다."""
    webhook_url = settings.SLACK_SUMMARY_WEBHOOK_URL
    if not webhook_url:
        logger.warning("SLACK_SUMMARY_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    header = f":newspaper: *일일 뉴스 요약* ({today_str}, {article_count}건)\n\n"
    full_text = header + summary_text

    chunks = _split_slack_message(full_text)

    async with httpx.AsyncClient(timeout=15) as client:
        for i, chunk in enumerate(chunks):
            payload = {"text": chunk, "mrkdwn": True}
            try:
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code == 200:
                    logger.info(f"[Slack] 뉴스 요약 발송 성공 ({i + 1}/{len(chunks)})")
                else:
                    logger.error(f"[Slack] 발송 실패: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"[Slack] 발송 중 오류: {e}")
