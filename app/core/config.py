from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    TEST_DATABASE_URL: str

    SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 30

    PASSWORD_RESET_EXPIRE_MINUTES: int = 15

    ALGORITHM: str = "HS256"

    # FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://127.0.0.1:5500"

    REDIS_URL: str

    SMTP_HOST: str

    SMTP_PORT: int = 587

    SMTP_USERNAME: str

    SMTP_PASSWORD: str

    SMTP_FROM_EMAIL: str

    SMTP_FROM_NAME: str = "Enterprise Task API"

    MAX_FILE_SIZE_MB: int = 10

    UPLOAD_DIR: str = "uploads"

    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,application/pdf,text/plain"

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    ENVIRONMENT: str = "development"

    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore[call-arg]

