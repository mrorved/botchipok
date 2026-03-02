from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./shop.db"
    SECRET_KEY: str = "change_me_in_production_please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_ID: int = 0
    API_BASE_URL: str = "http://backend:8000"
    BOT_API_SECRET: str = "bot_secret_key_change_me"

    class Config:
        env_file = ".env"

settings = Settings()
