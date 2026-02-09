from pydantic import BaseModel

class ExchangeRateResponse(BaseModel):
    rate: float
    change: float
    lastUpdated: str
