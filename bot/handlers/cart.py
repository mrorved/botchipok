from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import api_client

router = Router()

async def get_cart(state: FSMContext) -> dict:
    data = await state.get_data()
    return data.get("cart", {})

async def save_cart(state: FSMContext, cart: dict):
    await state.update_data(cart=cart)

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data[12:])
    cart = await get_cart(state)
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    await save_cart(state, cart)

    product = await api_client.get_product(product_id)
    qty = cart[key]

    kb = InlineKeyboardBuilder()
    kb.button(text=f"➕ Ещё {product['name']}", callback_data=f"add_to_cart_{product_id}")
    kb.button(text=f"🛒 Корзина ({sum(cart.values())})", callback_data="cart_view")
    kb.button(text="🛍 Каталог", callback_data="catalog")
    kb.adjust(1)

    text = (
        f"✅ <b>{product['name']}</b> добавлен в корзину\n"
        f"Количество: {qty} шт.\n"
        f"💰 {product['price'] * qty} ₽"
    )

    try:
        # Если сообщение с фото — редактируем caption
        await callback.message.edit_caption(caption=text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        except Exception:
            await callback.answer(f"✅ {product['name']} добавлен (x{qty})", show_alert=False)

    await callback.answer(f"✅ Добавлено в корзину x{qty}")

@router.callback_query(F.data == "cart_view")
async def view_cart(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart(state)
    if not cart:
        kb = InlineKeyboardBuilder()
        kb.button(text="🛍 В каталог", callback_data="catalog")
        try:
            await callback.message.edit_text("🛒 Корзина пуста", reply_markup=kb.as_markup())
        except Exception:
            await callback.message.answer("🛒 Корзина пуста", reply_markup=kb.as_markup())
        await callback.answer()
        return

    lines = []
    total = 0.0
    for product_id_str, qty in cart.items():
        product = await api_client.get_product(int(product_id_str))
        price = product["price"] * qty
        total += price
        lines.append(f"• {product['name']} × {qty} = {price:.0f} ₽")

    text = "🛒 <b>Ваша корзина:</b>\n\n" + "\n".join(lines) + f"\n\n💰 <b>Итого: {total:.0f} ₽</b>"

    kb = InlineKeyboardBuilder()
    for product_id_str in list(cart.keys()):
        product = await api_client.get_product(int(product_id_str))
        kb.button(
            text=f"➖ {product['name']} (x{cart[product_id_str]})",
            callback_data=f"remove_from_cart_{product_id_str}",
        )
    kb.button(text="✅ Оформить заказ", callback_data="checkout")
    kb.button(text="🗑 Очистить корзину", callback_data="cart_clear")
    kb.button(text="🛍 Продолжить покупки", callback_data="catalog")
    kb.adjust(1)

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery, state: FSMContext):
    product_id_str = callback.data[17:]
    cart = await get_cart(state)
    if product_id_str in cart:
        cart[product_id_str] -= 1
        if cart[product_id_str] <= 0:
            del cart[product_id_str]
    await save_cart(state, cart)
    await view_cart(callback, state)

@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery, state: FSMContext):
    await save_cart(state, {})
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 В каталог", callback_data="catalog")
    try:
        await callback.message.edit_text("🗑 Корзина очищена", reply_markup=kb.as_markup())
    except Exception:
        await callback.message.answer("🗑 Корзина очищена", reply_markup=kb.as_markup())
    await callback.answer()
