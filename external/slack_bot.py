import logging
import re

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config.env_setting import settings
from external.db import get_session
from service.investment_advisor_service import ask_advisor

logger = logging.getLogger(__name__)

_handler: AsyncSocketModeHandler | None = None

app = AsyncApp(token=settings.SLACK_BOT_TOKEN)


@app.event("app_mention")
async def handle_mention(event: dict, say, client):
    """멘션 이벤트를 받아 투자 비서에게 질문하고 스레드로 답변합니다."""
    raw_text: str = event.get("text", "")
    question = re.sub(r"<@[A-Z0-9]+>", "", raw_text).strip()

    if not question:
        await say("질문을 입력해주세요. 예: `@봇이름 오늘 투자 전략 알려줘`", thread_ts=event.get("ts"))
        return

    thread_ts = event.get("thread_ts") or event["ts"]

    # 스레드 대화 히스토리 수집
    conversation_history = []
    if event.get("thread_ts"):
        conversation_history = await _fetch_thread_history(
            client, event["channel"], event["thread_ts"], event["ts"]
        )

    await say("분석 중...", thread_ts=thread_ts)

    try:
        session_factory = get_session()
        async with session_factory() as session:
            result = await ask_advisor(question, session, conversation_history=conversation_history)
        answer = result["answer"]
    except Exception as e:
        logger.error(f"투자 비서 호출 실패: {e}", exc_info=True)
        answer = "죄송합니다. 답변 생성 중 오류가 발생했습니다."

    await say(answer, thread_ts=thread_ts)


async def _fetch_thread_history(client, channel: str, thread_ts: str, current_ts: str) -> list[dict]:
    """스레드의 이전 대화 히스토리를 가져옵니다.

    Returns:
        [{"role": "user"|"assistant", "content": str}, ...] 형태의 리스트
    """
    try:
        result = await client.conversations_replies(channel=channel, ts=thread_ts)
        messages = result.get("messages", [])
    except Exception as e:
        logger.warning(f"스레드 히스토리 조회 실패: {e}")
        return []

    history = []
    for msg in messages:
        # 현재 메시지와 "분석 중..." 메시지는 제외
        if msg["ts"] == current_ts or msg.get("text", "") == "분석 중...":
            continue

        text = msg.get("text", "").strip()
        if not text:
            continue

        if msg.get("bot_id"):
            history.append({"role": "assistant", "content": text})
        else:
            # 사용자 메시지에서 멘션 태그 제거
            clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
            if clean_text:
                history.append({"role": "user", "content": clean_text})

    return history


async def start():
    """Socket Mode 핸들러를 시작합니다."""
    global _handler
    _handler = AsyncSocketModeHandler(app, settings.SLACK_APP_TOKEN)
    await _handler.connect_async()
    logger.info("Slack 봇 시작 완료 (Socket Mode)")


async def stop():
    """Socket Mode 핸들러를 종료합니다."""
    global _handler
    if _handler is not None:
        await _handler.close_async()
        _handler = None
        logger.info("Slack 봇 종료 완료")
