# FastAPI Production-Ready Project Structure

## Complete Project Layout

```
my_fastapi_project/
│
├── app/                           # Main application package
│   ├── __init__.py
│   ├── main.py                    # FastAPI application instance
│   ├── config.py                  # Configuration settings
│   ├── dependencies.py            # Shared dependencies
│   │
│   ├── api/                       # API layer (routers)
│   │   ├── __init__.py
│   │   ├── v1/                    # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Main v1 router
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py       # User endpoints
│   │   │   │   ├── pipelines.py   # Pipeline endpoints
│   │   │   │   └── auth.py        # Auth endpoints
│   │   │   └── dependencies.py    # v1-specific dependencies
│   │   └── v2/                    # API version 2 (future)
│   │
│   ├── core/                      # Core application logic
│   │   ├── __init__.py
│   │   ├── security.py            # JWT, hashing, auth
│   │   ├── config.py              # Settings with Pydantic
│   │   └── exceptions.py          # Custom exceptions
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                # Base model class
│   │   ├── user.py                # User model
│   │   └── pipeline.py            # Pipeline model
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py                # User request/response schemas
│   │   ├── pipeline.py            # Pipeline schemas
│   │   └── token.py               # Auth token schemas
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py        # User business logic
│   │   └── pipeline_service.py    # Pipeline business logic
│   │
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                # Base repository
│   │   ├── user_repository.py     # User data access
│   │   └── pipeline_repository.py # Pipeline data access
│   │
│   ├── db/                        # Database
│   │   ├── __init__.py
│   │   ├── session.py             # Async session factory
│   │   └── init_db.py             # Database initialization
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── logging.py             # Logging configuration
│       └── helpers.py             # Helper functions
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── unit/                      # Unit tests
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/               # Integration tests
│   │   ├── test_api.py
│   │   └── test_db.py
│   └── e2e/                       # End-to-end tests
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── scripts/                       # Utility scripts
│   ├── run_dev.sh
│   ├── run_tests.sh
│   └── seed_db.py
│
├── .env                           # Environment variables (not in git!)
├── .env.example                   # Example env file
├── .gitignore
├── docker-compose.yml             # Docker compose for local dev
├── Dockerfile                     # Production Dockerfile
├── pyproject.toml                 # Project metadata & dependencies
├── requirements.txt               # Pinned dependencies
├── requirements-dev.txt           # Dev dependencies
└── README.md
```

---

## Key Files Explained

### 1. `app/main.py` - Application Entry Point

```python
"""
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Starting up...")
    
    # Create database tables (in production, use Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory pattern."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()
```

---

### 2. `app/core/config.py` - Configuration with Pydantic

```python
"""
Application Settings using Pydantic BaseSettings
"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Project
    PROJECT_NAME: str = "Data Pipeline API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for managing data pipelines"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
```

---

### 3. `app/db/session.py` - Database Session

```python
"""
Async SQLAlchemy Database Session
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set True for SQL logging
    pool_pre_ping=True,
    # For serverless, use NullPool:
    # poolclass=NullPool
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """Dependency that yields database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

### 4. `app/models/user.py` - SQLAlchemy Model

```python
"""
User SQLAlchemy Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pipelines = relationship("Pipeline", back_populates="owner")
```

---

### 5. `app/schemas/user.py` - Pydantic Schemas

```python
"""
User Pydantic Schemas (Request/Response)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


# Properties for creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


# Properties for update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


# Properties stored in DB (internal)
class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return to client (no password!)
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
```

---

### 6. `app/services/user_service.py` - Business Logic

```python
"""
User Business Logic Service
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user_repository import UserRepository
from app.core.security import get_password_hash, verify_password


class UserService:
    """Business logic for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
    
    async def create_user(self, user_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        # Check if user exists
        existing = await self.repository.get_by_email(user_in.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(user_in.password)
        
        # Create user
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name
        )
        
        return await self.repository.create(user)
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = await self.repository.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.repository.get_by_id(user_id)
```

---

### 7. `app/api/v1/endpoints/users.py` - API Endpoints

```python
"""
User API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.api.v1.dependencies import get_current_user

router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency for user service."""
    return UserService(db)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    try:
        user = await service.create_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current authenticated user."""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Get user by ID."""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
```

---

### 8. `app/api/v1/router.py` - API Router Aggregator

```python
"""
API v1 Router - Combines all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import users, pipelines, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
```

---

### 9. `tests/conftest.py` - Test Fixtures

```python
"""
Pytest Fixtures for Testing
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.models.base import Base


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create clean database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()
```

---

### 10. `Dockerfile` - Production Container

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY ./app ./app

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Run with Gunicorn + Uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

---

### 11. `docker-compose.yml` - Local Development

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app  # Hot reload in dev
    command: uvicorn app.main:app --host 0.0.0.0 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER (Routers)                     │
│  - HTTP handling, request/response                          │
│  - Path/query parameter parsing                              │
│  - Dependency injection                                      │
│  - OpenAPI documentation                                     │
├─────────────────────────────────────────────────────────────┤
│                   SERVICE LAYER (Business Logic)             │
│  - Business rules and validation                             │
│  - Orchestration of operations                               │
│  - Transaction management                                    │
│  - Cross-cutting concerns                                    │
├─────────────────────────────────────────────────────────────┤
│                  REPOSITORY LAYER (Data Access)              │
│  - Database queries                                          │
│  - ORM interactions                                          │
│  - Data mapping                                              │
├─────────────────────────────────────────────────────────────┤
│                    MODEL LAYER (Database)                    │
│  - SQLAlchemy models                                         │
│  - Table definitions                                         │
│  - Relationships                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Production Considerations

| Aspect | Solution |
|--------|----------|
| **Config** | Pydantic Settings with .env |
| **Database** | Async SQLAlchemy + Alembic migrations |
| **Auth** | JWT tokens with refresh |
| **Logging** | Structured logging (loguru/structlog) |
| **Monitoring** | Prometheus metrics + OpenTelemetry |
| **Testing** | pytest + httpx AsyncClient |
| **CI/CD** | GitHub Actions/GitLab CI |
| **Deployment** | Docker + Kubernetes |
| **Secrets** | Environment variables / Vault |
