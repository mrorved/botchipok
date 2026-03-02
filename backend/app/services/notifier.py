import httpx
from app.core.config import settings
from app.models.order import OrderStatus

STATUS_MESSAGES = {
    OrderStatus.CONFIRMED: "✅ Ваш заказ #{order_id} подтверждён!",
    OrderStatus.ADJUSTED: "📝 Ваш заказ #{order_id} подтверждён с корректировкой. Уточните детали у менеджера.",
    OrderStatus.PAID: "💳 Ваш заказ #{order_id} оплачен. Ожидайте выдачи.",
    OrderStatus.ISSUED: "🎉 Ваш заказ #{order_id} выдан! Спасибо за покупку.",
}

async def notify_user_status_change(telegram_id: int, order_id: int, status: OrderStatus):
    template = STATUS_MESSAGES.get(status)
    if not template or not settings.BOT_TOKEN:
        return
    text = template.format(order_id=order_id)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                json={"chat_id": telegram_id, "text": text},
                timeout=5,
            )
    except Exception:
        pass

async def notify_admin_new_order(order_id: int, user):
    if not settings.BOT_TOKEN or not settings.ADMIN_TELEGRAM_ID:
        return
    name = user.full_name or user.username or str(user.telegram_id)
    text = f"🛍 Новый заказ #{order_id} от {name}"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                json={"chat_id": settings.ADMIN_TELEGRAM_ID, "text": text},
                timeout=5,
            )
    except Exception:
        pass

async def notify_user_order_cancelled(telegram_id: int, order_id: int):
    if not settings.BOT_TOKEN:
        return
    text = f"❌ Ваш заказ #{order_id} был отменён."
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                json={"chat_id": telegram_id, "text": text},
                timeout=5,
            )
    except Exception:
        pass
