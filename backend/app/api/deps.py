from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.models.admin import Admin, AdminRole
from app.core.config import settings
from jose import JWTError

async def get_current_admin(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        admin_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin

async def require_admin(admin: Admin = Depends(get_current_admin)) -> Admin:
    if admin.role != AdminRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return admin

def verify_bot_secret(x_bot_secret: str = Header(...)):
    if x_bot_secret != settings.BOT_API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid bot secret")
