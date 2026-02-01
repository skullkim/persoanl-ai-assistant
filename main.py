from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from api.response.exchange_rate_response import ExchangeRateResponse
from api.response.fear_greed_index_response import FearGreedIndexResponse
from api.response.market_index_response import MarketIndexResponse
from api.response.news_item_response import NewsItemResponse
from api.response.youtube_video_response import YouTubeVideoResponse
from api.response.email_response import EmailResponse
from config.cors import add_cors_middleware
import typer
import uvicorn
import os
from config.env_setting import settings
from service.get_exchange_rate_service import get_exchange_rate_service
from service.gmail_service import get_emails_from_sender
from service.news_service import get_news_from_emails

app = FastAPI()
add_cors_middleware(app)

@app.get("/api/news", response_model=List[NewsItemResponse])
def get_news(offsetDays: int = 0, countDays: int = 3):
    """뉴스 피드 조회 - Gmail 뉴스레터에서 수집"""
    return get_news_from_emails(offset_days=offsetDays, count_days=countDays)

@app.get("/api/youtube/videos", response_model=List[YouTubeVideoResponse])
def get_youtube_videos(offsetDays: int = 0, countDays: int = 3):
    """유튜브 요약본 조회"""
    # TODO: 실제 유튜브 데이터 연동 필요
    mock_youtube_data = [
        {
            "id": "youtube1",
            "title": "2024년 하반기 투자 전략, 지금 주목해야 할 섹터는?",
            "channelName": "슈카월드",
            "thumbnailUrl": "https://picsum.photos/seed/youtube1/480/360",
            "videoUrl": "https://www.youtube.com/watch?v=example1",
            "date": "2024.07.26",
            "summary": """
- 하반기 시장 변동성 확대 예상
- 인플레이션 둔화 및 금리 인하 기대감 공존
- AI, 반도체 섹터의 지속적인 성장 모멘텀
- 신재생에너지 관련주 주목 필요
        """,
            "highlights": ["하반기 시장", "금리 인하", "AI", "신재생에너지"],
            "sentiment": "Neutral"
        },
        {
            "id": "youtube2",
            "title": "미 연준의 깜짝 발표! 시장은 어떻게 반응했나?",
            "channelName": "삼프로TV",
            "thumbnailUrl": "https://picsum.photos/seed/youtube2/480/360",
            "videoUrl": "https://www.youtube.com/watch?v=example2",
            "date": "2024.07.25",
            "summary": """
- 연준, 기준금리 동결 결정
- 예상보다 매파적인 발언으로 시장 단기 충격
- 달러 강세, 국채 금리 상승
- 향후 지표에 따른 조건부 인하 가능성 시사
        """,
            "highlights": ["기준금리 동결", "매파적 발언", "달러 강세"],
            "sentiment": "Negative"
        }
    ]

    return mock_youtube_data

@app.get("/api/investment/exchange-rate", response_model=ExchangeRateResponse)
def get_exchange_rate():
    exchange_rate = get_exchange_rate_service()
    return exchange_rate


@app.get("/api/investment/market-index", response_model=List[MarketIndexResponse])
def get_market_index():
    """시장 지수 조회"""
    mock_market_index_data = [
        {"date": "07-22", "close": 6915.61},
        {"date": "07-23", "close": 6950.12},
        {"date": "07-24", "close": 6930.45},
        {"date": "07-25", "close": 7010.88},
        {"date": "07-26", "close": 7050.21},
    ]

    return mock_market_index_data

@app.get("/api/investment/fear-greed-index", response_model=FearGreedIndexResponse)
def get_fear_greed_index():
    """공포 지수 조회"""
    return {
      "value": 68,
      "label": "Greed"
    }

# Gmail 이메일 조회
@app.get("/api/emails", response_model=List[EmailResponse])
def get_emails(sender: str, max_results: int = 10):
    """특정 발신자의 이메일 목록 조회"""
    return get_emails_from_sender(sender, max_results)


# 기본 루트 엔드포인트 (선택 사항)
@app.get("/")
def read_root():
    return {"message": "Financial Investment Assistant API"}
