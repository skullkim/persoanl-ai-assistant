import asyncio
import logging

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession

from config.env_setting import settings
from external.db.model import News, NewsOrganize
from external.db.repository import NewsRepository, NewsOrganizeRepository

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
너는 여러 뉴스레터를 하나의 브리핑으로 통합 정리하는 편집자야.

## 입력
아래에 같은 날짜에 발행된 여러 개의 뉴스레터 원문이 주어진다.

## 작업 지시

1. 모든 뉴스레터에서 개별 뉴스 항목을 빠짐없이 추출해라. 광고·구독 안내 등 메타 정보만 제외해라.
2. 출처(뉴스레터)별이 아니라 주제별로 재분류해라. 주제 분류는 내용에 맞게 자율적으로 정해라.
3. 여러 뉴스레터에서 같은 사건을 다룬 경우 하나의 항목으로 병합하되, 각 출처의 고유한 수치·맥락·인용은 모두 포함해라.

## 상세도 기준 (중요)

각 항목은 다음을 모두 포함하도록 써라:
- 핵심 사실 (무슨 일이 일어났는가)
- 구체적 수치 (금액, 퍼센트, 날짜, 기간 등 원문에 나온 숫자는 빠짐없이)
- 배경·맥락 (왜 이 일이 일어났는가, 어떤 흐름 속에 있는가)
- 시사점·전망 (시장이나 정책에 어떤 의미가 있는가)
- 원문에 인용된 인물의 발언이 있으면 포함

"요약"하지 마라. 원문의 정보량을 최대한 보존하면서 읽기 쉽게 "재구성"하는 것이 목표다.
짧은 한두 줄짜리 항목이 되지 않도록 해라. 각 항목은 최소 3~5문장 이상으로 써라.

## 출력 형식

슬랙 메시지 포맷으로 작성해라:
- 섹션 헤더: 이모지 + *볼드* (예: 📈 *증시*)
- 섹션 구분: ───────────────────── (구분선)
- 개별 항목: • *항목 제목 볼드* + 줄바꿈 후 본문
- 각 항목 끝에 괄호로 출처 표기 (예: (머니레터·Daily Byte))
- 맨 위에 날짜, 출처 목록, 주요 지수 요약을 넣어라
- 모든 출력은 반드시 한국어로만 작성해라. 영문 기사도 한국어로 번역해라.
- 고유명사(기업명, 인물명, 기술명 등)는 원문 그대로 영문 표기 가능하되, 설명은 반드시 한국어로 작성해라.
- 마크다운의 # 헤더, ** 볼드 등은 사용하지 마라 (Slack에서 렌더링되지 않음).

## 출력 예시

📈 *증시*

• *코스피 사상 첫 5,500선 돌파*
12일 코스피가 전 거래일 대비 167.78P(+3.13%) 오른 5,522.27로 마감하며 사상 처음 5,500선을 넘었다. 삼성전자·SK하이닉스 등 메모리 반도체주가 급등하며 지수를 끌어올렸고, 외국인이 3조 137억 원, 기관이 1조 3,687억 원을 순매수했다. 직접적인 촉매는 전날 미국 마이크론이 '엔비디아 HBM4 공급 탈락설'을 정면 반박하며 주가가 9% 넘게 급등한 것이었다. (머니레터·Daily Byte)

─────────────────────

💱 *환율·통화*

...

## 주의사항
- 항목을 누락하지 마라.
- 숫자를 반올림하거나 생략하지 마라.
- "~했다고 합니다" 같은 전달체가 아니라, "~했다"는 서술체로 써라.
"""

USER_PROMPT_TEMPLATE = """\
아래는 {date} 수집된 뉴스레터 원문 {count}건이다.
모든 개별 뉴스 항목을 추출하여 주제별로 통합 정리해라.

{articles_text}
"""

SLACK_MAX_LEN = 3900
CLI_TIMEOUT = 300  # Claude CLI 응답 대기 최대 5분


async def _call_claude_cli(prompt: str) -> str:
    """Claude CLI를 호출하여 답변을 받습니다."""
    process = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=CLI_TIMEOUT
        )
    except asyncio.TimeoutError:
        process.kill()
        raise RuntimeError(f"Claude CLI 응답 시간 초과 ({CLI_TIMEOUT}초)")

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(f"Claude CLI 오류 (code={process.returncode}): {error_msg}")

    return stdout.decode().strip()


def _format_articles_for_prompt(articles: list[News]) -> str:
    """뉴스레터 목록을 프롬프트용 텍스트로 변환합니다."""
    parts = []
    for i, article in enumerate(articles, 1):
        content = article.content or ""
        parts.append(
            f"[뉴스레터 {i}]\n"
            f"제목: {article.title}\n"
            f"날짜: {article.upload_date}\n"
            f"출처: {article.source}\n"
            f"본문:\n{content}\n"
        )
    return "\n---\n".join(parts)


async def organize_news(target_date: str, session: AsyncSession) -> tuple[str, int]:
    """지정된 날짜의 뉴스를 주제별로 통합 정리하고 DB에 저장합니다.

    Args:
        target_date: YYYY.MM.DD 형식의 대상 날짜
        session: DB 세션

    Returns:
        (정리 텍스트, 뉴스레터 수) 튜플
    """
    articles = await NewsRepository.find_by_upload_date(target_date, session)

    if not articles:
        logger.info(f"[뉴스 정리] {target_date} 뉴스 없음")
        return "", 0

    logger.info(f"[뉴스 정리] {target_date} 뉴스레터 {len(articles)}건 통합 정리 시작")

    articles_text = _format_articles_for_prompt(articles)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        date=target_date,
        count=len(articles),
        articles_text=articles_text,
    )

    full_prompt = SYSTEM_PROMPT + "\n\n" + user_prompt
    summary_text = await _call_claude_cli(full_prompt)

    article_ids = [a.id for a in articles if a.id is not None]
    news_organize = NewsOrganize(
        summary_date=target_date,
        category="Daily",
        content=summary_text,
        source_news_ids=article_ids,
    )
    await NewsOrganizeRepository.save(news_organize, session)

    logger.info(f"[뉴스 정리] 저장 완료 (id={news_organize.id})")
    return summary_text, len(articles)


def _split_slack_message(text: str) -> list[str]:
    """Slack 메시지 길이 제한에 맞게 텍스트를 분할합니다."""
    chunks = []
    while len(text) > SLACK_MAX_LEN:
        # 구분선(───) 기준으로 끊기 시도
        cut_point = text.rfind("─────", 0, SLACK_MAX_LEN)
        if cut_point == -1:
            cut_point = text.rfind("\n", 0, SLACK_MAX_LEN)
        if cut_point == -1:
            cut_point = SLACK_MAX_LEN
        chunks.append(text[:cut_point])
        text = text[cut_point:].lstrip("─\n ")
    chunks.append(text)
    return chunks


async def send_news_briefing_to_slack(summary_text: str, article_count: int, target_date: str):
    """뉴스 정리를 Slack으로 발송합니다.

    Args:
        summary_text: 정리 텍스트
        article_count: 뉴스레터 수
        target_date: YYYY.MM.DD 형식의 대상 날짜
    """
    webhook_url = settings.SLACK_SUMMARY_WEBHOOK_URL
    if not webhook_url:
        logger.warning("SLACK_SUMMARY_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    display_date = target_date.replace(".", "-")
    header = f":newspaper: *일일 뉴스 브리핑* ({display_date}, 뉴스레터 {article_count}건)\n\n"
    full_text = header + summary_text

    chunks = _split_slack_message(full_text)

    async with httpx.AsyncClient(timeout=15) as client:
        for i, chunk in enumerate(chunks):
            payload = {"text": chunk, "mrkdwn": True}
            try:
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code == 200:
                    logger.info(f"[Slack] 뉴스 브리핑 발송 성공 ({i + 1}/{len(chunks)})")
                else:
                    logger.error(f"[Slack] 발송 실패: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"[Slack] 발송 중 오류: {e}")
