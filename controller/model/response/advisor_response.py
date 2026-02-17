from pydantic import BaseModel


class SourceInfo(BaseModel):
    source_type: str
    source_id: int
    score: float
    metadata: dict = {}


class AdvisorResponse(BaseModel):
    answer: str
    sources: list[SourceInfo] = []
    context_count: int = 0
