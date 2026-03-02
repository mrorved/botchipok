from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import api_client

router = Router()

class RegistrationFSM(StatesGroup):
    waiting_phone = State()


# ─── Постоянная нижняя панель ────────────────────────────────────────────────

def main_menu_reply_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛍 Каталог"),
                KeyboardButton(text="🛒 Корзина"),
            ],
            [
                KeyboardButton(text="📋 Мои заказы"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,        # не скрывается после нажатия
    )


# ─── /start и регистрация ────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await api_client.upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )

    if user.get("phone"):
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\nДобро пожаловать в наш магазин.",
            reply_markup=main_menu_reply_kb(),
        )
        return

    await state.set_state(RegistrationFSM.waiting_phone)
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Для оформления заказов нам нужен ваш номер телефона.\n"
        "Нажмите кнопку ниже, чтобы поделиться им:",
        reply_markup=phone_kb,
    )


@router.message(RegistrationFSM.waiting_phone, F.contact)
async def received_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+" + phone

    await api_client.upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        phone=phone,
    )
    await state.clear()

    await message.answer(
        f"✅ Отлично! Номер {phone} сохранён.\n\nДобро пожаловать в наш магазин!",
        reply_markup=main_menu_reply_kb(),
    )


@router.message(RegistrationFSM.waiting_phone)
async def registration_wrong_input(message: Message):
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "Пожалуйста, используйте кнопку «📱 Поделиться номером».",
        reply_markup=phone_kb,
    )


# ─── Обработчики текстовых кнопок нижней панели ──────────────────────────────

@router.message(F.text == "🛍 Каталог")
async def menu_catalog(message: Message):
    await _send_catalog(message)


@router.message(F.text == "🛒 Корзина")
async def menu_cart(message: Message, state: FSMContext):
    # Импортируем здесь чтобы избежать циклических импортов
    from handlers.cart import show_cart_message
    await show_cart_message(message, state)


@router.message(F.text == "📋 Мои заказы")
async def menu_my_orders(message: Message):
    from handlers.my_orders import show_my_orders_message
    await show_my_orders_message(message)


# ─── Callback: catalog (из inline-кнопок "◀️ К категориям" и т.п.) ───────────

@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    categories = await api_client.get_categories()
    if not categories:
        await _show_products_from_callback(callback, None)
        return

    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat["name"], callback_data=f"cat_{cat['id']}")
    kb.button(text="📋 Все товары", callback_data="cat_all")
    kb.adjust(1)

    try:
        await callback.message.edit_text("📂 Выберите категорию:", reply_markup=kb.as_markup())
    except Exception:
        await callback.message.answer("📂 Выберите категорию:", reply_markup=kb.as_markup())
    await callback.answer()


# ─── Внутренняя функция отображения каталога (для message и callback) ─────────

async def _send_catalog(message: Message):
    categories = await api_client.get_categories()
    if not categories:
        await _show_products_from_message(message, None)
        return

    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat["name"], callback_data=f"cat_{cat['id']}")
    kb.button(text="📋 Все товары", callback_data="cat_all")
    kb.adjust(1)
    await message.answer("📂 Выберите категорию:", reply_markup=kb.as_markup())


# ─── Категории и товары ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    cat_id_str = callback.data[4:]
    cat_id = None if cat_id_str == "all" else int(cat_id_str)
    await _show_products_from_callback(callback, cat_id)


async def _show_products_from_message(message: Message, cat_id: int | None):
    products = await api_client.get_products(cat_id)
    if not products:
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ К категориям", callback_data="catalog")
        await message.answer("📭 Товаров нет.", reply_markup=kb.as_markup())
        return
    await _send_product_card_message(message, products[0], products, 0, cat_id)


async def _show_products_from_callback(callback: CallbackQuery, cat_id: int | None):
    products = await api_client.get_products(cat_id)
    if not products:
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ К категориям", callback_data="catalog")
        try:
            await callback.message.edit_text("📭 Товаров нет.", reply_markup=kb.as_markup())
        except Exception:
            await callback.message.answer("📭 Товаров нет.", reply_markup=kb.as_markup())
        await callback.answer()
        return
    await _send_product_card_callback(callback, products[0], products, 0, cat_id)


def _product_kb(product: dict, products: list, index: int, cat_id):
    """Inline-клавиатура карточки товара (без кнопки Главная)."""
    total = len(products)
    pid = product["id"]

    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 В корзину", callback_data=f"add_to_cart_{pid}")

    if total > 1:
        nav = []
        if index > 0:
            nav.append(InlineKeyboardButton(
                text="◀️", callback_data=f"pcat_{cat_id or 'all'}_{index - 1}"))
        if index < total - 1:
            nav.append(InlineKeyboardButton(
                text="▶️", callback_data=f"pcat_{cat_id or 'all'}_{index + 1}"))
        if nav:
            kb.row(*nav)

    kb.button(text="◀️ К категориям", callback_data="catalog")
    kb.adjust(1)
    return kb.as_markup()


def _product_text(product: dict, index: int, total: int) -> str:
    text = f"<b>{product['name']}</b>\n"
    if product.get("description"):
        text += f"\n{product['description']}\n"
    price_line = f"💰 <b>{product['price']} ₽</b>"
    if product.get("unit"):
        price_line += f"  <i>{product['unit']}</i>"
    if product.get("weight"):
        price_line += f"  📦 {product['weight']}"
    text += f"\n{price_line}"
    if total > 1:
        text += f"\n\n<i>{index + 1} из {total}</i>"
    return text


async def _send_product_card_message(message: Message, product: dict,
                                     products: list, index: int, cat_id):
    text = _product_text(product, index, len(products))
    kb = _product_kb(product, products, index, cat_id)

    if product.get("photo_url"):
        try:
            await message.answer_photo(photo=product["photo_url"], caption=text,
                                       reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


async def _send_product_card_callback(callback: CallbackQuery, product: dict,
                                      products: list, index: int, cat_id):
    text = _product_text(product, index, len(products))
    kb = _product_kb(product, products, index, cat_id)

    if product.get("photo_url"):
        try:
            await callback.message.answer_photo(photo=product["photo_url"], caption=text,
                                                reply_markup=kb, parse_mode="HTML")
            await callback.message.delete()
            await callback.answer()
            return
        except Exception:
            pass
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("pcat_"))
async def paginate_products(callback: CallbackQuery):
    parts = callback.data.split("_", 2)
    cat_id_str = parts[1]
    index = int(parts[2])
    cat_id = None if cat_id_str == "all" else int(cat_id_str)
    products = await api_client.get_products(cat_id)
    if not products or index >= len(products):
        await callback.answer("Товар не найден")
        return
    await _send_product_card_callback(callback, products[index], products, index, cat_id)


@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data[8:])
    product = await api_client.get_product(product_id)
    price_line = f"💰 <b>{product['price']} ₽</b>"
    if product.get("unit"):
        price_line += f"  <i>{product['unit']}</i>"
    if product.get("weight"):
        price_line += f"  📦 {product['weight']}"
    text = f"<b>{product['name']}</b>\n\n{product.get('description') or ''}\n\n{price_line}"
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 В корзину", callback_data=f"add_to_cart_{product_id}")
    kb.button(text="◀️ Каталог", callback_data="catalog")
    kb.adjust(1)
    if product.get("photo_url"):
        try:
            await callback.message.answer_photo(photo=product["photo_url"], caption=text,
                                                reply_markup=kb.as_markup(), parse_mode="HTML")
            await callback.message.delete()
            await callback.answer()
            return
        except Exception:
            pass
    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()
