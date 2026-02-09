from fastapi import APIRouter
from typing import List

from controller.model.response.email_response import EmailResponse
from service.gmail_service import get_emails_from_sender

router = APIRouter(prefix="/api", tags=["email"])


@router.get("/emails", response_model=List[EmailResponse])
def get_emails(sender: str, max_results: int = 10):
    """특정 발신자의 이메일 목록 조회"""
    return get_emails_from_sender(sender, max_results)
