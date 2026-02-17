from pydantic import BaseModel, Field


class AdvisorRequest(BaseModel):
    question: str = Field(..., min_length=1, description="투자 관련 질문")
    context_limit: int = Field(default=5, ge=1, le=20, description="검색할 컨텍스트 수")
