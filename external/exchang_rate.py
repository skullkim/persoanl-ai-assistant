import yfinance as yf
from fastapi import HTTPException

def get_latest_exchange_rate():
    ticker = yf.Ticker("USDKRW=X")
    # 주말/휴장일을 고려해 5일치 데이터를 가져옵니다.
    hist = ticker.history(period="5d")

    # 데이터가 2개 이상은 있어야 변동률 계산이 가능합니다.
    if len(hist) < 2:
        raise HTTPException(status_code=404, detail="비교할 수 있는 충분한 환율 데이터가 없습니다.")

    # 1. 가장 최신 데이터 (마지막 행)
    latest_close = hist['Close'].iloc[-1]
    latest_date = hist.index[-1].strftime('%Y-%m-%d')

    # 2. 직전 영업일 데이터 (마지막에서 두 번째 행)
    previous_close = hist['Close'].iloc[-2]

    # 3. 변동 계산 (최신 - 직전)
    change_amount = latest_close - previous_close
    # 변동률 공식: ((현재값 - 이전값) / 이전값) * 100
    change_percentage = (change_amount / previous_close) * 100

    return {
        "rate": round(latest_close, 2),
        "date": latest_date,
        "change_amount": round(change_amount, 2),
        "change_percentage": f"{change_percentage:+.2f}%",  # + 기호를 붙여 상승/하락 표시
        "previous_close": round(previous_close, 2),
        "source": "Yahoo Finance"
    }