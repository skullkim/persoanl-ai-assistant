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
from service.youtube_service import get_youtube_videos as get_youtube_videos_service

app = FastAPI()
add_cors_middleware(app)

@app.get("/api/news", response_model=List[NewsItemResponse])
def get_news(offsetDays: int = 0, countDays: int = 3):
    """뉴스 피드 조회 - Gmail 뉴스레터에서 수집"""
    return get_news_from_emails(offset_days=offsetDays, count_days=countDays)

@app.get("/api/youtube/videos", response_model=List[YouTubeVideoResponse])
def get_youtube_videos(offsetDays: int = 0, countDays: int = 3):
    """유튜브 요약본 조회 - YouTube Data API에서 수집"""
    return get_youtube_videos_service(offset_days=offsetDays, count_days=countDays)

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
