from fastapi import APIRouter
from typing import List

from controller.model.response.exchange_rate_response import ExchangeRateResponse
from controller.model.response.fear_greed_index_response import FearGreedIndexResponse
from controller.model.response.market_index_response import MarketIndexResponse
from service.get_exchange_rate_service import get_exchange_rate_service

router = APIRouter(prefix="/api/investment", tags=["investment"])


@router.get("/exchange-rate", response_model=ExchangeRateResponse)
def get_exchange_rate():
    """환율 조회"""
    return get_exchange_rate_service()


@router.get("/market-index", response_model=List[MarketIndexResponse])
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


@router.get("/fear-greed-index", response_model=FearGreedIndexResponse)
def get_fear_greed_index():
    """공포 지수 조회"""
    return {
        "value": 68,
        "label": "Greed"
    }
