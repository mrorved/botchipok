from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.product import Product

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/")
async def get_analytics(
    period: str = Query("month", enum=["day", "week", "month"]),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    now = datetime.utcnow()
    if period == "day":
        since = now - timedelta(days=1)
    elif period == "week":
        since = now - timedelta(weeks=1)
    else:
        since = now - timedelta(days=30)

    orders_count = await db.execute(
        select(func.count(Order.id)).where(Order.created_at >= since)
    )
    new_users = await db.execute(
        select(func.count(User.id)).where(User.created_at >= since)
    )

    top_products_result = await db.execute(
        select(Product.name, func.sum(OrderItem.quantity).label("total"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.created_at >= since)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
    )

    top_products = [{"name": row[0], "quantity": row[1]} for row in top_products_result.all()]

    return {
        "period": period,
        "orders_count": orders_count.scalar(),
        "new_users": new_users.scalar(),
        "top_products": top_products,
    }
