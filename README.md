# Learnable Core API

FastAPI API with MongoDB, Beanie, Motor, and fastapi-users authentication.

The app is organized by modules using Controller -> Service -> Repository:

- `app/modules/users/router.py` - HTTP controller
- `app/modules/users/service.py` - user business logic
- `app/modules/users/repository.py` - MongoDB/Beanie access
- `app/modules/auth/*` - fastapi-users manager, JWT backend, auth service, and auth routes

## Setup

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

Required environment variables:

- `MONGODB_URL`
- `DATABASE_NAME`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `ALGORITHM`

## Auth Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/jwt/login`
- `POST /api/v1/auth/jwt/refresh`
- `POST /api/v1/auth/jwt/logout`
- `POST /api/v1/auth/request-verify-token`
- `POST /api/v1/auth/verify`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`

## User Endpoints

- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/{username}`
- `GET /api/v1/admin/users`
