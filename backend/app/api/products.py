from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.product import Product
from app.models.category import Category
from app.schemas.schemas import ProductCreate, ProductUpdate, ProductOut
import io, csv
import openpyxl

router = APIRouter(prefix="/products", tags=["products"])

def _product_query():
    return select(Product).options(
        selectinload(Product.category).selectinload(Category.children),
        selectinload(Product.category).selectinload(Category.parent),
    )

@router.get("/", response_model=list[ProductOut])
async def get_products(
    category_id: int | None = None,
    visible_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = _product_query()
    if category_id is not None:
        q = q.where(Product.category_id == category_id)
    if visible_only:
        q = q.where(Product.is_visible == True)
    result = await db.execute(q)
    return result.scalars().all()

@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        _product_query().where(Product.id == product_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

@router.post("/", response_model=ProductOut)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    p = Product(**data.model_dump())
    db.add(p)
    await db.commit()
    result = await db.execute(_product_query().where(Product.id == p.id))
    return result.scalar_one()

@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    await db.commit()
    result = await db.execute(_product_query().where(Product.id == product_id))
    return result.scalar_one()

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(p)
    await db.commit()
    return {"ok": True}

@router.post("/import")
async def import_products(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    content = await file.read()
    products_data = []

    if file.filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        for row in reader:
            products_data.append(row)
    elif file.filename.endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            products_data.append(dict(zip(headers, row)))
    else:
        raise HTTPException(status_code=400, detail="Only CSV or XLSX supported")

    created = 0
    for row in products_data:
        if not row.get("name") or not row.get("price"):
            continue
        p = Product(
            name=str(row["name"]),
            description=str(row.get("description", "") or ""),
            price=float(row["price"]),
            photo_url=str(row.get("photo_url", "") or "") or None,
            is_visible=True,
        )
        db.add(p)
        created += 1
    await db.commit()
    return {"imported": created}
