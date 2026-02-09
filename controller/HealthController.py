from fastapi import APIRouter

from external.db import check_db_health

router = APIRouter(tags=["health"])


@router.get("/")
def read_root():
    """기본 루트 엔드포인트"""
    return {"message": "Financial Investment Assistant API"}


@router.get("/health")
async def health_check():
    """서버 및 데이터베이스 상태 확인"""
    db_health = await check_db_health()
    is_healthy = db_health["status"] == "healthy"

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "components": {
            "server": "running",
            "database": db_health
        }
    }
