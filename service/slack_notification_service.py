import logging
from datetime import datetime

from external.slack_client import send_webhook_message

logger = logging.getLogger(__name__)


def _build_batch_summary_blocks(news_count: int, youtube_count: int,
                                duration: float, rss_count: int = 0) -> list[dict]:
    """배치 실행 결과 요약 블록을 생성합니다."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = news_count + youtube_count + rss_count
    status_emoji = ":white_check_mark:" if total > 0 else ":warning:"

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{status_emoji} 일일 데이터 수집 완료", "emoji": True}
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:newspaper: 뉴스*\n{news_count}건 수집"},
                {"type": "mrkdwn", "text": f"*:movie_camera: 유튜브*\n{youtube_count}건 수집"},
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:satellite_antenna: RSS*\n{rss_count}건 수집"},
                {"type": "mrkdwn", "text": f"*:clock1: 소요시간*\n{duration:.2f}초"},
            ]
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:calendar: 실행시각*\n{now}"},
            ]
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Financial Investment Assistant - Daily Batch"}
            ]
        },
    ]


async def notify_batch_result(news_count: int, youtube_count: int, duration: float, rss_count: int = 0):
    """배치 수집 결과를 Slack으로 알림합니다."""
    blocks = _build_batch_summary_blocks(news_count, youtube_count, duration, rss_count)
    fallback_text = f"일일 수집 완료: 뉴스 {news_count}건, 유튜브 {youtube_count}건, RSS {rss_count}건 ({duration:.2f}초)"

    success = await send_webhook_message(blocks, text=fallback_text)
    if not success:
        logger.error("배치 결과 Slack 알림 전송 실패")
