import time
from datetime import datetime
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, RequestBlocked
from config.env_setting import settings

TRANSCRIPT_DELAY_SEC = 3
TRANSCRIPT_MAX_RETRIES = 3
TRANSCRIPT_RETRY_DELAY_SEC = 10


def get_youtube_service():
    """YouTube Data API 서비스 인스턴스를 반환합니다."""
    if not settings.YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
    return build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)


def get_channel_id_from_handle(handle: str) -> str | None:
    """채널 핸들(@username)로 채널 ID를 조회합니다."""
    service = get_youtube_service()

    # @ 제거
    handle = handle.lstrip("@")

    response = service.channels().list(
        part="id",
        forHandle=handle
    ).execute()

    items = response.get("items", [])
    if items:
        return items[0]["id"]
    return None


def fetch_channel_videos(channel_handle: str, max_results: int = 10,
                         published_after: str | None = None,
                         published_before: str | None = None) -> list[dict]:
    """채널의 영상 목록을 가져옵니다.

    Args:
        channel_handle: 채널 핸들 (@username)
        max_results: 최대 결과 수
        published_after: 이 날짜 이후 (ISO 8601 형식, e.g. 2026-01-01T00:00:00Z)
        published_before: 이 날짜 이전 (ISO 8601 형식)
    """
    channel_id = get_channel_id_from_handle(channel_handle)
    if not channel_id:
        raise ValueError(f"채널을 찾을 수 없습니다: {channel_handle}")

    service = get_youtube_service()

    search_params = {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "maxResults": max_results,
    }
    if published_after:
        search_params["publishedAfter"] = published_after
    if published_before:
        search_params["publishedBefore"] = published_before

    response = service.search().list(**search_params).execute()

    videos = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        video_id = item["id"]["videoId"]

        videos.append({
            "id": video_id,
            "title": snippet["title"],
            "channel_name": snippet["channelTitle"],
            "thumbnail_url": snippet["thumbnails"].get("high", {}).get("url", ""),
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "published_at": snippet["publishedAt"],
        })

    return videos


def fetch_video_transcript(video_id: str, languages: list[str] = None) -> str | None:
    """영상의 자막을 가져옵니다. IP 차단 시 딜레이 후 재시도합니다."""
    if languages is None:
        languages = ["ko", "en"]

    for attempt in range(1, TRANSCRIPT_MAX_RETRIES + 1):
        try:
            time.sleep(TRANSCRIPT_DELAY_SEC)
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(video_id, languages=languages)
            return " ".join([entry.text for entry in transcript])

        except TranscriptsDisabled:
            return None
        except NoTranscriptFound:
            return None
        except RequestBlocked:
            if attempt < TRANSCRIPT_MAX_RETRIES:
                wait = TRANSCRIPT_RETRY_DELAY_SEC * attempt
                print(f"자막 IP 차단 ({video_id}), {wait}초 후 재시도 ({attempt}/{TRANSCRIPT_MAX_RETRIES})")
                time.sleep(wait)
            else:
                print(f"자막 IP 차단 ({video_id}), 최대 재시도 초과 - 건너뜀")
                return None
        except Exception as e:
            print(f"자막 조회 실패 ({video_id}): {e}")
            return None
