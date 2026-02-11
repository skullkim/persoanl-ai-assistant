from datetime import datetime, timedelta, timezone
from config.env_setting import settings
from external.youtube_client import fetch_channel_videos, fetch_video_transcript


def _parse_published_date(published_at: str) -> tuple[str, datetime | None]:
    """YouTube 날짜를 YYYY.MM.DD 형식으로 변환합니다."""
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return dt.strftime("%Y.%m.%d"), dt
    except Exception:
        return published_at, None


def _is_in_date_range(dt: datetime | None, start_date: datetime, end_date: datetime) -> bool:
    """날짜가 지정된 범위 내에 있는지 확인합니다."""
    if dt is None:
        return False
    return start_date <= dt < end_date


def _extract_highlights(transcript: str, max_keywords: int = 5) -> list[str]:
    """자막에서 주요 키워드를 추출합니다. (간단한 구현)"""
    # TODO: LLM을 사용한 키워드 추출로 개선 필요
    # 현재는 빈 리스트 반환 (나중에 LLM 연동 시 구현)
    return []



def _video_to_response(video: dict, transcript: str | None) -> dict:
    """영상 데이터를 API 응답 형식으로 변환합니다."""
    date_str, _ = _parse_published_date(video["published_at"])

    return {
        "id": video["id"],
        "title": video["title"],
        "channelName": video["channel_name"],
        "thumbnailUrl": video["thumbnail_url"],
        "videoUrl": video["video_url"],
        "date": date_str,
        "subtitle": transcript if transcript else None,
        "summary": None,
        "highlights": _extract_highlights(transcript) if transcript else [],
    }


def get_youtube_videos(offset_days: int = 0, count_days: int = 3) -> list[dict]:
    """설정된 채널들에서 영상을 가져옵니다.

    Args:
        offset_days: 오늘로부터의 과거 오프셋 (0 = 오늘, 1 = 어제...)
        count_days: 가져올 날짜 범위 (예: 3이면 3일치)
    """
    channel_handles = settings.YOUTUBE_CHANNEL_HANDLES
    if not channel_handles:
        return []

    # 날짜 범위 계산 (timezone-aware)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today - timedelta(days=offset_days) + timedelta(days=1)
    start_date = end_date - timedelta(days=count_days)

    channels = [c.strip() for c in channel_handles.split(",") if c.strip()]
    all_videos = []

    for channel in channels:
        try:
            videos = fetch_channel_videos(channel, max_results=20)

            for video in videos:
                _, dt = _parse_published_date(video["published_at"])
                if not _is_in_date_range(dt, start_date, end_date):
                    continue

                # 자막 가져오기
                transcript = fetch_video_transcript(video["id"])

                video_response = _video_to_response(video, transcript)
                all_videos.append(video_response)

        except Exception as e:
            print(f"Failed to fetch videos from {channel}: {e}")
            continue

    # 날짜 기준 정렬 (최신순)
    all_videos.sort(key=lambda x: x["date"], reverse=True)

    return all_videos
