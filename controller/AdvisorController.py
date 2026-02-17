from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from external.db import get_session
from service.investment_advisor_service import ask_advisor
from controller.model.request.advisor_request import AdvisorRequest
from controller.model.response.advisor_response import AdvisorResponse

router = APIRouter(prefix="/api/advisor", tags=["Advisor"])


async def get_db_session():
    """DB 세션 의존성"""
    session_factory = get_session()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post("/ask", response_model=AdvisorResponse)
async def ask(request: AdvisorRequest, session: AsyncSession = Depends(get_db_session)):
    """RAG 기반 투자 비서에게 질문합니다."""
    result = await ask_advisor(
        question=request.question,
        session=session,
        context_limit=request.context_limit,
    )
    return AdvisorResponse(**result)
