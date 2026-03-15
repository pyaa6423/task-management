---
name: python-backend
description: Build Python backend applications, APIs, and services. Use this skill whenever the user wants to create or extend a Python backend — including REST API design, database integration, authentication, middleware, background tasks, and deployment configuration. Trigger on requests like "build a Python API", "create a FastAPI endpoint", "set up a Django app", "add authentication to my backend", "connect to a database with SQLAlchemy", "write a Flask route", or any server-side Python work.
---

# Python Backend Implementation

A skill for building Python backends — from project setup to production-ready APIs.

## First: Understand the Project

Before writing any code, read the existing codebase. Check for:

- **Framework**: FastAPI, Django, Flask, or other
- **Python version**: 3.11+ preferred
- **Package manager**: pip + `requirements.txt`, Poetry (`pyproject.toml`), or uv
- **ORM / database**: SQLAlchemy, Django ORM, Tortoise-ORM, raw psycopg2, etc.
- **Async style**: async/await or synchronous
- **Existing conventions**: module structure, naming style, error handling patterns

If starting from scratch, suggest **FastAPI** as the default for new APIs — it's fast, async-native, and generates OpenAPI docs automatically. For projects that need a full-featured admin panel or batteries-included setup, suggest **Django + Django REST Framework**.

Read `references/project-setup.md` for setup commands and project structure templates.

---

## Core Workflow

### 1. Understand the task

Ask or infer:
- What does this API/service need to do?
- What data does it store or retrieve?
- Who calls this — a frontend, another service, or external clients?
- Are there authentication or authorization requirements?
- Any performance or scaling concerns?

Don't ask more than necessary — make reasonable assumptions and note them.

### 2. Plan the structure

Before coding, think through:
- Which endpoints / routes are needed?
- What models / schemas are required?
- How does data flow (request → validation → business logic → DB → response)?
- Where does authentication fit in?

For anything beyond a single endpoint, briefly describe the plan before writing code.

### 3. Implement

Write clean, idiomatic Python. Key principles:

**API design**
- Follow REST conventions: nouns for resources, HTTP verbs for actions
- Return appropriate status codes (201 for created, 404 for not found, 422 for validation errors)
- Validate all inputs — never trust request data
- Return consistent response shapes

**FastAPI specifics**
- Use Pydantic models for request/response validation
- Annotate path, query, and body parameters with types — FastAPI handles the rest
- Use `Depends()` for dependency injection (DB sessions, current user, etc.)
- Prefer async route handlers when doing I/O

**Django/DRF specifics**
- Use serializers for validation and representation
- Keep business logic out of views — put it in model methods or service modules
- Use `get_object_or_404` rather than manual try/except for simple lookups

**General**
- Keep route handlers thin — extract logic into service functions or methods
- Never put secrets in code; use environment variables
- Validate at the boundary (API layer), trust internally

**Database**
- Read `references/database.md` for SQLAlchemy, Django ORM, and migration patterns
- Always use parameterized queries — never string-format SQL
- Close/release DB connections properly (use context managers or dependency injection)

### 4. Handle errors

Return meaningful errors to clients:

```python
# FastAPI
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="User not found")

# Custom exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

Log server-side errors (5xx) with enough context to debug. Don't expose stack traces to clients.

### 5. Verify

After implementing:
- Run the app and test the endpoints manually (`curl` or the auto-generated `/docs` in FastAPI)
- Run existing tests: `pytest` or `python manage.py test`
- Check for import errors and type issues: `mypy .` or `pyright`

---

## Common Patterns Quick Reference

### FastAPI endpoint with DB dependency
```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Pydantic request/response models
```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    model_config = ConfigDict(from_attributes=True)
```

### JWT auth dependency
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_jwt(token)  # raises if invalid
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### Environment config with Pydantic Settings
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

---

## Reference Files

Read these when you need detail on a specific area:

- **`references/project-setup.md`** — Setup commands for FastAPI, Django, dependencies, and project layout
- **`references/patterns.md`** — Auth, middleware, background tasks, testing, and service patterns
- **`references/database.md`** — SQLAlchemy (sync/async), Django ORM, migrations, and query patterns

---

## What Good Output Looks Like

- **Working**: the server starts and endpoints return correct responses
- **Typed**: function signatures have type annotations; Pydantic models validate inputs
- **Secure**: no hardcoded secrets, no SQL injection, inputs validated before use
- **Readable**: functions do one thing; names describe intent; no magic
- **Minimal**: only adds what was asked for; avoids premature abstraction
