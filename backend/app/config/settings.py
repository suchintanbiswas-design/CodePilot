from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "CodePilot"
    APP_ENV: str = "development"
    DEBUG: bool = True

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "codepilot"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    JWT_SECRET_KEY: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    MAX_UPLOAD_SIZE_BYTES: int = 2097152
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ADMIN_EMAIL: str = "admin@codepilot.local"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"

    DATABASE_URL: str | None = None

    @model_validator(mode='after')
    def assemble_db_connection(self):
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
