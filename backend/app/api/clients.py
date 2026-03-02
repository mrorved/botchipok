from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.order import Order, OrderItem
from app.schemas.schemas import UserOut

router = APIRouter(prefix="/clients", tags=["clients"])

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
