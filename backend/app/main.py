from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api import auth, categories, products, orders, bot_api, clients, analytics
from app.core.config import settings
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.admin import Admin, AdminRole
from sqlalchemy import select, text

app = FastAPI(title="Shop Admin API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(bot_api.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

@app.on_event("startup")
async def startup():
    await init_db()

    async with AsyncSessionLocal() as db:
        # Миграции для существующих БД
        for sql in [
            "ALTER TABLE users ADD COLUMN phone VARCHAR(50)",
            "ALTER TABLE products ADD COLUMN unit VARCHAR(50)",
            "ALTER TABLE products ADD COLUMN weight VARCHAR(100)",
            "ALTER TABLE orders ADD COLUMN has_adjustments BOOLEAN DEFAULT 0",
            "ALTER TABLE orders ADD COLUMN removed_items_log TEXT",
        ]:
            try:
                await db.execute(text(sql))
                await db.commit()
            except Exception:
                pass  # колонка уже существует

        # Делаем product_id в order_items nullable (для удаления товаров без потери истории)
        # SQLite не поддерживает ALTER COLUMN, поэтому пересоздаём таблицу
        try:
            await db.execute(text("SELECT nullable FROM pragma_table_info('order_items') WHERE name='product_id'"))
            # Проверяем: если product_id уже nullable — пропускаем
            result = await db.execute(text(
                "SELECT notnull FROM pragma_table_info('order_items') WHERE name='product_id'"
            ))
            row = result.fetchone()
            if row and row[0] == 1:  # notnull=1 значит NOT NULL — надо исправить
                await db.execute(text("PRAGMA foreign_keys=OFF"))
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS order_items_new (
                        id INTEGER PRIMARY KEY,
                        order_id INTEGER REFERENCES orders(id),
                        product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
                        quantity INTEGER DEFAULT 1,
                        price_at_order FLOAT
                    )
                """))
                await db.execute(text("INSERT INTO order_items_new SELECT * FROM order_items"))
                await db.execute(text("DROP TABLE order_items"))
                await db.execute(text("ALTER TABLE order_items_new RENAME TO order_items"))
                await db.execute(text("PRAGMA foreign_keys=ON"))
                await db.commit()
                print("✅ order_items.product_id migrated to nullable with SET NULL")
        except Exception as e:
            print(f"Migration order_items skip: {e}")
            pass

        # Создать дефолтного админа если нет
        result = await db.execute(select(Admin).where(Admin.username == "admin"))
        if not result.scalar_one_or_none():
            admin = Admin(
                username="admin",
                hashed_password=hash_password("admin123"),
                role=AdminRole.ADMIN,
            )
            db.add(admin)
            await db.commit()
            print("✅ Default admin created: admin / admin123")

@app.get("/health")
async def health():
    return {"status": "ok"}
