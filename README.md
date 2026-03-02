# 🛍 ShopAdmin — Telegram Bot + Web Admin Panel

Полная система управления магазином:
- **Telegram-бот** для клиентов (каталог, корзина, заказы)
- **Веб-панель** для администраторов (товары, заказы, аналитика)

---

## 📋 Структура проекта

```
shop_project/
├── backend/          # FastAPI REST API
│   ├── app/
│   │   ├── api/      # Роутеры (orders, products, categories...)
│   │   ├── models/   # SQLAlchemy модели
│   │   ├── schemas/  # Pydantic схемы
│   │   ├── services/ # Notifier (Telegram уведомления)
│   │   └── core/     # DB, config, security
│   ├── Dockerfile
│   └── requirements.txt
├── bot/              # aiogram 3 Telegram-бот
│   ├── handlers/     # catalog, cart, order
│   ├── main.py
│   ├── api_client.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/    # Dashboard, Orders, Products, Categories, Clients
│   │   ├── components/
│   │   ├── context/  # AuthContext
│   │   └── api/      # axios client
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Быстрый старт (Windows + Docker Desktop)

### 1. Установка Docker Desktop

Скачайте и установите [Docker Desktop для Windows](https://www.docker.com/products/docker-desktop/).
После установки убедитесь, что Docker запущен (иконка в трее).

### 2. Создание Telegram-бота

1. Откройте Telegram, найдите **@BotFather**
2. Отправьте `/newbot`
3. Придумайте имя и username для бота
4. Скопируйте **токен** (вида `1234567890:ABC...`)

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
# Windows — в командной строке или File Explorer
copy .env.example .env
```

Откройте `.env` в блокноте и заполните:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ  # ваш токен от BotFather
ADMIN_TELEGRAM_ID=123456789                          # ваш Telegram ID (узнать у @userinfobot)
SECRET_KEY=придумайте_длинный_случайный_ключ
BOT_API_SECRET=другой_случайный_ключ
API_BASE_URL=http://backend:8000
```

### 4. Запуск

Откройте **PowerShell** или **CMD** в папке проекта:

```powershell
# Собрать и запустить все сервисы
docker-compose up --build

# Или в фоне (рекомендуется после первого запуска)
docker-compose up --build -d
```

Первый запуск займёт 3–5 минут (установка зависимостей).

### 5. Проверка

| Сервис | URL |
|--------|-----|
| Веб-админка | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

**Логин по умолчанию:** `admin` / `admin123`
*(Смените пароль после первого входа!)*

---

## 🛑 Управление

```powershell
# Остановить
docker-compose down

# Посмотреть логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f bot

# Перезапустить один сервис
docker-compose restart bot
```

---

## 📦 База данных

SQLite файл хранится в `./data/shop.db` на вашем компьютере.
При обновлении кода данные сохраняются.

---

## 🔄 Переход на PostgreSQL (для Portainer/продакшн)

1. В `docker-compose.yml` добавьте сервис:

```yaml
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      POSTGRES_PASSWORD: shoppassword
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

2. В `.env` измените:
```env
DATABASE_URL=postgresql+asyncpg://shop:shoppassword@db:5432/shop
```

3. В `backend/requirements.txt` добавьте:
```
asyncpg==0.29.0
```

---

## 📊 Возможности веб-панели

| Раздел | Функции |
|--------|---------|
| **Дашборд** | Аналитика за день/неделю/месяц, топ товары |
| **Заказы** | Просмотр, смена статуса, экспорт Excel/CSV |
| **Товары** | CRUD, импорт из Excel/CSV, скрытие |
| **Категории** | CRUD с иерархией, скрытие |
| **Клиенты** | История заказов, сумма покупок |

## 🤖 Команды бота

| Команда | Действие |
|---------|---------|
| `/start` | Главное меню |
| Каталог | Навигация по категориям и товарам |
| Корзина | Просмотр, изменение количества |
| Оформить | Ввод комментария и создание заказа |

## 🔔 Уведомления

- Клиенту — при каждой смене статуса заказа
- Администратору — при создании нового заказа

## 📤 Статусы заказов и переходы

```
На подтверждении → Подтверждён / С корректировкой
Подтверждён → С корректировкой / Оплачен
С корректировкой → Оплачен
Оплачен → Выдан
```

---

## 🐳 Portainer (деплой в Docker Swarm/Compose)

1. Загрузите папку проекта на сервер
2. В Portainer → Stacks → Add stack
3. Вставьте содержимое `docker-compose.yml`
4. Добавьте переменные окружения в разделе **Environment variables**
5. Deploy

**Важно для Portainer:** замените `localhost` на внешний IP/домен сервера в настройках фронтенда.

---

## 🐛 Типичные проблемы

**Бот не отвечает**
- Проверьте правильность `BOT_TOKEN` в `.env`
- Убедитесь что `bot` контейнер запущен: `docker-compose ps`

**Ошибка 401 в браузере**
- Очистите localStorage браузера и войдите заново

**База данных не создаётся**
- Создайте папку `data/` вручную: `mkdir data`

**Порт занят**
- Измените порты в `docker-compose.yml` (например `"3001:80"`)
