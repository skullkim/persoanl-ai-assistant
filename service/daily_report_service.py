import json
import logging
from datetime import datetime, timedelta

import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from sqlmodel.ext.asyncio.session import AsyncSession

from config.env_setting import settings
from external.ollama_client import get_llm
from external.db.model import News, DailyReport
from external.db.repository import NewsRepository, DailyReportRepository

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
당신은 투자 섹터 분석 전문가입니다.
전달받은 최근 뉴스 데이터를 분석하여 섹터별 투자 추천 리포트를 작성합니다.

## 출력 형식
반드시 아래 JSON 형식으로 **먼저** 출력하고, 그 아래에 종합 분석 리포트를 작성하세요.

```json
{
  "sectors": [
    {
      "name": "섹터명",
      "recommendation": "매수|관망|매도",
      "confidence": 0.0~1.0,
      "reason": "추천 근거 1~2문장"
    }
  ]
}
```

## 종합 리포트
JSON 블록 아래에 Slack mrkdwn 형식으로 종합 분석을 작성하세요:
1. 시장 전반 동향 (2~3문장)
2. 주목할 섹터와 이유 (섹터별 2~3문장)
3. 리스크 요인 (1~2문장)
4. 결론 및 투자 전략 제안 (2~3문장)

## 분석 규칙
1. 수치(금액·비율·건수), 기업명을 반드시 포함할 것
2. 최소 3개, 최대 7개 섹터를 분석할 것
3. 뉴스에 근거하지 않은 추측은 하지 말 것
4. 한국어로 작성할 것
5. 투자 판단은 사용자 본인의 책임임을 명시할 것
"""

USER_PROMPT_TEMPLATE = """\
아래는 최근 {days}일간 수집된 뉴스 {count}건입니다.
이를 분석하여 섹터별 투자 추천 리포트를 작성해 주세요.

{articles_text}
"""

SLACK_MAX_LEN = 3900


def _format_articles_for_report(articles: list[News]) -> str:
    """기사 목록을 리포트 프롬프트용 텍스트로 변환합니다."""
    parts = []
    for i, article in enumerate(articles, 1):
        content = (article.content or "")[:1500]
        parts.append(
            f"[기사 {i}]\n"
            f"제목: {article.title}\n"
            f"날짜: {article.upload_date}\n"
            f"출처: {article.source}\n"
            f"카테고리: {article.category}\n"
            f"본문:\n{content}\n"
        )
    return "\n---\n".join(parts)


def _parse_sectors_json(response_text: str) -> dict | None:
    """LLM 응답에서 JSON 블록을 추출합니다."""
    try:
        start = response_text.find("```json")
        if start == -1:
            start = response_text.find("{")
            if start == -1:
                return None
            end = response_text.find("}", start)
            # 중첩된 } 찾기
            depth = 0
            for i in range(start, len(response_text)):
                if response_text[i] == "{":
                    depth += 1
                elif response_text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            json_str = response_text[start:end]
        else:
            start = response_text.find("{", start)
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()

        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"[리포트] JSON 파싱 실패: {e}")
        return None


async def generate_daily_report(session: AsyncSession, days: int = 3) -> tuple[str, int]:
    """최근 N일 뉴스를 분석하여 섹터 추천 리포트를 생성합니다.

    Returns:
        (리포트 텍스트, 분석 기사 수)
    """
    today_str = datetime.now().strftime("%Y.%m.%d")

    # 최근 N일 뉴스 수집
    all_articles = []
    for offset in range(days):
        date = datetime.now() - timedelta(days=offset)
        date_str = date.strftime("%Y.%m.%d")
        articles = await NewsRepository.find_by_upload_date(date_str, session)
        all_articles.extend(articles)

    if not all_articles:
        logger.info(f"[리포트] 최근 {days}일 뉴스 없음")
        return "", 0

    logger.info(f"[리포트] {len(all_articles)}건 뉴스로 섹터 분석 시작")

    articles_text = _format_articles_for_report(all_articles)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        days=days,
        count=len(all_articles),
        articles_text=articles_text,
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    response = await llm.ainvoke(messages)
    report_text = response.content

    # JSON 파싱
    sectors_data = _parse_sectors_json(report_text)

    # DB 저장
    report = DailyReport(
        report_date=today_str,
        content=report_text,
        sectors=sectors_data,
        source_count=len(all_articles),
    )
    await DailyReportRepository.save(report, session)
    logger.info(f"[리포트] 저장 완료 (id={report.id})")

    return report_text, len(all_articles)


def _split_slack_message(text: str) -> list[str]:
    """Slack 메시지 길이 제한에 맞게 텍스트를 분할합니다."""
    chunks = []
    while len(text) > SLACK_MAX_LEN:
        cut_point = text.rfind("\n", 0, SLACK_MAX_LEN)
        if cut_point == -1:
            cut_point = SLACK_MAX_LEN
        chunks.append(text[:cut_point])
        text = text[cut_point:].lstrip("\n ")
    chunks.append(text)
    return chunks


async def send_report_to_slack(report_text: str, article_count: int):
    """리포트를 Slack으로 발송합니다."""
    webhook_url = settings.SLACK_REPORT_WEBHOOK_URL or settings.SLACK_SUMMARY_WEBHOOK_URL
    if not webhook_url:
        logger.warning("SLACK_REPORT_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    header = f":chart_with_upwards_trend: *일일 섹터 추천 리포트* ({today_str}, {article_count}건 분석)\n\n"
    full_text = header + report_text

    chunks = _split_slack_message(full_text)

    async with httpx.AsyncClient(timeout=15) as client:
        for i, chunk in enumerate(chunks):
            payload = {"text": chunk, "mrkdwn": True}
            try:
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code == 200:
                    logger.info(f"[Slack] 리포트 발송 성공 ({i + 1}/{len(chunks)})")
                else:
                    logger.error(f"[Slack] 발송 실패: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"[Slack] 발송 중 오류: {e}")
