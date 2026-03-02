from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import api_client
from handlers.cart import get_cart, save_cart

router = Router()

class OrderFSM(StatesGroup):
    waiting_comment = State()

@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart(state)
    if not cart:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    await state.set_state(OrderFSM.waiting_comment)

    kb = InlineKeyboardBuilder()
    kb.button(text="➡️ Без комментария", callback_data="order_no_comment")
    kb.button(text="❌ Отмена", callback_data="cart_view")
    kb.adjust(1)

    try:
        await callback.message.edit_text(
            "💬 Введите комментарий к заказу\n(например: без лука, позвонить перед доставкой)\n\nИли нажмите «Без комментария»:",
            reply_markup=kb.as_markup(),
        )
    except Exception:
        await callback.message.answer(
            "💬 Введите комментарий или нажмите «Без комментария»:",
            reply_markup=kb.as_markup(),
        )
    await callback.answer()

@router.callback_query(F.data == "order_no_comment", OrderFSM.waiting_comment)
async def order_no_comment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await place_order(callback.message, callback.from_user.id, None, state)
    await callback.answer()

@router.message(OrderFSM.waiting_comment, F.text)
async def order_with_comment(message: Message, state: FSMContext):
    await state.clear()
    await place_order(message, message.from_user.id, message.text, state)

async def place_order(message, telegram_id: int, comment: str | None, state: FSMContext):
    # Получаем корзину заново (state уже очищен, нужно читать до clear)
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        # На случай если корзина уже была сохранена в state до clear
        await message.answer("❌ Корзина пуста. Начните заново с /start")
        return

    items = [{"product_id": int(pid), "quantity": qty} for pid, qty in cart.items()]

    try:
        order = await api_client.create_order(telegram_id, comment, items)

        # Очищаем корзину после успешного заказа
        await state.update_data(cart={})

        kb = InlineKeyboardBuilder()
        kb.button(text="🛍 Продолжить покупки", callback_data="catalog")

        text = (
            f"✅ <b>Заказ #{order['id']} оформлен!</b>\n\n"
            f"Статус: <i>На подтверждении</i>\n"
            f"Мы уведомим вас о каждом изменении статуса."
        )
        if comment:
            text += f"\n\n💬 Ваш комментарий: {comment}"

        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при оформлении заказа. Попробуйте позже.\n\n<code>{e}</code>",
            parse_mode="HTML"
        )
