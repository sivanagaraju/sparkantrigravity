"""
============================================================
FASTAPI TRICKY QUESTIONS - Lead Engineer Interview
============================================================
Topic: Common Pitfalls, Gotchas, and Advanced Scenarios
============================================================
"""

# ============================================================
# Q1: Sync vs Async - When to Use Which?
# ============================================================
"""
QUESTION: Should all FastAPI endpoints be async?

ANSWER: NO! It depends on what the endpoint does.

RULE:
- async def: For I/O-bound operations (network, database, file)
- def: For CPU-bound operations or when using sync libraries

WHY?
- async def with blocking code BLOCKS the entire event loop
- FastAPI runs sync def in a thread pool automatically
"""

from fastapi import FastAPI
import time
import asyncio

app = FastAPI()

# ❌ WRONG: Blocking code in async function
@app.get("/wrong")
async def wrong_endpoint():
    time.sleep(5)  # BLOCKS ENTIRE EVENT LOOP!
    return {"message": "done"}

# ✅ CORRECT: Use sync def for blocking code
@app.get("/correct-sync")
def correct_sync():  # No async!
    time.sleep(5)  # Runs in thread pool
    return {"message": "done"}

# ✅ CORRECT: Use async sleep for async functions
@app.get("/correct-async")
async def correct_async():
    await asyncio.sleep(5)  # Non-blocking
    return {"message": "done"}

# ============================================================
# Q2: Dependency Injection Gotcha - Singleton vs Factory
# ============================================================
"""
QUESTION: Why is my database connection shared across requests?

GOTCHA: Dependencies without yield are singletons!
"""

class DatabaseConnection:
    def __init__(self):
        self.id = id(self)
        print(f"Created connection {self.id}")

# ❌ WRONG: Singleton - same connection for all requests
def get_db_wrong():
    return DatabaseConnection()  # Created once at startup!

# ✅ CORRECT: Factory - new connection per request
def get_db_correct():
    db = DatabaseConnection()
    try:
        yield db
    finally:
        print(f"Closing connection {db.id}")

# ============================================================
# Q3: Mutable Default Arguments in Pydantic
# ============================================================
"""
QUESTION: Why are default lists shared across instances?
"""

from pydantic import BaseModel, Field
from typing import List

# ❌ WRONG: Mutable default in Python
class ItemWrong(BaseModel):
    tags: List[str] = []  # SHARED across instances!

# ✅ CORRECT: Use Field with default_factory
class ItemCorrect(BaseModel):
    tags: List[str] = Field(default_factory=list)

# ============================================================
# Q4: Response Model Filtering
# ============================================================
"""
QUESTION: Why is my password field being returned?
"""

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    # No password field!

# ❌ WRONG: Returns all fields including password
@app.post("/users/wrong")
async def create_user_wrong(user: UserCreate):
    return user  # Password included!

# ✅ CORRECT: Use response_model to filter
@app.post("/users/correct", response_model=UserResponse)
async def create_user_correct(user: UserCreate):
    return user  # Password filtered out!

# ============================================================
# Q5: Dependency Override Scope
# ============================================================
"""
QUESTION: Why aren't my test overrides working?

GOTCHA: Overrides must be done before requests, not during!
"""

"""
# ❌ WRONG: Override inside test function after client created
client = TestClient(app)

def test_wrong():
    app.dependency_overrides[get_db] = mock_db  # Too late!
    response = client.get("/")

# ✅ CORRECT: Override before creating client
def test_correct():
    app.dependency_overrides[get_db] = mock_db
    with TestClient(app) as client:  # Client created after override
        response = client.get("/")
    app.dependency_overrides.clear()
"""

# ============================================================
# Q6: Path Parameter Order Matters!
# ============================================================
"""
QUESTION: Why does /users/me return 404?
"""

# ❌ WRONG: Order matters - /users/{id} matches first!
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}

@app.get("/users/me")  # Never reached! "me" tries to convert to int
async def get_current_user():
    return {"user": "me"}

# ✅ CORRECT: Put specific routes BEFORE dynamic ones
# @app.get("/users/me")      # First!
# @app.get("/users/{user_id}")  # Second

# ============================================================
# Q7: Background Task DB Connection
# ============================================================
"""
QUESTION: Why does my background task fail with DB error?
"""

# ❌ WRONG: Using request-scoped DB in background task
@app.post("/items/wrong")
async def create_item_wrong(
    background_tasks: BackgroundTasks,
    db = Depends(get_db)  # Connection closed after request!
):
    background_tasks.add_task(process_item, db)  # DB already closed!
    return {"status": "queued"}

# ✅ CORRECT: Create new connection in background task
def process_item_correct(item_id: int):
    db = create_new_connection()  # Own connection!
    try:
        # Process item
        pass
    finally:
        db.close()

@app.post("/items/correct")
async def create_item_correct(
    item_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_item_correct, item_id)
    return {"status": "queued"}

# ============================================================
# Q8: CORS Preflight Failure
# ============================================================
"""
QUESTION: Why does my CORS work for GET but not POST?

ANSWER: POST with Content-Type: application/json triggers preflight.
Preflight OPTIONS request must also be allowed!
"""

from fastapi.middleware.cors import CORSMiddleware

# ❌ WRONG: Missing methods
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],  # OPTIONS not included!
)
"""

# ✅ CORRECT: Include all needed methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Include OPTIONS!
    allow_headers=["*"],
)

# ============================================================
# Q9: Query Parameter Type Coercion
# ============================================================
"""
QUESTION: Why does ?active=false still return true?
"""

# ❌ WRONG: String "false" is truthy!
@app.get("/items/wrong")
async def get_items_wrong(active: str = "true"):
    if active:  # "false" is truthy string!
        return {"active": True}

# ✅ CORRECT: Use bool type (FastAPI converts correctly)
@app.get("/items/correct")
async def get_items_correct(active: bool = True):
    return {"active": active}  # ?active=false → False

# ============================================================
# Q10: Circular Import with Routers
# ============================================================
"""
QUESTION: ImportError when using routers?

GOTCHA: Importing app in router that app imports causes circular import.
"""

"""
# ❌ WRONG
# app/main.py
from app.routers import users  # Imports users.py

# app/routers/users.py
from app.main import app  # Circular!
router = APIRouter()

# ✅ CORRECT: Use APIRouter, include in main
# app/routers/users.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/users")
async def get_users():
    pass

# app/main.py
from fastapi import FastAPI
from app.routers import users

app = FastAPI()
app.include_router(users.router, prefix="/api")
"""

# ============================================================
# Q11: Validation vs Business Logic
# ============================================================
"""
QUESTION: Where should I validate business rules?

PYDANTIC: Data format validation (types, constraints)
ENDPOINT: Business logic validation (DB checks, permissions)
"""

from pydantic import validator

class Order(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)  # Format validation
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v > 100:
            raise ValueError("Max 100 items per order")  # Business rule in Pydantic (OK for simple rules)
        return v

@app.post("/orders")
async def create_order(order: Order, db = Depends(get_db)):
    # Complex business validation in endpoint
    product = await db.get_product(order.product_id)
    if not product:
        raise HTTPException(404, "Product not found")  # DB-dependent validation
    if product.stock < order.quantity:
        raise HTTPException(400, "Insufficient stock")  # Business rule
    return {"order": order}

# ============================================================
# Q12: OAuth2 Scopes Gotcha
# ============================================================
"""
QUESTION: Why can users with 'read' scope access 'write' endpoints?

GOTCHA: Scopes must be checked explicitly!
"""

from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi import Security

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"read": "Read", "write": "Write"}
)

# ❌ WRONG: Not checking scopes
async def get_user_wrong(token: str = Depends(oauth2_scheme)):
    # Decodes token but doesn't check scopes!
    return decode_token(token)

# ✅ CORRECT: Check scopes explicitly
async def get_user_correct(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
):
    token_data = decode_token(token)
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(403, f"Scope '{scope}' required")
    return token_data

@app.get("/write-data")
async def write_data(user = Security(get_user_correct, scopes=["write"])):
    return {"user": user}

# ============================================================
# Q13: Testing Async Endpoints
# ============================================================
"""
QUESTION: Why do my async tests fail?

GOTCHA: TestClient is sync, use httpx for async tests.
"""

"""
# ❌ WRONG: Using TestClient for async testing
from fastapi.testclient import TestClient

async def test_async():  # This won't work properly
    client = TestClient(app)
    response = client.get("/")  # Sync call!

# ✅ CORRECT: Use httpx AsyncClient
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_async():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/")  # Async call!
        assert response.status_code == 200
"""

# ============================================================
# Q14: File Upload Size Limit
# ============================================================
"""
QUESTION: Why do large file uploads fail silently?
"""

from fastapi import File, UploadFile

# ❌ No size check
@app.post("/upload/wrong")
async def upload_wrong(file: UploadFile = File(...)):
    contents = await file.read()  # Could OOM with large files!
    return {"size": len(contents)}

# ✅ Stream large files
@app.post("/upload/correct")
async def upload_correct(file: UploadFile = File(...)):
    # Check size if content-length header present
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(413, "File too large")
    
    # Stream to disk
    with open(f"/tmp/{file.filename}", "wb") as f:
        while chunk := await file.read(8192):  # Read in chunks
            f.write(chunk)
    return {"filename": file.filename}

# ============================================================
# Q15: Startup Event Order
# ============================================================
"""
QUESTION: Why is my dependency not available at startup?

GOTCHA: Dependencies are request-scoped, not available at startup!
"""

# ❌ WRONG: Can't use Depends in startup
"""
@app.on_event("startup")
async def startup(db = Depends(get_db)):  # ERROR!
    await db.init()
"""

# ✅ CORRECT: Create resources directly in startup
@app.on_event("startup")
async def startup():
    app.state.db = await create_database_connection()

# Access in dependency
def get_db_from_state():
    return app.state.db

# ============================================================
# INTERVIEW TIPS
# ============================================================
"""
1. ASYNC VS SYNC:
   - Know when to use each
   - Never use blocking I/O in async functions
   
2. DEPENDENCY INJECTION:
   - Understand scopes (singleton vs factory)
   - Know how to test with overrides
   
3. SECURITY:
   - OAuth2 flow (token URL, scopes)
   - JWT encoding/decoding
   - CORS configuration
   
4. TESTING:
   - TestClient for sync
   - httpx AsyncClient for async
   - Dependency overrides
   
5. PERFORMANCE:
   - Connection pooling
   - Caching strategies
   - Background tasks vs Celery
"""
