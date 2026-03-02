from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Float, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from datetime import datetime
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"
    PAID = "paid"
    ISSUED = "issued"
    CANCELLED = "cancelled"

STATUS_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.ADJUSTED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.ADJUSTED, OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.ADJUSTED: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.ISSUED],
    OrderStatus.ISSUED: [],
    OrderStatus.CANCELLED: [],
}

STATUS_LABELS = {
    OrderStatus.PENDING: "На подтверждении",
    OrderStatus.CONFIRMED: "Подтверждён",
    OrderStatus.ADJUSTED: "Подтверждён с корректировкой",
    OrderStatus.PAID: "Оплачен",
    OrderStatus.ISSUED: "Выдан",
    OrderStatus.CANCELLED: "Отменён",
}

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    # nullable + SET NULL: при удалении товара позиция сохраняется, product станет None
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_order: Mapped[float] = mapped_column(Float)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product | None"] = relationship("Product", back_populates="order_items")
