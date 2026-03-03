# 🛍 ShopAdmin — Telegram Bot + Web Admin Panel

Полная система управления магазином с Telegram-ботом для клиентов и веб-панелью для администраторов.

## Стек

- **Backend** — FastAPI + SQLAlchemy (async) + SQLite / PostgreSQL
- **Frontend** — React + Vite + Tailwind CSS
- **Bot** — aiogram 3
- **Инфраструктура** — Docker Compose / Portainer

---

## Возможности

| Раздел | Функции |
|--------|---------|
| **Дашборд** | Аналитика за день / неделю / месяц, топ товары |
| **Заказы** | Просмотр, смена статуса, редактирование позиций, экспорт Excel/CSV, массовая рассылка клиентам с активными заказами |
| **Товары** | CRUD, единицы измерения, фасовка, импорт из Excel/CSV, скрытие |
| **Категории** | CRUD с иерархией, скрытие |
| **Клиенты** | История заказов, сумма покупок, личные сообщения |
| **Настройки** | Управление списком получателей уведомлений |

**Бот (клиентская часть):**
- Каталог с категориями и пагинацией
- Корзина, оформление заказа с комментарием
- Сбор номера телефона при первом запуске
- История заказов с детализацией
- Уведомления о каждом изменении статуса

**Уведомления администраторам:**
- Новый заказ (с именем и телефоном клиента)
- Любая смена статуса заказа
- Список получателей управляется из панели (раздел Настройки)

---

## Быстрый старт (локально, Windows)

### 1. Установить Docker Desktop

Скачать: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)

После установки убедитесь что Docker запущен (иконка в трее).

### 2. Создать Telegram-бота

1. Откройте Telegram, найдите **@BotFather**
2. Отправьте `/newbot`, придумайте имя и username
3. Скопируйте **токен** вида `1234567890:ABCdef...`

Свой Telegram ID узнайте у **@userinfobot**.

### 3. Настроить переменные окружения

Скопируйте `.env.example` в `.env`:

```bash
copy .env.example .env
```

Откройте `.env` и заполните:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
SECRET_KEY=придумайте_длинный_случайный_ключ_минимум_32_символа
BOT_API_SECRET=ещё_один_случайный_ключ

# Один администратор
ADMIN_TELEGRAM_ID=123456789

# Или несколько через запятую
ADMIN_TELEGRAM_IDS=123456789,987654321,555000111

API_BASE_URL=http://backend:8000
```

> Оба поля (`ADMIN_TELEGRAM_ID` и `ADMIN_TELEGRAM_IDS`) можно использовать одновременно — они объединяются.

### 4. Запустить

```bash
docker-compose up --build -d
```

Первый запуск занимает 3–5 минут.

### 5. Открыть панель

| Сервис | URL |
|--------|-----|
| Веб-панель | http://localhost:3000 |
| API Swagger | http://localhost:8000/docs |

**Логин по умолчанию:** `admin` / `admin123`

> ⚠️ Смените пароль после первого входа — через раздел API или напрямую в БД.

---

## Управление

```bash
# Остановить
docker-compose down

# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f bot

# Перезапустить без пересборки (например, после изменения .env)
docker-compose restart backend

# Пересобрать и перезапустить
docker-compose up --build -d
```

---

## Деплой в Portainer

### Подготовка сервера

На сервере должны быть установлены:
- Docker Engine
- Docker Compose plugin (`docker compose` v2)
- Portainer CE или BE

### Шаг 1 — Загрузить проект на сервер

Клонируйте репозиторий или загрузите архив:

```bash
git clone https://github.com/your/repo.git /opt/shopadmin
cd /opt/shopadmin
```

### Шаг 2 — Создать .env на сервере

```bash
cp .env.example .env
nano .env
```

Заполните все поля. Дополнительно для продакшена укажите внешний URL фронтенда если нужно (при наличии домена/реверс-прокси).

### Шаг 3 — Создать Stack в Portainer

1. Откройте Portainer → **Stacks** → **Add stack**
2. Выберите **Repository** (если проект в Git) или **Web editor** (вставить docker-compose.yml вручную)
3. Укажите имя стека, например `shopadmin`
4. В разделе **Environment variables** добавьте все переменные из `.env`:

```
BOT_TOKEN          = ваш_токен
SECRET_KEY         = ваш_ключ
BOT_API_SECRET     = ваш_ключ
ADMIN_TELEGRAM_ID  = ваш_id
ADMIN_TELEGRAM_IDS = id1,id2,id3   (опционально)
API_BASE_URL       = http://backend:8000
DATABASE_URL       = sqlite+aiosqlite:////app/data/shop.db
```

5. Нажмите **Deploy the stack**

### Шаг 4 — Настроить внешний доступ

Если у вас есть домен и реверс-прокси (Nginx Proxy Manager, Traefik):

- Фронтенд (порт `3000`) → `https://shop.yourdomain.com`
- Backend API (порт `8000`) → при необходимости прямого доступа к API

Пример конфига Nginx Proxy Manager:
- Domain: `shop.yourdomain.com`
- Forward Hostname: `shop_frontend` (имя контейнера)
- Forward Port: `80`
- Enable SSL (Let's Encrypt)

### Шаг 5 — Проверить работу

```bash
# На сервере
docker ps
docker logs shop_backend
```

В браузере откройте `https://shop.yourdomain.com` или `http://IP_сервера:3000`.

---

## Переход на PostgreSQL (рекомендуется для продакшена)

### 1. Обновить `docker-compose.yml`

Добавьте сервис БД и volume:

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      POSTGRES_PASSWORD: shoppassword
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    # ... остальные настройки ...
    depends_on:
      db:
        condition: service_healthy
    # убрать volume ./data

volumes:
  postgres_data:
```

### 2. Добавить `asyncpg` в `backend/requirements.txt`

```
asyncpg==0.29.0
```

### 3. Изменить `DATABASE_URL` в `.env`

```env
DATABASE_URL=postgresql+asyncpg://shop:shoppassword@db:5432/shop
```

### 4. Пересобрать

```bash
docker-compose up --build -d
```

---

## Структура проекта

```
shop_project/
├── backend/
│   ├── app/
│   │   ├── api/          # Роутеры: orders, products, categories, clients, settings...
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── schemas/      # Pydantic схемы
│   │   ├── services/     # notifier.py — Telegram уведомления
│   │   └── core/         # config, database, security
│   ├── Dockerfile
│   └── requirements.txt
├── bot/
│   ├── handlers/         # catalog, cart, order, my_orders
│   ├── main.py
│   ├── api_client.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        # Dashboard, Orders, Products, Categories, Clients, Settings
│   │   ├── components/   # Layout
│   │   ├── context/      # AuthContext
│   │   └── api/          # axios client
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Статусы заказов и переходы

```
На подтверждении → Подтверждён → Оплачен → Выдан
На подтверждении → С корректировкой → Оплачен → Выдан
Любой активный статус → Отменён
```

При каждой смене статуса:
- **Клиент** получает уведомление в бот
- **Все администраторы** из раздела Настройки получают уведомление

---

## Импорт товаров из Excel

Формат файла `.xlsx` / `.csv`:

| name | description | price | photo_url | Ед. изм | Вес |
|------|-------------|-------|-----------|---------|-----|
| Товар 1 | Описание | 100 | https://... | шт. | 500 г |

Поля `Ед. изм` и `Вес` (или `Объем`) — необязательные.

---

## Типичные проблемы

**Бот не отвечает**
```bash
docker logs shop_bot
# Проверьте BOT_TOKEN в .env
```

**Ошибка 401 в браузере**
- Очистите localStorage: F12 → Application → Local Storage → удалить `token`

**База данных не создаётся**
```bash
mkdir data
```

**Порт уже занят**
- Измените в `docker-compose.yml`: `"3001:80"` вместо `"3000:80"`

**В Portainer контейнер не запускается**
- Проверьте что все переменные окружения заполнены в разделе Environment variables стека
- Убедитесь что папка `./data` существует или используйте named volume

---

## Первичная настройка после запуска

1. Войдите в панель: `admin` / `admin123`
2. Перейдите в **Настройки** → добавьте Telegram ID всех администраторов
3. Нажмите **Тест** — убедитесь что уведомления доходят
4. Добавьте категории и товары
5. Отправьте `/start` боту — убедитесь что каталог работает

---

## Лицензия

MIT — используйте свободно.
