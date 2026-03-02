from sqlalchemy import String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(50))    # шт., кг, л, уп. и т.д.
    weight: Mapped[str | None] = mapped_column(String(100))  # фасовка: 1.1 кг, 500 мл и т.д.
    photo_url: Mapped[str | None] = mapped_column(String(500))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category | None"] = relationship("Category", back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
