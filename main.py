from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from api.response.exchange_rate_response import ExchangeRateResponse
from api.response.fear_greed_index_response import FearGreedIndexResponse
from api.response.market_index_response import MarketIndexResponse
from api.response.news_item_response import NewsItemResponse
from api.response.youtube_video_response import YouTubeVideoResponse
from config.cors import add_cors_middleware
import typer
import uvicorn
import os
from config.env_setting import settings
from service.get_exchange_rate_service import get_exchange_rate_service

app = FastAPI()
add_cors_middleware(app)

@app.get("/api/news", response_model=List[NewsItemResponse])
def get_news():
    APP_ENV = os.getenv("APP_ENV", "prod")
    print(f"APP_ENV: {settings.CORS_ORIGIN}")
    """뉴스 피드 조회"""
    mock_news_data = [
        {
            "id": "news1",
            "title": "글로벌 증시, 기술주 중심으로 상승 마감",
            "summary": "간밤 뉴욕 증시는 주요 기술 기업들의 실적 호조에 힘입어 상승 마감했습니다.",
            "content": "전체 뉴스 본문입니다. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            "category": "Economy",
            "imageUrl": "https://picsum.photos/seed/news1/800/600",
            "date": "2024.07.28",
            "source": "머니투데이"
        },
        {
            "id": "news2",
            "title": "차세대 AI 모델, 인간 수준의 언어 이해 능력 선보여",
            "summary": "새롭게 공개된 '알파-7' 모델이 복잡한 문맥 파악 및 추론에서 뛰어난 성능을 보였습니다.",
            "content": "알파-7은 자연어 처리 분야의 새로운 지평을 열었습니다. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
            "category": "Tech",
            "imageUrl": "https://picsum.photos/seed/news2/800/600",
            "date": "2024.07.27",
            "source": "전자신문"
        }
    ]
    return mock_news_data

@app.get("/api/youtube/videos", response_model=List[YouTubeVideoResponse])
def get_youtube_videos():
    """유튜브 요약본 조회"""
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

# 기본 루트 엔드포인트 (선택 사항)
@app.get("/")
def read_root():
    return {"message": "Financial Investment Assistant API"}
