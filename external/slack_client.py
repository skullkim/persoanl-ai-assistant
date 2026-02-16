import logging

import httpx

from config.env_setting import settings

logger = logging.getLogger(__name__)

SLACK_TIMEOUT = 10


async def send_webhook_message(blocks: list[dict], text: str = "") -> bool:
    """Slack Incoming Webhook으로 메시지를 전송합니다."""
    webhook_url = settings.SLACK_WEBHOOK_URL
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    payload = {"blocks": blocks}
    if text:
        payload["text"] = text

    try:
        async with httpx.AsyncClient(timeout=SLACK_TIMEOUT) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code == 200:
                return True
            logger.error(f"Slack Webhook 전송 실패: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Slack Webhook 전송 중 오류: {e}")
        return False
