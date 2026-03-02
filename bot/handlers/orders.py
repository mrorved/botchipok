from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.order import Order, OrderItem, OrderStatus, STATUS_TRANSITIONS, STATUS_LABELS
from app.schemas.schemas import OrderOut, OrderStatusUpdate
from app.services.notifier import notify_user_status_change
import io, csv
import openpyxl

router = APIRouter(prefix="/orders", tags=["orders"])

def _order_query():
    return (
        select(Order)
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .order_by(Order.created_at.desc())
    )

@router.get("/", response_model=list[OrderOut])
async def get_orders(
    status: OrderStatus | None = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    q = _order_query()
    if status:
        q = q.where(Order.status == status)
    result = await db.execute(q)
    return result.scalars().all()

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(_order_query().where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(_order_query().where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed = STATUS_TRANSITIONS.get(order.status, [])
    if data.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя перейти из '{order.status}' в '{data.status}'. Допустимо: {[s.value for s in allowed]}"
        )

    order.status = data.status
    await db.commit()
    await notify_user_status_change(order.user.telegram_id, order.id, data.status)

    result2 = await db.execute(_order_query().where(Order.id == order_id))
    return result2.scalar_one()

@router.get("/export/pending")
async def export_pending_orders(
    format: str = "xlsx",
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(
        _order_query().where(Order.status == OrderStatus.PENDING)
    )
    orders = result.scalars().all()

    rows = []
    for o in orders:
        items_str = ", ".join(
            f"{item.product.name if item.product else item.product_id} x{item.quantity}"
            for item in o.items
        )
        rows.append({
            "ID": o.id,
            "Клиент": o.user.full_name or o.user.username or str(o.user.telegram_id),
            "Telegram": f"@{o.user.username}" if o.user.username else str(o.user.telegram_id),
            "Товары": items_str,
            "Комментарий": o.comment or "",
            "Статус": STATUS_LABELS[o.status],
            "Дата": o.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    if format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=orders.csv"},
        )
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заказы"
        if rows:
            ws.append(list(rows[0].keys()))
            for row in rows:
                ws.append(list(row.values()))
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=orders.xlsx"},
        )
