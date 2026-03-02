from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
import enum

class AdminRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole), default=AdminRole.MANAGER)
