from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import api_client

router = Router()

STATUS_EMOJI = {
    "pending":   "🕐",
    "confirmed": "✅",
    "adjusted":  "📝",
    "paid":      "💳",
    "issued":    "🎉",
    "cancelled": "❌",
}


async def _orders_text_and_kb(orders: list):
    """Возвращает (text, markup) для списка заказов."""
    kb = InlineKeyboardBuilder()
    for o in orders:
        emoji = STATUS_EMOJI.get(o["status"], "•")
        kb.button(
            text=f"{emoji} Заказ #{o['id']} — {o['status_label']}",
            callback_data=f"order_detail_{o['id']}",
        )
    kb.adjust(1)
    return "📋 <b>Мои заказы:</b>", kb.as_markup()


# Вызывается из нижней панели (Message)
async def show_my_orders_message(message: Message):
    orders = await api_client.get_my_orders(message.from_user.id)
    if not orders:
        await message.answer("📋 У вас пока нет заказов.")
        return
    text, markup = await _orders_text_and_kb(orders)
    await message.answer(text, reply_markup=markup, parse_mode="HTML")


# ─── Callback-обработчики ────────────────────────────────────────────────────

@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: CallbackQuery):
    orders = await api_client.get_my_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📋 У вас пока нет заказов.")
        await callback.answer()
        return
    text, markup = await _orders_text_and_kb(orders)
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order_detail_"))
async def show_order_detail(callback: CallbackQuery):
    order_id = int(callback.data[13:])
    orders = await api_client.get_my_orders(callback.from_user.id)
    order = next((o for o in orders if o["id"] == order_id), None)

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    emoji = STATUS_EMOJI.get(order["status"], "•")
    lines = [
        f"• {i['name']} × {i['quantity']} = {i['price'] * i['quantity']:.0f} ₽"
        for i in order["items"]
    ]

    text = (
        f"<b>Заказ #{order['id']}</b>\n"
        f"📅 {order['created_at']}\n"
        f"{emoji} <i>{order['status_label']}</i>\n\n"
        + "\n".join(lines)
        + f"\n\n💰 <b>Итого: {order['total']:.0f} ₽</b>"
    )
    if order.get("comment"):
        text += f"\n💬 {order['comment']}"

    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ К списку заказов", callback_data="my_orders")
    kb.adjust(1)

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()
