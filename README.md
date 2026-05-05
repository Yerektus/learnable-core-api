# Learnable Core API

Core API для Learnable: сервис авторизации и профилей пользователей на FastAPI.

Стек:

- FastAPI
- MongoDB
- Beanie
- Motor
- fastapi-users
- JWT access/refresh tokens
- Pydantic Settings
- uv

## Возможности

- Регистрация пользователей.
- Вход по email или username.
- JWT access token и refresh token.
- Обновление access token через refresh token.
- Получение и обновление текущего профиля.
- Публичный профиль пользователя по username.
- Админский список пользователей.
- Email verification и password reset роуты от `fastapi-users`.
- Health check.

## Требования

- Python `3.13+`
- `uv`
- Docker и Docker Compose для локальной MongoDB

## Быстрый старт

Перейдите в папку API:

```bash
cd learnable-core-api
```

Скопируйте переменные окружения:

```bash
cp .env.example .env
```

Запустите MongoDB:

```bash
docker compose up -d
```

Установите зависимости:

```bash
uv sync
```

Запустите API:

```bash
uv run uvicorn app.main:app --reload
```

API будет доступен на:

- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Переменные окружения

Пример находится в `.env.example`.

| Переменная | Описание | Значение по умолчанию |
| --- | --- | --- |
| `MONGODB_URL` | URL подключения к MongoDB | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Имя базы данных | `learnable` |
| `SECRET_KEY` | Секрет для JWT, reset password и verify email токенов | обязательна |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access token в минутах | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh token в днях | `7` |
| `ALGORITHM` | JWT algorithm | `HS256` |

`SECRET_KEY` в локальной разработке можно оставить тестовым, но для staging/production нужно использовать длинное случайное значение.

## Запуск MongoDB

`docker-compose.yml` поднимает MongoDB 7:

```bash
docker compose up -d
```

Проверить статус:

```bash
docker compose ps
```

Остановить MongoDB:

```bash
docker compose down
```

Остановить и удалить локальные данные:

```bash
docker compose down -v
```

## Структура проекта

```text
learnable-core-api/
├── app/
│   ├── main.py                 # FastAPI app, middleware, routers, lifespan
│   ├── config.py               # Settings через pydantic-settings
│   ├── database.py             # MongoDB client и Beanie init
│   ├── exceptions.py           # Global exception handlers
│   └── modules/
│       ├── auth/
│       │   ├── router.py       # Auth endpoints
│       │   ├── service.py      # Login, refresh token, admin guard
│       │   ├── manager.py      # fastapi-users UserManager
│       │   ├── backend.py      # JWT backend
│       │   └── dependencies.py # Auth dependencies
│       └── users/
│           ├── router.py       # User and admin endpoints
│           ├── service.py      # User business logic
│           ├── repository.py   # Beanie access layer
│           ├── schemas.py      # Request/response schemas
│           └── models.py       # User document
├── docker-compose.yml
├── main.py                     # Local uvicorn entrypoint
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## API

### Health

| Method | Path | Auth | Описание |
| --- | --- | --- | --- |
| `GET` | `/health` | нет | Проверка, что сервис поднят |

### Auth

| Method | Path | Auth | Описание |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | нет | Регистрация пользователя |
| `POST` | `/api/v1/auth/jwt/login` | нет | Вход и получение access/refresh token |
| `POST` | `/api/v1/auth/jwt/refresh` | нет | Обновление пары токенов |
| `POST` | `/api/v1/auth/jwt/logout` | нет | Logout endpoint, возвращает `204` |
| `POST` | `/api/v1/auth/request-verify-token` | bearer | Запрос токена верификации email |
| `POST` | `/api/v1/auth/verify` | нет | Верификация email |
| `POST` | `/api/v1/auth/forgot-password` | нет | Запрос reset password токена |
| `POST` | `/api/v1/auth/reset-password` | нет | Сброс пароля |

### Users

| Method | Path | Auth | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/users/me` | bearer | Текущий профиль |
| `PATCH` | `/api/v1/users/me` | bearer | Обновление текущего профиля |
| `GET` | `/api/v1/users/{username}` | нет | Публичный профиль пользователя |

### Admin

| Method | Path | Auth | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/admin/users` | bearer, `role=admin` | Список пользователей |

Query параметры:

- `skip`: смещение, минимум `0`, по умолчанию `0`
- `limit`: размер страницы, от `1` до `500`, по умолчанию `100`

## Модель пользователя

Ответы пользовательских эндпоинтов возвращают:

```json
{
  "id": "663000000000000000000000",
  "email": "user@example.com",
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-05-05T12:00:00.000Z"
}
```

Username:

- приводится к lowercase;
- должен быть длиной от `3` до `30` символов;
- может содержать латинские буквы, цифры и `_`;
- уникален в MongoDB.

Пароль при регистрации должен быть минимум `8` символов и не должен содержать email пользователя.

## Примеры запросов

### Регистрация

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "strong-password",
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login

`/api/v1/auth/jwt/login` принимает `application/x-www-form-urlencoded`.
В поле `username` можно передать email или username.

```bash
curl -X POST http://localhost:8000/api/v1/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=strong-password"
```

Ответ:

```json
{
  "access_token": "<access-token>",
  "refresh_token": "<refresh-token>",
  "token_type": "bearer"
}
```

### Refresh token

```bash
curl -X POST http://localhost:8000/api/v1/auth/jwt/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh-token>"
  }'
```

### Текущий профиль

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access-token>"
```

### Обновление профиля

```bash
curl -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_updated",
    "first_name": "John",
    "last_name": "Updated"
  }'
```

### Публичный профиль

```bash
curl http://localhost:8000/api/v1/users/john_updated
```

### Список пользователей для админа

```bash
curl "http://localhost:8000/api/v1/admin/users?skip=0&limit=100" \
  -H "Authorization: Bearer <admin-access-token>"
```

## Роли

У пользователя есть поле `role`:

- `user`
- `admin`

Админские эндпоинты используют bearer token активного пользователя и дополнительно проверяют `role == "admin"`.

## CORS

По умолчанию API принимает запросы с:

- `http://localhost:3000`
- `http://localhost:5173`

Значение задается в `app/config.py` через `cors_origins`.

## Разработка

Запуск через `uvicorn`:

```bash
uv run uvicorn app.main:app --reload
```

Запуск через entrypoint:

```bash
uv run python main.py
```

Проверка health endpoint:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok"
}
```

## Примечания

- Refresh tokens сейчас stateless: они подписываются `SECRET_KEY` и не хранятся в базе.
- Logout endpoint возвращает `204`, но не инвалидирует уже выпущенные JWT.
- Токены для email verification и password reset логируются в callback-методах `UserManager`; отправка email пока не подключена.
- В репозитории сейчас нет отдельного test suite.
