import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

CNN_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


async def fetch_fear_greed_index() -> dict | None:
    """CNN Fear & Greed Index API에서 현재 공포/탐욕 지수를 가져옵니다.

    Returns:
        {"value": int, "label": str, "date": str} 또는 실패 시 None
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"{CNN_API_URL}/{today_str}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()

        data = resp.json()
        fg = data.get("fear_and_greed", {})
        score = fg.get("score")
        rating = fg.get("rating")

        if score is None or rating is None:
            logger.warning(f"[공포/탐욕] 응답에서 score/rating을 찾을 수 없음: {fg}")
            return None

        return {
            "value": round(score),
            "label": rating,
            "date": today_str,
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"[공포/탐욕] API HTTP 오류: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"[공포/탐욕] API 호출 실패: {e}")
        return None
