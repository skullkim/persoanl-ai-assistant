from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    APP_ENV: str
    CORS_ORIGIN: str = ""
    NEWS_SENDER_EMAILS: str = ""  # 콤마로 구분된 발신자 이메일 목록
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CHANNEL_HANDLES: str = ""  # 콤마로 구분된 채널 핸들 (@channel)
    GOOGLE_CSE_ID: str = ""  # Google Custom Search Engine ID
    RSS_FEED_URLS: str = ""  # 콤마로 구분된 RSS 피드 URL

    # Slack
    SLACK_WEBHOOK_URL: str = ""
    SLACK_SUMMARY_WEBHOOK_URL: str = ""
    SLACK_REPORT_WEBHOOK_URL: str = ""
    SLACK_BOT_TOKEN: str = ""   # xoxb-...
    SLACK_APP_TOKEN: str = ""   # xapp-...

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma3:12b"
    EMBED_MODEL: str = "snowflake-arctic-embed2"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "financial_assistant"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # Database Pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_CONNECT_TIMEOUT: int = 10
    DB_COMMAND_TIMEOUT: int = 60

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