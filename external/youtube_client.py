from datetime import datetime
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from config.env_setting import settings


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


def get_channel_upload_playlist_id(channel_id: str) -> str | None:
    """채널의 업로드 플레이리스트 ID를 조회합니다."""
    service = get_youtube_service()

    response = service.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    items = response.get("items", [])
    if items:
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    return None


def fetch_channel_videos(channel_handle: str, max_results: int = 10) -> list[dict]:
    """채널의 최신 영상 목록을 가져옵니다."""
    channel_id = get_channel_id_from_handle(channel_handle)
    if not channel_id:
        raise ValueError(f"채널을 찾을 수 없습니다: {channel_handle}")

    playlist_id = get_channel_upload_playlist_id(channel_id)
    if not playlist_id:
        raise ValueError(f"업로드 플레이리스트를 찾을 수 없습니다: {channel_handle}")

    service = get_youtube_service()

    # 플레이리스트에서 영상 목록 조회
    response = service.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=max_results
    ).execute()

    videos = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        video_id = snippet["resourceId"]["videoId"]

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
    """영상의 자막을 가져옵니다."""
    if languages is None:
        languages = ["ko", "en"]

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=languages)
        return " ".join([entry.text for entry in transcript])

    except TranscriptsDisabled:
        return None
    except NoTranscriptFound:
        return None
    except Exception as e:
        print(f"자막 조회 실패 ({video_id}): {e}")
        return None
