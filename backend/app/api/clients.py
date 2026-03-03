from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.schemas import UserOut
from app.services.notifier import _send_telegram

router = APIRouter(prefix="/clients", tags=["clients"])

ACTIVE_STATUSES = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.ADJUSTED,
    OrderStatus.PAID,
]


class SendMessageRequest(BaseModel):
    text: str


@router.get("/", response_model=list[UserOut])
async def get_clients(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/{user_id}/orders")
async def get_client_orders(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    total = sum(
        sum(item.price_at_order * item.quantity for item in o.items)
        for o in orders
    )
    return {"orders": orders, "total_amount": total}


@router.post("/{user_id}/message")
async def send_message_to_client(
    user_id: int,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Отправить личное сообщение конкретному клиенту."""
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    await _send_telegram(user.telegram_id, data.text.strip())
    return {"ok": True, "sent_to": user.telegram_id}


@router.post("/broadcast/active-orders")
async def broadcast_active_orders(
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Отправить сообщение всем уникальным клиентам с активными заказами."""
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")

    result = await db.execute(
        select(User)
        .join(Order, Order.user_id == User.id)
        .where(Order.status.in_(ACTIVE_STATUSES))
        .distinct()
    )
    users = result.scalars().all()

    if not users:
        return {"ok": True, "sent": 0, "message": "Нет клиентов с активными заказами"}

    sent = 0
    failed = 0
    for user in users:
        try:
            await _send_telegram(user.telegram_id, data.text.strip())
            sent += 1
        except Exception:
            failed += 1

    return {"ok": True, "sent": sent, "failed": failed}
