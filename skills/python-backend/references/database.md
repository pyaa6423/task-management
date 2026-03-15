# Database Reference

## SQLAlchemy (Async) — FastAPI

### Setup

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,  # logs SQL in debug mode
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

App lifespan (preferred over `@app.on_event`):
```python
# app/main.py
from contextlib import asynccontextmanager
from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # dev only; use Alembic in prod
    yield
    # shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### Defining models

```python
# app/models/user.py
from sqlalchemy import String, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    posts: Mapped[list["Post"]] = relationship(back_populates="author")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped[User] = relationship(back_populates="posts")
```

### Querying

```python
from sqlalchemy import select, update, delete, func, or_

# Get by primary key
user = await db.get(User, user_id)

# Single row
user = await db.scalar(select(User).where(User.email == email))

# Multiple rows
users = (await db.scalars(select(User).where(User.is_active == True))).all()

# With relationships (eager load to avoid N+1)
stmt = select(User).options(selectinload(User.posts)).where(User.id == user_id)
user = await db.scalar(stmt)

# Count
total = await db.scalar(select(func.count()).select_from(User))

# Filter with OR
stmt = select(User).where(or_(User.email == email, User.name == name))

# Order and paginate
stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)

# Exists check
exists = await db.scalar(select(User).where(User.email == email).exists().select())
```

### Insert / Update / Delete

```python
# Insert
user = User(email="test@example.com", name="Test")
db.add(user)
await db.commit()
await db.refresh(user)  # reload from DB (gets auto-generated id, timestamps)

# Bulk insert
db.add_all([User(...), User(...)])
await db.commit()

# Update via ORM
user.name = "New Name"
await db.commit()

# Update via query (more efficient for bulk)
await db.execute(
    update(User).where(User.id == user_id).values(name="New Name")
)
await db.commit()

# Delete
await db.delete(user)
await db.commit()

# Bulk delete
await db.execute(delete(User).where(User.is_active == False))
await db.commit()
```

### Transactions

```python
async with db.begin():
    db.add(order)
    db.add(payment)
    # commits on exit, rolls back on exception
```

---

## Django ORM

### Models

```python
# models.py
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return self.email

class Post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
```

### Querying

```python
# Get or 404
from django.shortcuts import get_object_or_404
user = get_object_or_404(User, pk=user_id)

# Filter
active_users = User.objects.filter(is_active=True).order_by("-created_at")

# Select related (avoid N+1 for FK)
posts = Post.objects.select_related("author").all()

# Prefetch related (avoid N+1 for M2M and reverse FK)
users = User.objects.prefetch_related("posts").all()

# Aggregation
from django.db.models import Count, Avg
User.objects.annotate(post_count=Count("posts")).filter(post_count__gt=5)

# Exists
User.objects.filter(email=email).exists()

# Update
User.objects.filter(pk=user_id).update(name="New Name")

# Bulk create
User.objects.bulk_create([User(email=e) for e in emails])
```

### Transactions

```python
from django.db import transaction

@transaction.atomic
def create_order(user, items):
    order = Order.objects.create(user=user)
    for item in items:
        OrderItem.objects.create(order=order, **item)
    return order

# Or as context manager
with transaction.atomic():
    ...
```

### Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py migrate myapp 0003  # migrate to specific version
```

---

## Alembic (SQLAlchemy migrations)

### Setup

```bash
alembic init alembic
```

`alembic/env.py`:
```python
from app.database import Base
from app.models import user, post  # import all model modules

target_metadata = Base.metadata

# For async engines:
from sqlalchemy.ext.asyncio import async_engine_from_config

def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
    )
    # ... (see alembic async docs for full setup)
```

`alembic.ini` — set `sqlalchemy.url`:
```ini
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/mydb
```

### Commands

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add users table"

# Apply all pending migrations
alembic upgrade head

# Roll back one
alembic downgrade -1

# Roll back to specific revision
alembic downgrade abc123

# Show current version
alembic current

# Show history
alembic history --verbose
```

### Manual migration example

```python
# alembic/versions/abc123_add_index.py
def upgrade():
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.add_column("posts", sa.Column("published_at", sa.DateTime(), nullable=True))

def downgrade():
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("posts", "published_at")
```

---

## Common Query Patterns

### Avoid N+1 queries

```python
# BAD — triggers a query per user
users = (await db.scalars(select(User))).all()
for user in users:
    posts = user.posts  # N additional queries!

# GOOD — single query with JOIN
from sqlalchemy.orm import selectinload, joinedload

# selectinload: two queries, better for collections
stmt = select(User).options(selectinload(User.posts))

# joinedload: one JOIN query, better for single FK relationships
stmt = select(Post).options(joinedload(Post.author))
```

### Upsert

```python
# PostgreSQL — INSERT ... ON CONFLICT DO UPDATE
from sqlalchemy.dialects.postgresql import insert

stmt = insert(User).values(email=email, name=name)
stmt = stmt.on_conflict_do_update(
    index_elements=["email"],
    set_={"name": stmt.excluded.name},
)
await db.execute(stmt)
await db.commit()
```

### Full-text search (PostgreSQL)

```python
from sqlalchemy import text

results = await db.scalars(
    select(Post).where(
        text("to_tsvector('english', title || ' ' || body) @@ plainto_tsquery('english', :query)")
    ).params(query=search_term)
)
```

### Connection pooling tips

- Default pool size (`pool_size=5`) is fine for most apps
- Increase `pool_size` and `max_overflow` under high load
- Set `pool_pre_ping=True` to avoid stale connections after DB restarts:
  ```python
  engine = create_async_engine(url, pool_pre_ping=True)
  ```
- Never hold a DB session open across network calls or long-running tasks
