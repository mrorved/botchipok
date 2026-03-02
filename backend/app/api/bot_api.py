from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import verify_bot_secret
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order, OrderItem, STATUS_LABELS
from app.schemas.schemas import BotCreateUser, BotCreateOrder, UserOut, ProductOut
from app.services.notifier import notify_admin_new_order

router = APIRouter(prefix="/bot", tags=["bot"], dependencies=[Depends(verify_bot_secret)])


@router.post("/users/upsert", response_model=UserOut)
async def upsert_user(data: BotCreateUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == data.telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(**data.model_dump())
        db.add(user)
    else:
        user.username = data.username
        user.full_name = data.full_name
        if data.phone:
            user.phone = data.phone
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/users/{telegram_id}", response_model=UserOut)
async def get_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/products", response_model=list[ProductOut])
async def get_visible_products(
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_visible == True)
    )
    if category_id is not None:
        q = q.where(Product.category_id == category_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/categories")
async def get_visible_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.children))
        .where(Category.is_visible == True, Category.parent_id == None)
    )
    cats = result.scalars().all()
    return [{"id": c.id, "name": c.name, "parent_id": c.parent_id} for c in cats]


@router.post("/orders")
async def create_order(data: BotCreateOrder, db: AsyncSession = Depends(get_db)):
    # 1. Найти пользователя
    result = await db.execute(select(User).where(User.telegram_id == data.telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Call /bot/users/upsert first.")

    # 2. Создать заказ
    order = Order(user_id=user.id, comment=data.comment)
    db.add(order)
    await db.flush()  # получаем order.id

    # 3. Добавить позиции
    for item_data in data.items:
        prod_result = await db.execute(
            select(Product).where(Product.id == item_data.product_id)
        )
        product = prod_result.scalar_one_or_none()
        if not product:
            continue
        oi = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data.quantity,
            price_at_order=product.price,
        )
        db.add(oi)

    await db.commit()

    # 4. Уведомить администратора
    try:
        await notify_admin_new_order(order.id, user)
    except Exception:
        pass  # не ломаем заказ из-за уведомления

    # 5. Вернуть простой ответ без сложных relations
    return {
        "id": order.id,
        "status": order.status.value,
        "comment": order.comment,
        "user_id": user.id,
        "items": [
            {"product_id": i.product_id, "quantity": i.quantity}
            for i in (await db.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )).scalars().all()
        ]
    }


@router.get("/orders/{telegram_id}")
async def get_user_orders(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        return []

    orders_result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    orders = orders_result.scalars().all()

    return [
        {
            "id": o.id,
            "status": o.status.value,
            "status_label": STATUS_LABELS[o.status],
            "comment": o.comment,
            "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
            "items": [
                {
                    "name": i.product.name if i.product else f"Товар #{i.product_id}",
                    "quantity": i.quantity,
                    "price": i.price_at_order,
                }
                for i in o.items
            ],
            "total": sum(i.price_at_order * i.quantity for i in o.items),
        }
        for o in orders
    ]
