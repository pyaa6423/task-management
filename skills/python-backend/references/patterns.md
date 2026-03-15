# Backend Patterns Reference

## Authentication

### JWT with FastAPI

```python
# app/dependencies/auth.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str, expires_delta: timedelta = timedelta(hours=1)) -> str:
    payload = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user
```

Login route:
```python
@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}
```

### Role-based access control

```python
def require_role(*roles: str):
    async def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return dependency

# Usage
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    ...
```

---

## Middleware

### FastAPI middleware

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # or ["*"] for development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response

# Request ID
import uuid
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### Rate limiting

```bash
uv add slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/auth/token")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

---

## Service Layer Pattern

Keep route handlers thin. Put business logic in service functions:

```python
# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import CreateUserRequest
from app.dependencies.auth import hash_password

async def create_user(db: AsyncSession, data: CreateUserRequest) -> User:
    # Check for existing user
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise ValueError(f"Email {data.email} is already registered")

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
```

Route handler delegates to service:
```python
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await user_service.create_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return user
```

---

## Background Tasks

### FastAPI built-in (lightweight, in-process)

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, name: str):
    # runs after response is sent
    await email_client.send(to=email, subject="Welcome!", body=f"Hi {name}")

@router.post("/users", status_code=201)
async def create_user(data: CreateUserRequest, background_tasks: BackgroundTasks, ...):
    user = await user_service.create_user(db, data)
    background_tasks.add_task(send_welcome_email, user.email, user.name)
    return user
```

Good for: sending emails, logging, cache invalidation after a response. Not for heavy or long-running work.

### Celery (distributed, for heavy tasks)

```python
# tasks.py
from celery import Celery

celery = Celery("myapp", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")

@celery.task
def process_report(report_id: int):
    ...

# Dispatch from FastAPI
process_report.delay(report_id)
```

### ARQ (async alternative to Celery)

```python
# tasks.py
async def send_email(ctx, *, to: str, subject: str):
    await email_client.send(to=to, subject=subject)

class WorkerSettings:
    functions = [send_email]
    redis_settings = RedisSettings()

# Dispatch
await arq_pool.enqueue_job("send_email", to="user@example.com", subject="Hi")
```

---

## Error Handling

### Global exception handlers (FastAPI)

```python
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

### Custom exceptions

```python
# app/exceptions.py
class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, resource: str, id: int):
        super().__init__(f"{resource} {id} not found", status_code=404)

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)
```

Register handler:
```python
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
```

---

## Testing

### FastAPI with pytest

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db(engine):
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

Test example:
```python
# tests/test_users.py
import pytest

@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post("/users", json={"email": "test@example.com", "name": "Test"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_create_duplicate_user(client):
    payload = {"email": "dupe@example.com", "name": "Dupe"}
    await client.post("/users", json=payload)
    response = await client.post("/users", json=payload)
    assert response.status_code == 409
```

`pytest.ini` or `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Django with pytest-django

```python
# conftest.py
import pytest

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client
```

```python
@pytest.mark.django_db
def test_list_users(authenticated_client):
    response = authenticated_client.get("/api/users/")
    assert response.status_code == 200
```

---

## Logging

```python
# app/logging.py
import logging
import sys

def setup_logging(debug: bool = False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

logger = logging.getLogger(__name__)
```

For structured logging (JSON, easier to query in production):
```bash
uv add structlog
```

```python
import structlog
logger = structlog.get_logger()
logger.info("user_created", user_id=user.id, email=user.email)
```

---

## Pagination

```python
# Offset-based (simple)
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

async def paginate(query, db: AsyncSession, page: int = 1, page_size: int = 20):
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    items = await db.scalars(query.offset((page - 1) * page_size).limit(page_size))
    return {
        "items": items.all(),
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size),
    }
```

```python
# Cursor-based (for large datasets / real-time data)
@router.get("/events")
async def list_events(cursor: int | None = None, limit: int = 20, db: AsyncSession = Depends(get_db)):
    query = select(Event).order_by(Event.id.desc()).limit(limit + 1)
    if cursor:
        query = query.where(Event.id < cursor)
    events = (await db.scalars(query)).all()
    next_cursor = events[-1].id if len(events) > limit else None
    return {"items": events[:limit], "next_cursor": next_cursor}
```
