# FastAPI Architecture & Performance - Lead Engineer Guide

## 1. Architecture Patterns

### Why Architecture Matters

```
MONOLITH (Small App)              LAYERED (Medium App)                MICROSERVICES (Large)
──────────────────               ──────────────────                   ──────────────────
┌─────────────┐                  ┌─────────────┐                      ┌──────┐ ┌──────┐
│   Single    │                  │  API Layer  │                      │Svc A │ │Svc B │
│    File     │                  ├─────────────┤                      └───┬──┘ └──┬──┘
│             │                  │  Service    │                          │       │
│  100 lines  │                  ├─────────────┤                      ┌───▼───────▼──┐
│             │                  │  Repository │                      │   API GW     │
└─────────────┘                  ├─────────────┤                      └──────────────┘
                                 │  Database   │
                                 └─────────────┘
```

### Layer Responsibilities

| Layer | Purpose | Contains |
|-------|---------|----------|
| **API Layer** | HTTP handling | Routes, request parsing, validation |
| **Service Layer** | Business logic | Rules, calculations, orchestration |
| **Repository Layer** | Data access | Database queries, ORM |
| **Model Layer** | Data structure | SQLAlchemy models, relationships |
| **Schema Layer** | API contracts | Pydantic request/response models |

---

## 2. Modular App Structure

### Why Split Code?

```
❌ BAD: Single main.py (500+ lines)            ✅ GOOD: Modular structure
──────────────────────────────                  ────────────────────────────
- Hard to navigate                              - Easy to find code
- Merge conflicts                               - Parallel development
- Hard to test                                  - Unit testable
- Tight coupling                                - Loose coupling
```

### How to Split

#### Step 1: Create Routers

```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/")
async def list_users():
    return []

@router.post("/")
async def create_user(user: UserCreate):
    return {"created": user.name}
```

#### Step 2: Combine Routers

```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import users, products, orders

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
```

#### Step 3: Main App

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
```

---

## 3. Event Hooks (Startup/Shutdown)

### What are Event Hooks?

Event hooks let you run code when your application **starts** or **stops**. Use them for:
- **Startup**: Connect to database, load ML models, warm up caches
- **Shutdown**: Close connections, flush logs, cleanup resources

### Why They Matter

```
WITHOUT HOOKS:                           WITH HOOKS:
──────────────                           ───────────
First request creates DB connection     DB ready before first request
Slow first response                     Fast first response
Connection may leak on shutdown         Clean shutdown
```

### Old Way: @app.on_event

```python
from fastapi import FastAPI

app = FastAPI()

# Dictionary to store our connections
connections = {}

@app.on_event("startup")
async def startup_event():
    """Runs ONCE when application starts."""
    print("🚀 Application starting...")
    
    # Connect to database
    connections["db"] = await create_database_connection()
    
    # Load ML model
    connections["model"] = load_model("model.pkl")
    
    # Warm up cache
    await warm_up_cache()
    
    print("✅ Ready to serve requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Runs ONCE when application stops."""
    print("🛑 Application shutting down...")
    
    # Close database
    await connections["db"].close()
    
    # Flush any pending logs
    await flush_logs()
    
    print("👋 Cleanup complete")
```

### New Way: Lifespan (Recommended)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern way to handle startup/shutdown.
    Everything before 'yield' is startup.
    Everything after 'yield' is shutdown.
    """
    # ===== STARTUP =====
    print("🚀 Starting up...")
    
    # Store in app.state (accessible in endpoints)
    app.state.db = await create_database_pool()
    app.state.redis = await create_redis_connection()
    app.state.model = load_ml_model()
    
    print("✅ Ready!")
    
    yield  # Application runs here
    
    # ===== SHUTDOWN =====
    print("🛑 Shutting down...")
    
    await app.state.db.close()
    await app.state.redis.close()
    
    print("👋 Done!")

# Pass lifespan to FastAPI
app = FastAPI(lifespan=lifespan)

# Access in endpoints
@app.get("/predict")
async def predict(request: Request):
    model = request.app.state.model
    return model.predict(...)
```

---

## 4. Background Tasks

### What are Background Tasks?

Operations that run **after** the response is sent to the client. The client doesn't wait for them.

```
Timeline:
────────────────────────────────────────────────────────────────
Request    Process    Response     Background Task
  │          │          │              │
  │    100ms │    50ms  │              │  5 seconds
  │          │          │              │
  ▼──────────▼──────────▼              ▼
        Client receives               Runs independently
        response in 150ms             (client doesn't wait)
```

### When to Use Background Tasks

| Use Case | Why Background? |
|----------|-----------------|
| Send email | Email server is slow |
| Process file | Large file takes time |
| Update cache | Not critical for response |
| Send notification | External API latency |
| Write logs | Batch for efficiency |

### How to Use

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

# Define the background task function
def send_welcome_email(email: str, name: str):
    """This runs in the background after response."""
    import time
    time.sleep(5)  # Simulate slow email
    print(f"📧 Sent welcome email to {email}")

def log_user_creation(user_id: int):
    """Log to analytics system."""
    print(f"📊 Logged user {user_id} creation")

@app.post("/register")
async def register_user(
    email: str,
    name: str,
    background_tasks: BackgroundTasks  # Inject BackgroundTasks
):
    # Quick operations (sync with response)
    user = create_user(email, name)
    
    # Schedule background tasks (async after response)
    background_tasks.add_task(send_welcome_email, email, name)
    background_tasks.add_task(log_user_creation, user.id)
    
    # Return immediately (don't wait for tasks)
    return {"status": "registered", "user_id": user.id}
```

### Background Tasks vs Celery

| Aspect | BackgroundTasks | Celery |
|--------|-----------------|--------|
| **Runs in** | Same process | Separate worker |
| **Survives restart** | ❌ No | ✅ Yes |
| **Retry on failure** | ❌ No | ✅ Yes |
| **Distributed** | ❌ No | ✅ Yes |
| **Setup** | Zero | Redis/RabbitMQ |
| **Use when** | Quick, non-critical | Long, must complete |

---

## 5. Custom Middleware

### What is Middleware?

Middleware is code that runs for **every request** before/after your endpoint.

```
Request Flow with Middleware:
────────────────────────────────────────────────────────────
                    
  Request → Middleware 1 → Middleware 2 → Endpoint
                                              │
  Response ← Middleware 1 ← Middleware 2 ←────┘

Each middleware can:
  - Modify the request before it reaches endpoint
  - Modify the response before it reaches client
  - Short-circuit (return early without hitting endpoint)
```

### Common Middleware Use Cases

| Use Case | What It Does |
|----------|--------------|
| **Logging** | Log every request/response |
| **Timing** | Measure request duration |
| **Authentication** | Check auth header |
| **CORS** | Add CORS headers |
| **Rate Limiting** | Block excessive requests |
| **Request ID** | Add unique ID for tracing |

### Creating Custom Middleware

#### Method 1: Using @app.middleware

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to every response."""
    
    # BEFORE: Request comes in
    start_time = time.time()
    
    # PROCESS: Call the actual endpoint
    response = await call_next(request)
    
    # AFTER: Response going out
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

#### Method 2: Using BaseHTTPMiddleware Class

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request
import logging
import uuid

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log details of every request."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Log request
        logger.info(f"[{request_id}] {request.method} {request.url}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            logger.info(f"[{request_id}] Status: {response.status_code}")
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] Error: {str(e)}")
            raise

# Add to app
app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
```

#### Method 3: Pure ASGI Middleware

```python
class SimpleMiddleware:
    """Pure ASGI middleware (lowest level, most control)."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Modify request here
            print(f"Request: {scope['path']}")
        
        # Call next middleware/app
        await self.app(scope, receive, send)

app = FastAPI()
app.add_middleware(SimpleMiddleware)
```

---

## 6. Exception Handling

### Why Custom Exceptions?

```
DEFAULT BEHAVIOR:                       CUSTOM HANDLING:
─────────────────                       ────────────────
raise ValueError("Bad data")            raise ValidationError(field="email")
  ↓                                       ↓
500 Internal Server Error               400 Bad Request
{                                       {
  "detail": "Internal Server Error"       "error": "ValidationError",
}                                         "field": "email",
                                          "message": "Invalid email format"
                                        }
```

### Creating Custom Exceptions

```python
# app/core/exceptions.py

class AppException(Exception):
    """Base exception for our application."""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code

class NotFoundError(AppException):
    """Resource not found."""
    def __init__(self, resource: str, id: int):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND"
        )
        self.resource = resource
        self.id = id

class ValidationError(AppException):
    """Validation failed."""
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation failed for {field}: {message}",
            code="VALIDATION_ERROR"
        )
        self.field = field

class AuthenticationError(AppException):
    """Authentication failed."""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, code="AUTH_ERROR")
```

### Registering Exception Handlers

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException, NotFoundError, AuthenticationError

app = FastAPI()

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.code,
            "message": exc.message,
            "resource": exc.resource,
            "id": exc.id,
            "path": str(request.url)
        }
    )

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=401,
        content={
            "error": exc.code,
            "message": exc.message
        },
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle all other app exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.code,
            "message": exc.message
        }
    )

# Usage in endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = find_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)  # Returns proper 404 JSON
    return user
```

---

## 7. Async/Await (Performance)

### Why Async Matters

```
SYNC ENDPOINT:                          ASYNC ENDPOINT:
──────────────                          ───────────────
Request 1 → Wait for DB (100ms) → Done   Request 1 → Start DB call (async)
                                                   ↓
Request 2 → Wait (blocked)               Request 2 → Start DB call (async)
                                                   ↓
Request 3 → Wait (blocked)               Request 3 → Start DB call (async)
                                                   ↓
Total: 300ms (serial)                    All complete → 100ms (parallel)
```

### When to Use Async

| Situation | Use | Why |
|-----------|-----|-----|
| Database query | `async def` | Waiting for DB |
| HTTP call | `async def` | Waiting for network |
| File read | `async def` | Waiting for disk |
| CPU calculation | `def` | No waiting |
| Sync library | `def` | Can't await |

### Correct Async Patterns

```python
# ✅ CORRECT: Async for I/O operations
@app.get("/users")
async def get_users():
    # Async database query
    users = await db.fetch_all("SELECT * FROM users")
    return users

# ✅ CORRECT: Sync for CPU-bound or sync libraries
@app.get("/calculate")
def calculate():  # No async!
    # CPU-intensive work (runs in thread pool)
    result = heavy_computation()
    return {"result": result}

# ❌ WRONG: Blocking call in async function
@app.get("/bad")
async def bad_endpoint():
    import time
    time.sleep(5)  # BLOCKS THE ENTIRE EVENT LOOP!
    return {"message": "done"}

# ✅ CORRECT: Use async sleep
@app.get("/good")
async def good_endpoint():
    import asyncio
    await asyncio.sleep(5)  # Non-blocking
    return {"message": "done"}
```

---

## 8. Connection Pooling

### What is Connection Pooling?

Instead of creating a new database connection for each request, we reuse connections from a pool.

```
WITHOUT POOLING:                         WITH POOLING:
────────────────                         ────────────────
Request → Create Connection → Query      Request → Get from Pool → Query
Request → Create Connection → Query        ↓           ↓
Request → Create Connection → Query      Request → Get from Pool → Query
                                           ↓           ↓
Total: 3 connections created             Total: 3 connections reused
       30ms overhead each                       0ms overhead
```

### SQLAlchemy Async Pool

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import QueuePool

# Create engine with connection pool
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    poolclass=QueuePool,
    
    # Pool settings
    pool_size=5,           # Keep 5 connections ready
    max_overflow=10,       # Allow 10 more when busy
    pool_timeout=30,       # Wait 30s for connection
    pool_recycle=1800,     # Recycle after 30 minutes
    pool_pre_ping=True,    # Check connection health
    
    echo=False             # SQL logging
)

# Async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency
async def get_db():
    async with async_session() as session:
        yield session
```

---

## 9. Caching

### Why Cache?

```
WITHOUT CACHE:                           WITH CACHE:
──────────────                           ───────────
User 1 → Query DB (100ms) → Response     User 1 → Query DB → Cache → Response
User 2 → Query DB (100ms) → Response     User 2 → Cache hit (1ms) → Response
User 3 → Query DB (100ms) → Response     User 3 → Cache hit (1ms) → Response

Total DB calls: 3                        Total DB calls: 1
```

### Redis Caching

```python
import redis.asyncio as redis
import json
from functools import wraps

# Create Redis connection
redis_client = redis.from_url("redis://localhost:6379")

# Cache decorator
def cached(expire_seconds: int = 300):
    """Cache function result in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try to get from cache
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Call function if not cached
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.set(
                cache_key,
                json.dumps(result),
                ex=expire_seconds
            )
            
            return result
        return wrapper
    return decorator

# Usage
@app.get("/products/{product_id}")
@cached(expire_seconds=60)  # Cache for 1 minute
async def get_product(product_id: int):
    # This DB call only happens on cache miss
    product = await db.get_product(product_id)
    return product
```

### Simple In-Memory Cache

```python
from functools import lru_cache
import time

class TTLCache:
    """Simple time-based cache."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache = {}
    
    def get(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value):
        self.cache[key] = (value, time.time())

# Usage
cache = TTLCache(ttl_seconds=60)

@app.get("/config")
async def get_config():
    cached = cache.get("config")
    if cached:
        return cached
    
    config = await load_config_from_db()
    cache.set("config", config)
    return config
```

---

## 10. Rate Limiting

### Why Rate Limit?

| Without Rate Limiting | With Rate Limiting |
|-----------------------|-------------------|
| Bot scrapes 10,000 requests/second | Bot limited to 10/minute |
| Server overloaded | Server protected |
| Costs skyrocket | Costs controlled |
| Legitimate users blocked | Fair access |

### Simple Rate Limiter

```python
from fastapi import FastAPI, Request, HTTPException
from collections import defaultdict
import time

app = FastAPI()

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window
        
        # Remove old requests
        self.requests[key] = [
            t for t in self.requests[key] 
            if t > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Record new request
        self.requests[key].append(now)
        return True

# 10 requests per minute per IP
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get client IP
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
    
    return await call_next(request)
```

### Using slowapi Library

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/data")
@limiter.limit("5/minute")  # 5 requests per minute
async def get_data(request: Request):
    return {"data": "sensitive"}

@app.post("/api/expensive")
@limiter.limit("1/hour")  # 1 request per hour
async def expensive_operation(request: Request):
    return {"status": "done"}
```

---

## Summary Table

| Topic | What | When |
|-------|------|------|
| **Routers** | Split endpoints by feature | Apps with 5+ endpoints |
| **Event Hooks** | Startup/shutdown code | DB connections, models |
| **Background Tasks** | After-response work | Emails, notifications |
| **Middleware** | Cross-cutting concerns | Logging, auth, timing |
| **Exception Handlers** | Custom error responses | Consistent API errors |
| **Async/Await** | Non-blocking I/O | DB, HTTP, file ops |
| **Connection Pool** | Reuse DB connections | All database apps |
| **Caching** | Avoid repeated work | Repeated queries |
| **Rate Limiting** | Prevent abuse | Public APIs |
