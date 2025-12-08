# FastAPI Cheatsheet - Quick Reference

## 🚀 Quick Start
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

# Run: uvicorn main:app --reload
```

---

## 📝 Path Operations
```python
@app.get("/items")        # Read
@app.post("/items")       # Create
@app.put("/items/{id}")   # Update/Replace
@app.patch("/items/{id}") # Partial Update
@app.delete("/items/{id}")# Delete
```

---

## 🔗 Parameters
```python
# Path Parameter (required)
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id}

# Query Parameter (optional)
@app.get("/search")
async def search(q: str = None, skip: int = 0, limit: int = 10):
    return {"q": q, "skip": skip, "limit": limit}

# With validation
from fastapi import Query, Path
item_id: int = Path(..., ge=1)
q: str = Query(..., min_length=1, max_length=50)
```

---

## 📦 Pydantic Models
```python
from pydantic import BaseModel, Field, validator

class Item(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    description: str = None
    
    @validator('name')
    def validate_name(cls, v):
        return v.title()
    
    class Config:
        from_attributes = True  # For ORM

# Request body
@app.post("/items")
async def create(item: Item):
    return item

# Response model
@app.get("/items/{id}", response_model=Item)
async def get_item(id: int):
    return Item(name="test", price=10)
```

---

## 🔌 Dependency Injection
```python
from fastapi import Depends

# Function dependency
def get_db():
    db = "connection"
    try:
        yield db
    finally:
        pass  # cleanup

# Class dependency
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 10):
        self.skip = skip
        self.limit = limit

@app.get("/items")
async def get_items(
    db = Depends(get_db),
    pagination: Pagination = Depends()
):
    return {"db": db, "skip": pagination.skip}
```

---

## 🔐 Authentication
```python
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create token
token = jwt.encode({"sub": "user"}, "secret", algorithm="HS256")

# Verify token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, "secret", algorithms=["HS256"])
    return payload["sub"]
```

---

## 🛡️ CORS
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Background Tasks
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Long running task
    pass

@app.post("/send")
async def send(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Hello")
    return {"status": "queued"}
```

---

## 🔄 Event Hooks
```python
@app.on_event("startup")
async def startup():
    # Connect DB, load models
    pass

@app.on_event("shutdown")
async def shutdown():
    # Close connections
    pass

# Modern (FastAPI 0.95+)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # startup
    yield
    # shutdown

app = FastAPI(lifespan=lifespan)
```

---

## 🧪 Testing
```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

# Mock dependency
def override_get_db():
    return "test_db"

app.dependency_overrides[get_db] = override_get_db
```

---

## 🌐 WebSocket
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

---

## 📡 Streaming
```python
from fastapi.responses import StreamingResponse

async def generate():
    for i in range(10):
        yield f"data: {i}\n\n"
        await asyncio.sleep(0.5)

@app.get("/stream")
async def stream():
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## ⚠️ Exception Handling
```python
from fastapi import HTTPException

@app.get("/items/{id}")
async def get_item(id: int):
    if id == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": id}

# Custom exception
class CustomError(Exception):
    pass

@app.exception_handler(CustomError)
async def custom_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": str(exc)})
```

---

## 🏗️ Project Structure
```
app/
├── main.py          # FastAPI app
├── dependencies.py  # Shared Depends
├── routers/
│   ├── items.py
│   └── users.py
├── models/          # SQLAlchemy
├── schemas/         # Pydantic
└── services/        # Business logic
```

---

## 📋 Common Commands
```bash
# Development
uvicorn main:app --reload

# Production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# With HTTPS
uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

---

## 💡 Quick Tips
| Pattern | Do | Don't |
|---------|-----|-------|
| Async | `async def` for I/O | Sync for CPU-bound |
| Validation | Pydantic models | Manual checks |
| Auth | Depends() | Global middleware |
| DB | async SQLAlchemy | Sync in async routes |
| Config | Pydantic Settings | Hardcoded values |
