from pydantic import BaseModel

class FearGreedIndexResponse(BaseModel):
    value: int
    label: str
