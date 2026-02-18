import logging
from decimal import Decimal, ROUND_HALF_UP

import yfinance as yf
from sqlmodel.ext.asyncio.session import AsyncSession

from external.db.model import ExchangeRateHistory, FearGreedIndex
from external.db.repository import ExchangeRateHistoryRepository, FearGreedIndexRepository
from external.fear_greed_client import fetch_fear_greed_index

logger = logging.getLogger(__name__)


async def collect_exchange_rate(session: AsyncSession) -> int:
    """yfinance에서 USD/KRW 환율 이력을 수집하여 DB에 저장합니다.

    Returns:
        신규 저장 건수
    """
    try:
        ticker = yf.Ticker("USDKRW=X")
        hist = ticker.history(period="5d")
    except Exception as e:
        logger.error(f"[환율] yfinance 조회 실패: {e}")
        return 0

    if len(hist) < 2:
        logger.warning("[환율] 충분한 환율 데이터가 없습니다.")
        return 0

    saved = 0
    for i in range(1, len(hist)):
        date_str = hist.index[i].strftime("%Y-%m-%d")

        if await ExchangeRateHistoryRepository.exists_by_date(date_str, session):
            continue

        current = Decimal(str(hist["Close"].iloc[i])).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        previous = Decimal(str(hist["Close"].iloc[i - 1])).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        change = current - previous
        pct = (change / previous * 100).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        record = ExchangeRateHistory(
            record_date=date_str,
            rate=current,
            previous_rate=previous,
            change_amount=change,
            change_percentage=pct,
        )
        await ExchangeRateHistoryRepository.save(record, session)
        saved += 1
        logger.info(f"[환율] {date_str}: {current} (변동 {change:+})")

    return saved


async def collect_fear_greed_index(session: AsyncSession) -> int:
    """CNN Fear & Greed Index를 수집하여 DB에 저장합니다.

    Returns:
        신규 저장 건수
    """
    data = await fetch_fear_greed_index()
    if data is None:
        logger.warning("[공포/탐욕] 데이터를 가져올 수 없습니다.")
        return 0

    date_str = data["date"]
    if await FearGreedIndexRepository.exists_by_date(date_str, session):
        logger.info(f"[공포/탐욕] {date_str} 이미 존재")
        return 0

    record = FearGreedIndex(
        record_date=date_str,
        value=data["value"],
        label=data["label"],
    )
    await FearGreedIndexRepository.save(record, session)
    logger.info(f"[공포/탐욕] {date_str}: {data['value']} ({data['label']})")
    return 1
