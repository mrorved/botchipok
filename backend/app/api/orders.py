from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.order import Order, OrderItem, OrderStatus, STATUS_TRANSITIONS, STATUS_LABELS
from app.models.product import Product
from app.schemas.schemas import OrderOut, OrderStatusUpdate, OrderItemUpdate
from app.services.notifier import notify_user_status_change, notify_user_order_cancelled
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

@router.get("/export/pending")
async def export_pending_orders(
    format: str = "xlsx",
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(_order_query().where(Order.status == OrderStatus.PENDING))
    orders = result.scalars().all()

    # Сводка: сколько каждого товара суммарно по всем заказам на подтверждении
    summary: dict[str, dict] = {}
    for o in orders:
        for item in o.items:
            name = item.product.name if item.product else f"Товар #{item.product_id}"
            if name not in summary:
                summary[name] = {"qty": 0, "price": item.price_at_order}
            summary[name]["qty"] += item.quantity

    rows = [
        {
            "Товар": name,
            "Количество": v["qty"],
            "Цена за шт.": v["price"],
            "Сумма": v["price"] * v["qty"],
        }
        for name, v in sorted(summary.items())
    ]

    # Добавляем детали по заказам отдельным блоком
    order_rows = []
    for o in orders:
        items_str = ", ".join(
            f"{item.product.name if item.product else item.product_id} x{item.quantity}"
            for item in o.items
        )
        order_rows.append({
            "ID": o.id,
            "Клиент": o.user.full_name or o.user.username or str(o.user.telegram_id),
            "Telegram": f"@{o.user.username}" if o.user.username else str(o.user.telegram_id),
            "Товары": items_str,
            "Комментарий": o.comment or "",
            "Дата": o.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    if format == "csv":
        output = io.StringIO()
        output.write("=== СВОДНЫЙ СПИСОК ТОВАРОВ ===\n")
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        output.write("\n=== ДЕТАЛИ ЗАКАЗОВ ===\n")
        if order_rows:
            writer2 = csv.DictWriter(output, fieldnames=order_rows[0].keys())
            writer2.writeheader()
            writer2.writerows(order_rows)
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=pending_orders.csv"})
    else:
        from openpyxl.styles import Font, PatternFill
        wb = openpyxl.Workbook()

        # Лист 1: Сводный список товаров
        ws1 = wb.active
        ws1.title = "Сводка товаров"
        if rows:
            for col, h in enumerate(rows[0].keys(), 1):
                cell = ws1.cell(row=1, column=col, value=h)
                cell.font = Font(bold=True)
            for row in rows:
                ws1.append(list(row.values()))
            # Итог
            total = sum(r["Сумма"] for r in rows)
            ws1.append(["ИТОГО:", sum(r["Количество"] for r in rows), "", total])
            last = ws1.max_row
            ws1.cell(row=last, column=1).font = Font(bold=True)
            ws1.cell(row=last, column=4).font = Font(bold=True)
        for col in ws1.columns:
            ws1.column_dimensions[col[0].column_letter].width = max(
                len(str(col[0].value or "")), 
                max((len(str(c.value or "")) for c in col), default=0)
            ) + 4

        # Лист 2: Детали заказов
        ws2 = wb.create_sheet("Заказы")
        if order_rows:
            for col, h in enumerate(order_rows[0].keys(), 1):
                cell = ws2.cell(row=1, column=col, value=h)
                cell.font = Font(bold=True)
            for row in order_rows:
                ws2.append(list(row.values()))
        for col in ws2.columns:
            ws2.column_dimensions[col[0].column_letter].width = min(
                max((len(str(c.value or "")) for c in col), default=10) + 4, 50
            )

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=pending_orders.xlsx"})

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
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
        raise HTTPException(status_code=400,
            detail=f"Нельзя перейти из '{order.status}' в '{data.status}'")

    order.status = data.status
    await db.commit()

    if data.status == OrderStatus.CANCELLED:
        await notify_user_order_cancelled(order.user.telegram_id, order.id)
    else:
        await notify_user_status_change(order.user.telegram_id, order.id, data.status)

    result2 = await db.execute(_order_query().where(Order.id == order_id))
    return result2.scalar_one()

@router.patch("/{order_id}/items/{item_id}", response_model=OrderOut)
async def update_order_item(
    order_id: int,
    item_id: int,
    data: OrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(OrderItem).where(OrderItem.id == item_id, OrderItem.order_id == order_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if data.quantity <= 0:
        await db.delete(item)
    else:
        item.quantity = data.quantity

    await db.commit()
    result2 = await db.execute(_order_query().where(Order.id == order_id))
    return result2.scalar_one()

@router.delete("/{order_id}/items/{item_id}", response_model=OrderOut)
async def delete_order_item(
    order_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(OrderItem).where(OrderItem.id == item_id, OrderItem.order_id == order_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()
    result2 = await db.execute(_order_query().where(Order.id == order_id))
    return result2.scalar_one()


@router.get("/{order_id}/export")
async def export_single_order(
    order_id: int,
    format: str = "xlsx",
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(_order_query().where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    rows = []
    for item in order.items:
        rows.append({
            "Товар": item.product.name if item.product else f"#{item.product_id}",
            "Количество": item.quantity,
            "Цена за шт.": item.price_at_order,
            "Сумма": item.price_at_order * item.quantity,
        })
    # Итог
    total = sum(item.price_at_order * item.quantity for item in order.items)

    meta = {
        "Заказ №": order.id,
        "Клиент": order.user.full_name or order.user.username or str(order.user.telegram_id),
        "Telegram": f"@{order.user.username}" if order.user.username else str(order.user.telegram_id),
        "Статус": STATUS_LABELS[order.status],
        "Комментарий": order.comment or "",
        "Дата": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "Итого": f"{total:.0f} ₽",
    }

    if format == "csv":
        output = io.StringIO()
        # Мета-блок
        for k, v in meta.items():
            output.write(f"{k},{v}\n")
        output.write("\n")
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=order_{order_id}.csv"},
        )
    else:
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Заказ #{order_id}"

        # Мета-блок
        for i, (k, v) in enumerate(meta.items(), 1):
            ws.cell(row=i, column=1, value=k).font = Font(bold=True)
            ws.cell(row=i, column=2, value=str(v))

        ws.append([])

        # Таблица товаров
        if rows:
            header_row = len(meta) + 2
            headers = list(rows[0].keys())
            for col, h in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col, value=h)
                cell.font = Font(bold=True)
                cell.fill = PatternFill("solid", fgColor="1a1a2e")
            for row in rows:
                ws.append(list(row.values()))

            # Итог
            ws.append(["", "", "ИТОГО:", total])
            last = ws.max_row
            ws.cell(row=last, column=3).font = Font(bold=True)
            ws.cell(row=last, column=4).font = Font(bold=True)

        # Ширина столбцов
        for col in ws.columns:
            max_len = max((len(str(cell.value or '')) for cell in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=order_{order_id}.xlsx"},
        )
