# Project Setup Reference

## New Projects

### FastAPI (recommended for new APIs)

```bash
# With uv (recommended — fast, modern)
uv init my-api
cd my-api
uv add fastapi "uvicorn[standard]" pydantic-settings

# With pip
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install fastapi "uvicorn[standard]" pydantic-settings
```

Minimal `main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="My API", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

Run:
```bash
uvicorn main:app --reload
# API docs at http://localhost:8000/docs
```

### Django + Django REST Framework

```bash
uv add django djangorestframework
# or: pip install django djangorestframework

django-admin startproject myproject .
python manage.py startapp api
```

`settings.py` additions:
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'api',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Flask (lightweight, minimal)

```bash
uv add flask flask-sqlalchemy flask-migrate python-dotenv
```

```python
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Common Dependencies

### Database
```bash
# PostgreSQL async (FastAPI)
uv add sqlalchemy asyncpg alembic

# PostgreSQL sync (Flask/Django)
uv add sqlalchemy psycopg2-binary alembic

# Django ORM — built-in, just add the adapter
uv add psycopg2-binary  # or psycopg[binary] for psycopg3
```

### Authentication
```bash
# FastAPI JWT
uv add python-jose[cryptography] passlib[bcrypt]

# Django
uv add djangorestframework-simplejwt

# OAuth (any framework)
uv add authlib httpx
```

### Validation & settings
```bash
uv add pydantic pydantic-settings pydantic[email]
```

### HTTP client (for calling other services)
```bash
uv add httpx  # async-native, preferred over requests for FastAPI
```

### Background tasks
```bash
uv add celery redis  # distributed task queue
uv add arq           # simpler async alternative to Celery
```

### Testing
```bash
uv add --dev pytest pytest-asyncio httpx anyio
# Django: pytest-django
uv add --dev pytest-django
```

### Linting & formatting
```bash
uv add --dev ruff mypy
```

---

## Project Layouts

### FastAPI — feature-based layout

```
my-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # Engine, session factory, get_db
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/             # Pydantic request/response models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routers/             # Route handlers (thin — delegate to services)
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── auth.py
│   ├── services/            # Business logic
│   │   └── user_service.py
│   ├── dependencies/        # Shared Depends() functions
│   │   └── auth.py
│   └── middleware/
│       └── logging.py
├── alembic/                 # DB migrations
├── tests/
│   ├── conftest.py
│   └── test_users.py
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

### Django — app-based layout

```
myproject/
├── myproject/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   └── products/
├── manage.py
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```

---

## Configuration

### `.env` file
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb
SECRET_KEY=change-me-in-production
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Pydantic Settings (`app/config.py`)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    allowed_hosts: list[str] = ["localhost"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Usage as FastAPI dependency:
```python
from fastapi import Depends
from app.config import Settings, get_settings

@router.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {"debug": settings.debug}
```

---

## Alembic Migrations

```bash
alembic init alembic
```

`alembic/env.py` — point at your models:
```python
from app.database import Base
from app.models import *  # import all models so Alembic sees them
target_metadata = Base.metadata
```

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add users table"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

---

## Dockerfile (FastAPI)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
