from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./shop.db"
    SECRET_KEY: str = "change_me_in_production_please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    BOT_TOKEN: str = ""

    # Основной ID администратора (старое поле, оставляем для совместимости)
    ADMIN_TELEGRAM_ID: int = 0

    # Список ID через запятую: "123456,789012,345678"
    # Если указан — используется вместо ADMIN_TELEGRAM_ID
    ADMIN_TELEGRAM_IDS: str = ""

    API_BASE_URL: str = "http://backend:8000"
    BOT_API_SECRET: str = "bot_secret_key_change_me"

    def get_admin_ids(self) -> List[int]:
        """Возвращает список всех Telegram ID администраторов."""
        ids = set()
        # Из нового поля
        if self.ADMIN_TELEGRAM_IDS:
            for part in self.ADMIN_TELEGRAM_IDS.split(","):
                part = part.strip()
                if part.isdigit():
                    ids.add(int(part))
        # Из старого поля (для обратной совместимости)
        if self.ADMIN_TELEGRAM_ID:
            ids.add(self.ADMIN_TELEGRAM_ID)
        return list(ids)

    class Config:
        env_file = ".env"

settings = Settings()