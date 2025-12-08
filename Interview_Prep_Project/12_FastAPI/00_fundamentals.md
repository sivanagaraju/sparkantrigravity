# FastAPI Fundamentals - Concepts Explained

## 1. What is FastAPI?

**FastAPI** is a modern, high-performance Python web framework for building APIs. It's built on top of:
- **Starlette**: For web handling (routing, middleware, WebSockets)
- **Pydantic**: For data validation and serialization
- **Python type hints**: For automatic documentation and validation

### Why FastAPI for Data Engineering?

| Benefit | Description |
|---------|-------------|
| **Performance** | One of the fastest Python frameworks (on par with Node.js and Go) |
| **Automatic Docs** | Swagger/OpenAPI docs generated from code |
| **Type Safety** | Catches errors at development time |
| **Async Support** | Non-blocking I/O for high concurrency |
| **Easy Testing** | Built-in test client |

---

## 2. ASGI and Uvicorn

### What is ASGI?

**ASGI (Asynchronous Server Gateway Interface)** is a specification that defines how Python web applications communicate with web servers asynchronously.

```
WSGI (Old, Sync)           ASGI (New, Async)
─────────────────          ─────────────────
Request → Server           Request → Server
Server → App               Server → App (async)
App processes              App can handle other
(blocks)                   requests while waiting
App → Server               App → Server
Server → Response          Server → Response
```

### What is Uvicorn?

**Uvicorn** is an ASGI server implementation that runs your FastAPI application.

```
Browser → Request
            ↓
         Uvicorn (ASGI Server)
            ↓
         FastAPI (Application)
            ↓
         Your Code
            ↓
         Response
            ↓
         Browser
```

**Why Uvicorn?**
- Lightning fast (uses uvloop)
- Production-ready
- Supports HTTP/1.1 and WebSockets
- Hot reloading for development

### Running FastAPI

```bash
# Development (with auto-reload)
uvicorn app.main:app --reload

# Production (with multiple workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# What this means:
# app.main → file path (app/main.py)
# app → FastAPI instance variable name
# -w 4 → 4 worker processes
# -k uvicorn.workers.UvicornWorker → Use async workers
```

---

## 3. Pydantic Models

### What is Pydantic?

**Pydantic** is a data validation library that uses Python type hints to:
1. **Validate** incoming data (ensure correct types and constraints)
2. **Parse** data (convert strings to proper types)
3. **Serialize** data (convert Python objects to JSON)

### Why Use Pydantic?

```
WITHOUT PYDANTIC:                    WITH PYDANTIC:
─────────────────                    ──────────────
def create_user(data: dict):         class User(BaseModel):
    if 'name' not in data:               name: str
        raise Error                      email: EmailStr
    if not isinstance(data['name'],      age: int
        str):
        raise Error                  def create_user(user: User):
    if 'email' not in data:              # Already validated!
        raise Error                      return user
    # ... lots of manual checks
```

### Pydantic Concepts

#### BaseModel - The Foundation
```python
from pydantic import BaseModel

class User(BaseModel):
    name: str          # Required, must be string
    email: str         # Required, must be string
    age: int           # Required, must be integer
    
# Creating an instance
user = User(name="John", email="john@example.com", age=30)

# What happens:
# 1. Pydantic checks if all required fields are present
# 2. Pydantic converts/validates types ("30" → 30)
# 3. Pydantic raises ValidationError if invalid
```

#### Field - Adding Constraints
```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(
        ...,              # ... means required
        min_length=1,     # At least 1 character
        max_length=100,   # At most 100 characters
        description="Product name"
    )
    price: float = Field(
        ...,
        gt=0,             # Greater than 0
        description="Price in USD"
    )
    quantity: int = Field(
        default=0,        # Default value
        ge=0              # Greater than or equal to 0
    )
```

#### Optional Fields
```python
from typing import Optional

class User(BaseModel):
    name: str                      # Required
    email: str                     # Required
    nickname: Optional[str] = None # Optional, defaults to None
    age: int = 18                  # Optional, defaults to 18
```

#### Validator - Custom Validation
```python
from pydantic import BaseModel, validator

class User(BaseModel):
    email: str
    password: str
    
    @validator('email')
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()  # Also transform the value
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be 8+ characters')
        return v
```

#### Config - Model Settings
```python
class User(BaseModel):
    user_id: int
    user_name: str
    
    class Config:
        # Allow creating from ORM objects (SQLAlchemy)
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
        
        # Use field names even if they differ
        populate_by_name = True
        
        # Example JSON for docs
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "user_name": "john"
            }
        }
```

---

## 4. Dependency Injection

### What is Dependency Injection?

**Dependency Injection (DI)** is a design pattern where a function/class receives its dependencies (things it needs) from the outside, rather than creating them internally.

```
WITHOUT DI:                          WITH DI:
───────────                          ────────
def get_users():                     def get_users(db):  # db injected!
    db = connect_to_database()           return db.query("SELECT *")
    return db.query("SELECT *")
    
# Problem: Hard to test,            # Benefit: Easy to test,
# can't swap database                # can swap database
```

### Why Dependency Injection?

| Benefit | Without DI | With DI |
|---------|-----------|---------|
| **Testing** | Hard to mock | Easy to override |
| **Flexibility** | Hardcoded | Swappable |
| **Reusability** | Duplicate code | Share dependencies |
| **Separation** | Mixed concerns | Clean separation |

### FastAPI Depends()

FastAPI's `Depends()` is the mechanism for dependency injection:

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 1. DEFINE a dependency (a function that returns something)
def get_database():
    db = DatabaseConnection()
    try:
        yield db      # yield = cleanup after request
    finally:
        db.close()    # This runs after the request

# 2. USE the dependency with Depends()
@app.get("/users")
async def get_users(db = Depends(get_database)):
    # db is automatically injected!
    return db.query("SELECT * FROM users")
```

### Types of Dependencies

#### Function Dependencies
```python
def common_parameters(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/items")
async def get_items(params: dict = Depends(common_parameters)):
    return {"skip": params["skip"], "limit": params["limit"]}
```

#### Class Dependencies
```python
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 10):
        self.skip = skip
        self.limit = limit

@app.get("/users")
async def get_users(pagination: Pagination = Depends()):
    # pagination.skip and pagination.limit available
    return {"skip": pagination.skip}
```

#### Nested Dependencies
```python
def get_db():
    return "database_connection"

def get_current_user(db = Depends(get_db)):
    # This dependency depends on get_db!
    return {"user": "john", "db": db}

@app.get("/me")
async def get_me(user = Depends(get_current_user)):
    return user  # {"user": "john", "db": "database_connection"}
```

#### Generator Dependencies (with cleanup)
```python
def get_db():
    db = create_connection()
    try:
        yield db           # 1. Return db to endpoint
    finally:
        db.close()         # 2. Cleanup after request completes

@app.get("/users")
async def get_users(db = Depends(get_db)):
    return db.query("...")  # db is valid here
    # After this returns, finally block runs
```

---

## 5. Request and Response Flow

### How a Request is Processed

```
1. CLIENT sends HTTP request
        ↓
2. UVICORN (ASGI server) receives request
        ↓
3. MIDDLEWARE (if any) processes request
        ↓
4. ROUTER finds matching path operation
        ↓
5. DEPENDENCIES are resolved (Depends())
        ↓
6. REQUEST BODY validated (Pydantic)
        ↓
7. PATH/QUERY PARAMS validated
        ↓
8. ENDPOINT FUNCTION executes
        ↓
9. RESPONSE MODEL filters output (Pydantic)
        ↓
10. MIDDLEWARE (if any) processes response
        ↓
11. UVICORN sends HTTP response
        ↓
12. CLIENT receives response
```

### Path Parameters vs Query Parameters

```python
# PATH PARAMETERS: Part of the URL path
# Used for: Resource identification
@app.get("/users/{user_id}")  # /users/123
async def get_user(user_id: int):
    return {"user_id": user_id}

# QUERY PARAMETERS: After ? in URL
# Used for: Filtering, pagination, options
@app.get("/users")  # /users?skip=0&limit=10
async def get_users(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# COMBINED
@app.get("/users/{user_id}/orders")  # /users/123/orders?status=pending
async def get_user_orders(
    user_id: int,           # Path
    status: str = None      # Query
):
    return {"user_id": user_id, "status": status}
```

### Request Body

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

# Request body is automatically parsed from JSON
@app.post("/users")
async def create_user(user: UserCreate):  # user parsed from JSON body
    return {"created": user.name}

# Client sends:
# POST /users
# Content-Type: application/json
# {"name": "John", "email": "john@example.com"}
```

### Response Model

```python
class UserCreate(BaseModel):
    name: str
    email: str
    password: str  # Sensitive!

class UserResponse(BaseModel):
    name: str
    email: str
    # No password!

# response_model filters the output
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Even if user has password, response won't include it
    return user
```

---

## 6. Routers (Modular Structure)

### What are Routers?

**Routers** allow you to split your API into multiple files/modules. Think of them as "mini apps" that can be combined.

```
WITHOUT ROUTERS:                     WITH ROUTERS:
────────────────                     ─────────────
main.py (1000+ lines)               main.py (50 lines)
- all user endpoints                routers/
- all product endpoints               users.py (user endpoints)
- all order endpoints                 products.py (product endpoints)
- all auth endpoints                  orders.py (order endpoints)
                                      auth.py (auth endpoints)
```

### Creating Routers

```python
# routers/users.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/users",      # All routes start with /users
    tags=["users"],       # Group in docs
)

@router.get("/")
async def list_users():
    return []

@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}
```

```python
# main.py
from fastapi import FastAPI
from routers import users, products, orders

app = FastAPI()

app.include_router(users.router)
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
```

---

## 7. Background Tasks

### What are Background Tasks?

**Background Tasks** are operations that run after the response is sent to the client. Used for:
- Sending emails
- Processing uploads
- Logging
- Notifications

```
┌─────────────────────────────────────────────────┐
│              REQUEST TIMELINE                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  Request → Process → Response → Background Task │
│    1ms       10ms      sent       (runs async)  │
│                          ↑                       │
│                    Client done                   │
│                    waiting here                  │
└─────────────────────────────────────────────────┘
```

### Using Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(to: str, subject: str):
    # Slow operation - 5 seconds
    time.sleep(5)
    print(f"Email sent to {to}")

@app.post("/register")
async def register(
    email: str,
    background_tasks: BackgroundTasks
):
    # Create user (fast)
    user = create_user(email)
    
    # Schedule email (doesn't block response)
    background_tasks.add_task(send_email, email, "Welcome!")
    
    # Return immediately (email sends in background)
    return {"status": "registered"}
```

---

## 8. Event Lifecycle

### Startup and Shutdown

```python
# OLD WAY (still works)
@app.on_event("startup")
async def startup():
    # Runs when application starts
    # Use for: DB connections, loading ML models, etc.
    app.state.db = await connect_database()

@app.on_event("shutdown")
async def shutdown():
    # Runs when application stops
    # Use for: Closing connections, cleanup
    await app.state.db.close()

# NEW WAY (FastAPI 0.95+) - Recommended
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("Starting up...")
    app.state.db = await connect_database()
    
    yield  # Application runs here
    
    # SHUTDOWN
    print("Shutting down...")
    await app.state.db.close()

app = FastAPI(lifespan=lifespan)
```

---

## 9. Exception Handling

### Built-in HTTPException

```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = find_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
            headers={"X-Error": "User lookup failed"}
        )
    return user
```

### Custom Exceptions

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Define custom exception
class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id

# Register handler
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "UserNotFound",
            "message": f"User {exc.user_id} not found",
            "path": str(request.url)
        }
    )

# Use in endpoint
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if not user_exists(user_id):
        raise UserNotFoundError(user_id)
    return get_user_from_db(user_id)
```

---

## 10. Key Takeaways

| Concept | What It Does | When to Use |
|---------|--------------|-------------|
| **Pydantic** | Validates and parses data | Request/response bodies |
| **Depends()** | Injects dependencies | DB connections, auth, shared logic |
| **Path Params** | URL variables `/users/{id}` | Resource identification |
| **Query Params** | URL query `?skip=0` | Filtering, pagination |
| **Routers** | Split code into modules | Organize large APIs |
| **Background Tasks** | Run after response | Emails, notifications |
| **Lifespan** | Startup/shutdown hooks | DB connections, warmup |
| **Exception Handlers** | Custom error responses | Consistent error format |
