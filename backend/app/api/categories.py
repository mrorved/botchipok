from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.category import Category
from app.schemas.schemas import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=list[CategoryOut])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.children))
        .where(Category.parent_id == None)
    )
    return result.scalars().all()

@router.get("/all", response_model=list[CategoryOut])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).options(selectinload(Category.children)))
    return result.scalars().all()

@router.post("/", response_model=CategoryOut)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    cat = Category(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat

@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in data.model_dump().items():
        setattr(cat, k, v)
    await db.commit()
    await db.refresh(cat)
    return cat

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
    await db.commit()
    return {"ok": True}
