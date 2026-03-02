from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import api_client

router = Router()

class RegistrationFSM(StatesGroup):
    waiting_phone = State()

def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 Каталог", callback_data="catalog")
    kb.button(text="🛒 Корзина", callback_data="cart_view")
    kb.button(text="📋 Мои заказы", callback_data="my_orders")
    kb.adjust(2, 1)
    return kb.as_markup()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Регистрируем пользователя (без телефона пока)
    user = await api_client.upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )

    # Если телефон уже есть — сразу в меню
    if user.get("phone"):
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\nДобро пожаловать в наш магазин.",
            reply_markup=main_menu_kb(),
        )
        return

    # Первый вход — запрашиваем номер
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
    phone = message.contact.phone_number
    # Нормализуем: убираем лишние символы, добавляем +
    phone = phone.strip().replace(" ", "").replace("-", "")
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
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Выберите действие:", reply_markup=main_menu_kb())

@router.message(RegistrationFSM.waiting_phone)
async def registration_wrong_input(message: Message):
    """Если пользователь написал текст вместо кнопки."""
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "Пожалуйста, используйте кнопку «📱 Поделиться номером» для передачи контакта.",
        reply_markup=phone_kb,
    )

@router.callback_query(F.data == "home")
async def show_home(callback: CallbackQuery):
    try:
        await callback.message.edit_text("🏠 Главная", reply_markup=main_menu_kb())
    except Exception:
        await callback.message.answer("🏠 Главная", reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    categories = await api_client.get_categories()
    if not categories:
        await show_products_list(callback, None)
        return

    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat["name"], callback_data=f"cat_{cat['id']}")
    kb.button(text="📋 Все товары", callback_data="cat_all")
    kb.button(text="🏠 Главная", callback_data="home")
    kb.adjust(1)
    try:
        await callback.message.edit_text("📂 Выберите категорию:", reply_markup=kb.as_markup())
    except Exception:
        await callback.message.answer("📂 Выберите категорию:", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    cat_id_str = callback.data[4:]
    cat_id = None if cat_id_str == "all" else int(cat_id_str)
    await show_products_list(callback, cat_id)

async def show_products_list(callback: CallbackQuery, cat_id: int | None):
    products = await api_client.get_products(cat_id)
    if not products:
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад", callback_data="catalog")
        try:
            await callback.message.edit_text("📭 Товаров нет.", reply_markup=kb.as_markup())
        except Exception:
            await callback.message.answer("📭 Товаров нет.", reply_markup=kb.as_markup())
        await callback.answer()
        return
    await show_product_card(callback, products[0], products, 0, cat_id)

async def show_product_card(callback: CallbackQuery, product: dict, products: list, index: int, cat_id):
    total = len(products)
    pid = product["id"]

    text = f"<b>{product['name']}</b>\n"
    if product.get("description"):
        text += f"\n{product['description']}\n"
    text += f"\n💰 <b>{product['price']} ₽</b>"
    if total > 1:
        text += f"\n\n<i>{index + 1} из {total}</i>"

    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 В корзину", callback_data=f"add_to_cart_{pid}")
    if total > 1:
        nav = []
        if index > 0:
            nav.append(InlineKeyboardButton(text="◀️", callback_data=f"pcat_{cat_id or 'all'}_{index-1}"))
        if index < total - 1:
            nav.append(InlineKeyboardButton(text="▶️", callback_data=f"pcat_{cat_id or 'all'}_{index+1}"))
        if nav:
            kb.row(*nav)
    kb.button(text="◀️ К категориям", callback_data="catalog")
    kb.adjust(1)

    if product.get("photo_url"):
        try:
            await callback.message.answer_photo(
                photo=product["photo_url"], caption=text,
                reply_markup=kb.as_markup(), parse_mode="HTML",
            )
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
    await show_product_card(callback, products[index], products, index, cat_id)

@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data[8:])
    product = await api_client.get_product(product_id)
    text = f"<b>{product['name']}</b>\n\n{product.get('description') or ''}\n\n💰 <b>{product['price']} ₽</b>"
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
