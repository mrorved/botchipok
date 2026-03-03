import httpx
from app.core.config import settings
from app.models.order import OrderStatus

STATUS_MESSAGES = {
    OrderStatus.PAID: "💳 Ваш заказ #{order_id} оплачен. Ожидайте выдачи.",
    OrderStatus.ISSUED: "🎉 Ваш заказ #{order_id} выдан! Спасибо за покупку.",
}


async def _send_telegram(chat_id: int, text: str):
    if not settings.BOT_TOKEN:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=5,
            )
    except Exception:
        pass


async def notify_user_status_change(telegram_id: int, order_id: int, status: OrderStatus):
    template = STATUS_MESSAGES.get(status)
    if not template:
        return
    await _send_telegram(telegram_id, template.format(order_id=order_id))


async def notify_user_confirmed(telegram_id: int, order_id: int, items: list, total: float):
    """
    Отправляет детальное сообщение при подтверждении заказа (confirmed / adjusted).
    items — список dict: {"name": str, "quantity": int, "price": float, "removed": bool}
    """
    lines = []
    has_removed = False

    for i, item in enumerate(items, 1):
        if item["removed"]:
            lines.append(f"  {i}. {item['name']} — <s>нет на складе</s>")
            has_removed = True
        else:
            lines.append(f"  {i}. {item['name']} × {item['quantity']} = {item['price'] * item['quantity']:.0f} ₽")

    items_text = "\n".join(lines)

    if has_removed:
        header = f"📝 <b>Ваш заказ #{order_id} подтверждён с корректировкой</b>"
        footer = (
            f"\n⚠️ Некоторые позиции недоступны и были убраны из заказа.\n"
            f"\n💰 <b>Итоговая сумма: {total:.0f} ₽</b>"
        )
    else:
        header = f"✅ <b>Ваш заказ #{order_id} подтверждён</b>"
        footer = f"\n💰 <b>Итоговая сумма: {total:.0f} ₽</b>"

    text = f"{header}\n\n{items_text}{footer}"
    await _send_telegram(telegram_id, text)


async def notify_user_order_cancelled(telegram_id: int, order_id: int):
    await _send_telegram(telegram_id, f"❌ Ваш заказ #{order_id} был отменён.")


async def notify_admin_new_order(order_id: int, user):
    if not settings.ADMIN_TELEGRAM_ID:
        return
    name = user.full_name or user.username or str(user.telegram_id)
    await _send_telegram(
        settings.ADMIN_TELEGRAM_ID,
        f"🛍 Новый заказ #{order_id} от {name}"
    )
