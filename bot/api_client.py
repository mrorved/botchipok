import httpx
from config import settings

HEADERS = {"x-bot-secret": settings.BOT_API_SECRET}
BASE = settings.API_BASE_URL

async def upsert_user(telegram_id: int, username: str | None, full_name: str | None, phone: str | None = None):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE}/api/bot/users/upsert",
            json={"telegram_id": telegram_id, "username": username, "full_name": full_name, "phone": phone},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()

async def get_user(telegram_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/bot/users/{telegram_id}", headers=HEADERS)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

async def get_categories():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/bot/categories", headers=HEADERS)
        r.raise_for_status()
        return r.json()

async def get_products(category_id: int | None = None):
    params = {}
    if category_id is not None:
        params["category_id"] = category_id
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/bot/products", params=params, headers=HEADERS)
        r.raise_for_status()
        return r.json()

async def get_product(product_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/products/{product_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()

async def create_order(telegram_id: int, comment: str | None, items: list[dict]):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE}/api/bot/orders",
            json={"telegram_id": telegram_id, "comment": comment, "items": items},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()

async def get_my_orders(telegram_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/bot/orders/{telegram_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()
