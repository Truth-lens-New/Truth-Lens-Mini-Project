# Database Review Notes

This file is a focused walkthrough of the TruthLens database design and usage.

## 1) Database Stack and Connection

Sources:
- `docker-compose.yml`
- `backend/app/core/config.py`

```yaml
postgres:
  image: postgres:15-alpine
  container_name: truthlens_db
  ports:
    - "5432:5432"
```

```python
class Settings(BaseSettings):
    postgres_user: str = "truthlens"
    postgres_password: str = "truthlens_secret"
    postgres_db: str = "truthlens"
    database_url: str = "postgresql+asyncpg://truthlens:truthlens_secret@postgres:5432/truthlens"
```

What to say:
- Runtime DB is PostgreSQL 15 (containerized).
- Backend uses SQLAlchemy async engine with `asyncpg`.

## 2) SQLAlchemy Engine and Session Lifecycle

Source: `backend/app/core/database.py`

```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

```python
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

What to say:
- `get_db` is a FastAPI dependency, so every request gets a managed async session.
- `expire_on_commit=False` avoids auto-expiring objects after commit.

## 3) Schema Overview (Current Core Tables)

### `users`

Source: `backend/app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    checks = relationship("Check", back_populates="user")
```

### `checks`

Source: `backend/app/models/check.py`

```python
class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    input_text = Column(Text, nullable=True)
    input_url = Column(String(2048), nullable=True)
    claim = Column(Text, nullable=True)

    verdict = Column(String(100), nullable=False)
    confidence = Column(String(20), nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="checks")
```

Relationship summary:
- One `User` -> many `Check`
- Each `Check` belongs to exactly one `User` (`user_id` foreign key)

## 4) Table Initialization Strategy

Source: `backend/app/core/database.py`

```python
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

What to say:
- Current project bootstrap uses SQLAlchemy metadata `create_all` at startup.
- This is convenient for dev but should usually be paired with migrations for production evolution.

## 5) How DB Is Used in API Flows

### Auth flow (register/login/profile)

Source: `backend/app/api/auth/auth.py`

```python
result = await db.execute(select(User).where(User.email == request.email))
existing_user = result.scalar_one_or_none()

db.add(user)
await db.commit()
await db.refresh(user)
```

```python
count_result = await db.execute(
    select(func.count()).select_from(Check).where(Check.user_id == user_id)
)
```

### History read/delete flow

Source: `backend/app/api/v1/history.py`

```python
query = (
    select(Check)
    .where(Check.user_id == user_id)
    .order_by(Check.created_at.desc())
    .offset(skip)
    .limit(limit)
)
```

```python
stmt = delete(Check).where(Check.user_id == user_id)
await db.execute(stmt)
await db.commit()
```

### v3 investigation persistence

Source: `backend/app/api/v3/endpoints/analyze.py`

```python
db_check = Check(
    user_id=current_user["user_id"],
    input_text=input_text_val,
    input_url=input_url_val,
    claim=result.original_text,
    verdict=result.verdict.value,
    confidence=conf_label,
    explanation=result.evidence_summary,
    pipeline_version="3.0.0",
)
db.add(db_check)

await db.commit()
```

What to say:
- Extension and web app both persist to the same `checks` table.
- That shared table is why history can stay unified across clients.

## 6) 30-Second Review Pitch

- "We run PostgreSQL with SQLAlchemy async sessions and a simple `users` + `checks` relational schema."
- "Every API request gets a managed DB session via dependency injection (`get_db`)."
- "Auth, history, and claim investigations all converge on `checks`, making history consistent across web and extension."
