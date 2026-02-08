from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    APP_ENV: str
    CORS_ORIGIN: str = ""
    NEWS_SENDER_EMAILS: str = ""  # 콤마로 구분된 발신자 이메일 목록
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CHANNEL_HANDLES: str = ""  # 콤마로 구분된 채널 핸들 (@channel)

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "financial_assistant"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 연결 URL을 생성합니다."""
        if self.DB_PASSWORD:
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 실행 시점에 APP_ENV 값에 따라 읽어올 .env 파일을 결정합니다.
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('APP_ENV')}",
        extra="ignore"
    )

settings = Settings()