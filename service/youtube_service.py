from datetime import datetime, timedelta, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from external.youtube_client import fetch_channel_videos, fetch_video_transcript
from external.db.model import Video
from external.db.repository import VideoRepository, VideoSourceRepository


def _parse_published_date(published_at: str) -> tuple[str, datetime | None]:
    """YouTube 날짜를 YYYY.MM.DD 형식으로 변환합니다."""
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return dt.strftime("%Y.%m.%d"), dt
    except Exception:
        return published_at, None


def _extract_highlights(transcript: str, max_keywords: int = 5) -> list[str]:
    """자막에서 주요 키워드를 추출합니다. (간단한 구현)"""
    # TODO: LLM을 사용한 키워드 추출로 개선 필요
    # 현재는 빈 리스트 반환 (나중에 LLM 연동 시 구현)
    return []



def _video_to_response(video: dict, transcript: str | None, source_name: str | None = None) -> dict:
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
        "source": source_name,
    }


async def get_youtube_videos(session: AsyncSession, offset_days: int = 0, count_days: int = 1) -> list[dict]:
    """DB에 등록된 유튜브 채널에서 영상을 가져옵니다.

    Args:
        session: DB 세션
        offset_days: 오늘로부터의 과거 오프셋 (0 = 오늘, 1 = 어제...)
        count_days: 가져올 날짜 범위 (예: 3이면 3일치)
    """
    sources = await VideoSourceRepository.find_active(session)
    if not sources:
        return []

    # 날짜 범위 계산 (timezone-aware)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today - timedelta(days=offset_days) + timedelta(days=1)
    start_date = end_date - timedelta(days=count_days)

    # YouTube 검색용 날짜 (ISO 8601 형식)
    after_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    before_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    all_videos = []

    for source in sources:
        try:
            videos = fetch_channel_videos(source.channel_handle, max_results=20,
                                          published_after=after_str,
                                          published_before=before_str)

            for video in videos:
                # 자막 가져오기
                transcript = fetch_video_transcript(video["id"])

                video_response = _video_to_response(video, transcript, source.channel_name)
                all_videos.append(video_response)

        except Exception as e:
            print(f"Failed to fetch videos from {source.channel_handle}: {e}")
            continue

    # 날짜 기준 정렬 (최신순)
    all_videos.sort(key=lambda x: x["date"], reverse=True)

    return all_videos


async def save_videos_if_not_exists(videos: list[dict], session: AsyncSession) -> int:
    """중복되지 않는 영상만 저장합니다."""
    if not videos:
        return 0

    saved = 0
    skipped = 0
    for video in videos:
        title = video["title"]
        upload_date = video.get("date", "")

        if await VideoRepository.exists_by_title_and_upload_date(title, upload_date, session):
            skipped += 1
            continue

        v = Video(
            title=title,
            channel_name=video.get("channelName", ""),
            thumbnail_url=video.get("thumbnailUrl", ""),
            video_url=video.get("videoUrl", ""),
            upload_date=upload_date,
            subtitle=video.get("subtitle"),
            summary=video.get("summary"),
            highlights=video.get("highlights", []),
            source=video.get("source"),
        )
        await VideoRepository.save(v, session)
        saved += 1

    if skipped > 0:
        print(f"[유튜브] 중복 {skipped}개 건너뜀")

    return saved
