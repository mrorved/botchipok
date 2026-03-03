from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.notify_admin import NotifyAdmin

router = APIRouter(prefix="/settings", tags=["settings"])


class NotifyAdminCreate(BaseModel):
    telegram_id: int
    label: Optional[str] = None


class NotifyAdminUpdate(BaseModel):
    label: Optional[str] = None
    is_active: bool = True


class NotifyAdminOut(BaseModel):
    id: int
    telegram_id: int
    label: Optional[str] = None
    is_active: bool
    model_config = {"from_attributes": True}


@router.get("/notify-admins", response_model=list[NotifyAdminOut])
async def get_notify_admins(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(NotifyAdmin).order_by(NotifyAdmin.id))
    return result.scalars().all()


@router.post("/notify-admins", response_model=NotifyAdminOut)
async def add_notify_admin(
    data: NotifyAdminCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    existing = await db.execute(
        select(NotifyAdmin).where(NotifyAdmin.telegram_id == data.telegram_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот Telegram ID уже добавлен")
    na = NotifyAdmin(telegram_id=data.telegram_id, label=data.label)
    db.add(na)
    await db.commit()
    await db.refresh(na)
    return na


@router.patch("/notify-admins/{item_id}", response_model=NotifyAdminOut)
async def update_notify_admin(
    item_id: int,
    data: NotifyAdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(NotifyAdmin).where(NotifyAdmin.id == item_id))
    na = result.scalar_one_or_none()
    if not na:
        raise HTTPException(status_code=404, detail="Не найден")
    na.label = data.label
    na.is_active = data.is_active
    await db.commit()
    await db.refresh(na)
    return na


@router.delete("/notify-admins/{item_id}")
async def delete_notify_admin(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(NotifyAdmin).where(NotifyAdmin.id == item_id))
    na = result.scalar_one_or_none()
    if not na:
        raise HTTPException(status_code=404, detail="Не найден")
    await db.delete(na)
    await db.commit()
    return {"ok": True}


@router.post("/notify-admins/test")
async def test_notify(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    from app.services.notifier import _send_telegram
    result = await db.execute(
        select(NotifyAdmin).where(NotifyAdmin.is_active == True)
    )
    admins = result.scalars().all()
    if not admins:
        raise HTTPException(status_code=400, detail="Список получателей пуст")

    sent = []
    for na in admins:
        await _send_telegram(na.telegram_id, "✅ Тест уведомлений ShopAdmin — всё работает!")
        sent.append(na.telegram_id)

    return {"ok": True, "sent_to": sent}
