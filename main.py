from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from config.cors import add_cors_middleware
from config.env_setting import settings
from external.db import init_db, close_db
from external import slack_bot

from controller.HealthController import router as health_router
from controller.AdvisorController import router as advisor_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    logger.info("서버 시작 중...")
    try:
        await init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise

    # Slack 봇 시작 (토큰 미설정 시 스킵)
    if settings.SLACK_BOT_TOKEN and settings.SLACK_APP_TOKEN:
        try:
            await slack_bot.start()
        except Exception as e:
            logger.error(f"Slack 봇 시작 실패: {e}")
    else:
        logger.info("Slack 봇 토큰 미설정 — 봇 시작 스킵")

    yield

    logger.info("서버 종료 중...")
    await slack_bot.stop()
    await close_db()
    logger.info("서버 종료 완료")


app = FastAPI(lifespan=lifespan)
add_cors_middleware(app)

# 컨트롤러 등록
app.include_router(health_router)
app.include_router(advisor_router)
