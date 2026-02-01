from pydantic import BaseModel

class MarketIndexResponse(BaseModel):
    date: str
    close: float
