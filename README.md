# Funtech test task

Тестовое задание для Funtech, сервис управления заказами на FastAPI.

## Стек

- **FastAPI** - основной фреймворк
- **PostgreSQL** + SQLAlchemy (async)
- **Redis** - кеширование
- **Kafka** - очередь событий
- **Celery** - фоновые задачи
- **Alembic** - миграции
- **JWT** - аутентификация

Всё упаковано в Docker Compose.

## Запуск

Нужны Docker и Docker Compose. Клонируете репозиторий, копируете `.env.example` в `.env` и запускаете:

```bash
cp .env.example .env
docker compose up --build
```

После запуска приложение доступно на `http://localhost:8000`.

Миграции применяются автоматически при старте контейнера с приложением, так что дополнительно ничего делать не нужно.

## Что внутри

Реализовано всё из задания:

- Регистрация и авторизация по JWT (OAuth2 Password Flow)
- CRUD для заказов с проверкой прав доступа
- Кеширование заказов в Redis (TTL 5 минут)
- Отправка события в Kafka при создании заказа
- Celery worker для обработки фоновых задач
- Health check эндпоинт для мониторинга
- Rate limiting через slowapi
- CORS middleware

## API эндпоинты

**Регистрация и авторизация:**
- `POST /register/` — создать нового пользователя
- `POST /token/` — получить JWT токен (в Swagger UI кнопка "Authorize" работает)

**Заказы (требуют авторизации):**
- `POST /orders/` — создать заказ
- `GET /orders/{order_id}/` — получить заказ по ID
- `PATCH /orders/{order_id}/` — обновить статус заказа
- `GET /orders/user/{user_id}/` — список всех заказов пользователя

**Мониторинг:**
- `GET /health/` — проверка состояния PostgreSQL и Redis

Полная документация с примерами доступна в Swagger UI на `/docs`.

## Тесты

Запуск тестов:

```bash
uv sync --dev
uv run pytest tests/ -v
```

Тесты используют моки для БД, Redis и Kafka, поэтому не требуют поднятия инфраструктуры.