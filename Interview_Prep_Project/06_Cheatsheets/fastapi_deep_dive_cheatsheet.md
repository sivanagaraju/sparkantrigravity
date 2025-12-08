# FastAPI Deep Dive Cheat Sheet

> **Lead/Staff Data Engineer Interview Prep**
> 
> 📓 Notebook: [08_dependency_injection_deep_dive.ipynb](file:///c:/Users/sivan/Learning/Code/sparkantrigravity/Interview_Prep_Project/12_FastAPI/08_dependency_injection_deep_dive.ipynb)

---

## 🔧 Dependency Injection Patterns

### Pattern Reference
```python
# 1. Function Dependency (Simple)
def get_config():
    return {"env": "prod"}

# 2. Generator Dependency (Lifecycle)
def get_db():
    db = connect()
    try:
        yield db      # → Endpoint uses this
    finally:
        db.close()    # → Cleanup after response

# 3. Class Dependency (Stateful)
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 10):
        self.skip = skip
        self.limit = limit

# 4. Nested Dependency (Chain)
def get_current_user(token = Depends(get_token)):
    return decode(token)
```

### Usage
```python
@app.get("/items")
async def get_items(
    config = Depends(get_config),        # Function
    db = Depends(get_db),                # Generator
    page: Pagination = Depends(),        # Class (auto-instantiate)
    user = Depends(get_current_user)     # Nested
):
    pass
```

---

## 🧪 Testing with DI

```python
# Override real dependency with mock
def mock_get_db():
    return "FakeDB"

app.dependency_overrides[get_db] = mock_get_db

# In tests
client = TestClient(app)
response = client.get("/items")

# Cleanup
app.dependency_overrides.clear()
```

---

## ⚡ Request Flow

```
Client → Uvicorn → Middleware → Router → Dependencies → Endpoint → Response → Client
                                 ↑
                           Cached per request!
```

---

## 📊 Pydantic Quick Reference

```python
from pydantic import BaseModel, Field, validator

class Pipeline(BaseModel):
    name: str = Field(..., min_length=1)           # Required
    schedule: str = Field(default="0 * * * *")     # Optional with default
    
    @validator("schedule")
    def validate_cron(cls, v):
        if not is_valid_cron(v):
            raise ValueError("Invalid cron")
        return v
    
    class Config:
        from_attributes = True  # For ORM objects
```

---

## 🔐 Auth Pattern

```python
def get_token(auth: str = Header(...)):
    return auth.split(" ")[1]

def get_user(token = Depends(get_token)):
    return decode_jwt(token)

def require_admin(user = Depends(get_user)):
    if user.role != "admin":
        raise HTTPException(403)
    return user

@app.delete("/resource")
async def delete(admin = Depends(require_admin)):
    pass
```

---

## 🎯 Interview Quick Hits

| Question | Answer |
|----------|--------|
| **Depends() caching** | Cached per request (same dep = same result) |
| **Generator cleanup** | `finally` runs after response sent |
| **Class vs Function dep** | Class = stateful + auto-param parsing |
| **BackgroundTasks vs Celery** | BG = in-process, Celery = distributed |
| **async def vs def** | Use `async` for I/O-bound, `def` for CPU-bound |

---

## 🏗️ Production Patterns

### Health Check + DB Dependency
```python
@app.get("/health")
async def health(db = Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        return {"status": "healthy"}
    except:
        raise HTTPException(503, "Unhealthy")
```

### Rate Limiting Dependency
```python
async def rate_limit(request: Request, redis = Depends(get_redis)):
    key = f"rate:{request.client.host}"
    count = await redis.incr(key)
    if count > 100:
        raise HTTPException(429, "Rate limited")
```

---

## 📁 Project Structure

```
app/
├── main.py              # FastAPI app instance
├── dependencies.py      # Shared dependencies
├── routers/
│   ├── pipelines.py     # /pipelines routes
│   └── jobs.py          # /jobs routes
├── models/
│   ├── db.py            # SQLAlchemy models
│   └── schemas.py       # Pydantic models
└── services/
    └── pipeline_service.py
```
