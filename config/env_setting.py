from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    APP_ENV: str
    CORS_ORIGIN: str = "" # Default to empty string if not set

    # 실행 시점에 APP_ENV 값에 따라 읽어올 .env 파일을 결정합니다.
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('APP_ENV')}"
    )

settings = Settings()