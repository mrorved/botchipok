from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_BASE_URL: str = "http://backend:8000"
    BOT_API_SECRET: str = "bot_secret_key_change_me"

    class Config:
        env_file = ".env"

settings = Settings()
