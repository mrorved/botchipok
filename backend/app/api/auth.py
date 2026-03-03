from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password
from app.models.admin import Admin
from app.schemas.schemas import AdminLogin, Token
from app.api.deps import get_current_admin
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=Token)
async def login(data: AdminLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.username == data.username))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(admin.id), "role": admin.role})
    return Token(access_token=token)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if not verify_password(data.old_password, admin.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Новый пароль должен быть минимум 6 символов")
    admin.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"ok": True}
