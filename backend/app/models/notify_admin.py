from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class NotifyAdmin(Base):
    __tablename__ = "notify_admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    label: Mapped[str | None] = mapped_column(String(255))  # имя/пометка
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
