import httpx
from app.core.config import settings
from app.models.order import OrderStatus


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


async def _get_notify_admin_ids() -> list[int]:
    """Получить список активных Telegram ID администраторов из БД."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.notify_admin import NotifyAdmin
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NotifyAdmin.telegram_id).where(NotifyAdmin.is_active == True)
            )
            ids = result.scalars().all()
            if ids:
                return list(ids)
    except Exception:
        pass
    # Fallback к .env если БД недоступна
    return settings.get_admin_ids()


async def notify_user_status_change(telegram_id: int, order_id: int, status: OrderStatus):
    STATUS_MESSAGES = {
        OrderStatus.PAID: "💳 Ваш заказ #{order_id} оплачен. Ожидайте выдачи.",
        OrderStatus.ISSUED: "🎉 Ваш заказ #{order_id} выдан! Спасибо за покупку.",
    }
    template = STATUS_MESSAGES.get(status)
    if not template:
        return
    await _send_telegram(telegram_id, template.format(order_id=order_id))


async def notify_user_confirmed(
    telegram_id: int,
    order_id: int,
    items: list,
    total: float,
    force_adjusted: bool = False,
):
    lines = []
    has_removed = force_adjusted

    for i, item in enumerate(items, 1):
        if item["removed"]:
            lines.append(f"  {i}. {item['name']} \u2014 <s>\u043d\u0435\u0442 \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435</s>")
            has_removed = True
        else:
            lines.append(
                f"  {i}. {item['name']} \u00d7 {item['quantity']} = "
                f"{item['price'] * item['quantity']:.0f} \u20bd"
            )

    items_text = "\n".join(lines)

    if has_removed:
        header = f"\U0001f4dd <b>\u0412\u0430\u0448 \u0437\u0430\u043a\u0430\u0437 #{order_id} \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d \u0441 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u043e\u0439</b>"
        footer = (
            f"\n\n\u26a0\ufe0f \u041d\u0435\u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u043f\u043e\u0437\u0438\u0446\u0438\u0438 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b \u0438 \u0431\u044b\u043b\u0438 \u0443\u0431\u0440\u0430\u043d\u044b \u0438\u0437 \u0437\u0430\u043a\u0430\u0437\u0430."
            f"\n\n\U0001f4b0 <b>\u0418\u0442\u043e\u0433\u043e\u0432\u0430\u044f \u0441\u0443\u043c\u043c\u0430: {total:.0f} \u20bd</b>"
        )
    else:
        header = f"\u2705 <b>\u0412\u0430\u0448 \u0437\u0430\u043a\u0430\u0437 #{order_id} \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d</b>"
        footer = f"\n\n\U0001f4b0 <b>\u0418\u0442\u043e\u0433\u043e\u0432\u0430\u044f \u0441\u0443\u043c\u043c\u0430: {total:.0f} \u20bd</b>"

    text = f"{header}\n\n{items_text}{footer}"
    await _send_telegram(telegram_id, text)


async def notify_user_order_cancelled(telegram_id: int, order_id: int):
    await _send_telegram(telegram_id, f"\u274c \u0412\u0430\u0448 \u0437\u0430\u043a\u0430\u0437 #{order_id} \u0431\u044b\u043b \u043e\u0442\u043c\u0435\u043d\u0451\u043d.")


async def notify_admin_new_order(order_id: int, user):
    """Уведомить всех активных администраторов о новом заказе."""
    admin_ids = await _get_notify_admin_ids()
    if not admin_ids:
        return
    name = user.full_name or user.username or str(user.telegram_id)
    phone = f" \u00b7 {user.phone}" if getattr(user, "phone", None) else ""
    tg = f" (@{user.username})" if user.username else ""
    text = f"\U0001f6cd \u041d\u043e\u0432\u044b\u0439 \u0437\u0430\u043a\u0430\u0437 #{order_id}\n\u041a\u043b\u0438\u0435\u043d\u0442: {name}{tg}{phone}"
    for admin_id in admin_ids:
        await _send_telegram(admin_id, text)


async def notify_admins_status_change(order_id: int, user, old_status: str, new_status: str):
    """Уведомить всех активных администраторов о смене статуса заказа."""
    admin_ids = await _get_notify_admin_ids()
    if not admin_ids:
        return

    STATUS_LABELS = {
        "pending": "\u041d\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0438",
        "confirmed": "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d",
        "adjusted": "\u0421 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u043e\u0439",
        "paid": "\u041e\u043f\u043b\u0430\u0447\u0435\u043d",
        "issued": "\u0412\u044b\u0434\u0430\u043d",
        "cancelled": "\u041e\u0442\u043c\u0435\u043d\u0451\u043d",
    }
    STATUS_EMOJI = {
        "confirmed": "\u2705", "adjusted": "\U0001f4dd", "paid": "\U0001f4b3",
        "issued": "\U0001f389", "cancelled": "\u274c",
    }
    name = user.full_name or user.username or str(user.telegram_id)
    tg = f" (@{user.username})" if user.username else ""
    emoji = STATUS_EMOJI.get(new_status, "\u2022")
    label = STATUS_LABELS.get(new_status, new_status)
    text = f"{emoji} \u0417\u0430\u043a\u0430\u0437 #{order_id} \u2192 <b>{label}</b>\n\u041a\u043b\u0438\u0435\u043d\u0442: {name}{tg}"
    for admin_id in admin_ids:
        await _send_telegram(admin_id, text)
