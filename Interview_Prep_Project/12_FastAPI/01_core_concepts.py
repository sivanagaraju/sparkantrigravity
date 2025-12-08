"""
============================================================
FASTAPI CORE CONCEPTS - Lead Engineer Interview
============================================================
Topic: ASGI, Path Operations, Pydantic, Dependency Injection
============================================================
"""

# ============================================================
# 1. ASGI AND UVICORN
# ============================================================
"""
ASGI (Asynchronous Server Gateway Interface):
- Python async web server specification
- Successor to WSGI (synchronous)
- Supports HTTP, WebSockets, background tasks

UVICORN:
- Lightning-fast ASGI server
- Based on uvloop (libuv) and httptools
- Production-ready with Gunicorn

RUN COMMANDS:
uvicorn main:app --reload                    # Development
uvicorn main:app --host 0.0.0.0 --port 8000  # Production
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4  # Multi-worker
"""

from fastapi import FastAPI, Depends, HTTPException, Query, Path, Body
from fastapi import BackgroundTasks, Request, Response
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum

app = FastAPI(
    title="Data Pipeline API",
    description="API for managing data pipelines",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
    openapi_url="/openapi.json"
)

# ============================================================
# 2. PATH OPERATIONS
# ============================================================

# Basic CRUD operations
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the API"}

@app.get("/pipelines")
async def list_pipelines():
    """GET - Retrieve resources."""
    return {"pipelines": ["etl_daily", "etl_hourly"]}

@app.post("/pipelines")
async def create_pipeline(name: str):
    """POST - Create resource."""
    return {"created": name}

@app.put("/pipelines/{pipeline_id}")
async def update_pipeline(pipeline_id: int, name: str):
    """PUT - Update/replace resource."""
    return {"updated": pipeline_id, "name": name}

@app.patch("/pipelines/{pipeline_id}")
async def partial_update_pipeline(pipeline_id: int, name: Optional[str] = None):
    """PATCH - Partial update."""
    return {"patched": pipeline_id}

@app.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: int):
    """DELETE - Remove resource."""
    return {"deleted": pipeline_id}

# ============================================================
# 3. PATH AND QUERY PARAMETERS
# ============================================================

# Path parameters (required, part of URL)
@app.get("/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: int = Path(..., title="Pipeline ID", ge=1)
):
    """Path parameter with validation."""
    return {"pipeline_id": pipeline_id}

# Query parameters (optional, after ?)
@app.get("/search")
async def search_pipelines(
    q: str = Query(..., min_length=1, max_length=50),  # Required
    skip: int = Query(0, ge=0),                        # Optional with default
    limit: int = Query(10, le=100),                    # Optional with max
    status: Optional[str] = None                       # Optional, can be None
):
    """Query parameters: /search?q=etl&skip=0&limit=10"""
    return {"query": q, "skip": skip, "limit": limit, "status": status}

# Enum for fixed choices
class PipelineStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"

@app.get("/pipelines/status/{status}")
async def get_by_status(status: PipelineStatus):
    """Enum path parameter - validates against choices."""
    return {"status": status, "value": status.value}

# ============================================================
# 4. PYDANTIC MODELS (Request/Response)
# ============================================================

class PipelineBase(BaseModel):
    """Base model with shared fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    schedule: str = Field(..., regex=r"^[0-9*/ ]+$")  # Cron pattern

class PipelineCreate(PipelineBase):
    """Request model for creating pipeline."""
    source: str
    destination: str
    
    @validator('source')
    def validate_source(cls, v):
        """Custom validation."""
        if not v.startswith(('s3://', 'gs://', 'abfss://')):
            raise ValueError('Source must be a cloud storage path')
        return v

class PipelineResponse(PipelineBase):
    """Response model with additional fields."""
    id: int
    status: PipelineStatus
    created_at: str
    
    class Config:
        # Allow ORM objects
        orm_mode = True

class PipelineUpdate(BaseModel):
    """Partial update model - all fields optional."""
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None

# Using models
@app.post("/pipelines/create", response_model=PipelineResponse)
async def create_pipeline_v2(pipeline: PipelineCreate):
    """Request body with Pydantic validation."""
    # pipeline is already validated
    return PipelineResponse(
        id=1,
        name=pipeline.name,
        description=pipeline.description,
        schedule=pipeline.schedule,
        status=PipelineStatus.STOPPED,
        created_at="2024-01-15T10:00:00Z"
    )

# ============================================================
# 5. DEPENDENCY INJECTION
# ============================================================

# Simple dependency
def get_db():
    """Database connection dependency."""
    db = "database_connection"  # Simulated
    try:
        yield db
    finally:
        pass  # Close connection

# Dependency with parameters
def get_query_params(
    skip: int = 0,
    limit: int = 10
) -> Dict[str, int]:
    """Common query params dependency."""
    return {"skip": skip, "limit": limit}

# Class-based dependency
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 10):
        self.skip = skip
        self.limit = limit

@app.get("/items")
async def get_items(
    db: str = Depends(get_db),
    pagination: Pagination = Depends()
):
    """Using multiple dependencies."""
    return {
        "db": db,
        "skip": pagination.skip,
        "limit": pagination.limit
    }

# Nested dependencies
def get_current_user(db: str = Depends(get_db)):
    """Dependency that uses another dependency."""
    return {"user_id": 1, "username": "admin", "db": db}

@app.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Endpoint using nested dependency."""
    return user

# ============================================================
# 6. REQUEST AND RESPONSE HANDLING
# ============================================================

# Multiple response models
@app.get(
    "/pipelines/{pipeline_id}/details",
    response_model=PipelineResponse,
    responses={
        404: {"description": "Pipeline not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_pipeline_details(pipeline_id: int):
    """Endpoint with multiple response types."""
    if pipeline_id == 0:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return PipelineResponse(
        id=pipeline_id,
        name="test",
        schedule="0 * * * *",
        status=PipelineStatus.RUNNING,
        created_at="2024-01-15T10:00:00Z"
    )

# Custom response
from fastapi.responses import JSONResponse, StreamingResponse

@app.get("/custom-response")
async def custom_response():
    """Return custom JSON response."""
    return JSONResponse(
        content={"message": "Custom response"},
        status_code=201,
        headers={"X-Custom-Header": "value"}
    )

# ============================================================
# 7. BACKGROUND TASKS
# ============================================================

def send_notification(email: str, message: str):
    """Background task function."""
    # Simulate sending email
    print(f"Sending to {email}: {message}")

@app.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: int,
    background_tasks: BackgroundTasks
):
    """Trigger pipeline and send notification in background."""
    # Start pipeline (quick operation)
    
    # Schedule background task (non-blocking)
    background_tasks.add_task(
        send_notification,
        email="admin@company.com",
        message=f"Pipeline {pipeline_id} started"
    )
    
    return {"status": "started", "pipeline_id": pipeline_id}

# ============================================================
# 8. EVENT HOOKS (Startup/Shutdown)
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("Application starting...")
    # Initialize connections, load models, etc.
    app.state.db_pool = "connection_pool"

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("Application shutting down...")
    # Close connections, cleanup

# Modern alternative (Lifespan)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler (FastAPI 0.95+)."""
    # Startup
    print("Starting up...")
    app.state.db_pool = "connection_pool"
    
    yield  # Application runs
    
    # Shutdown
    print("Shutting down...")

# app = FastAPI(lifespan=lifespan)

# ============================================================
# 9. ROUTERS (Modular Structure)
# ============================================================

from fastapi import APIRouter

# Create router for pipelines
pipelines_router = APIRouter(
    prefix="/api/v1/pipelines",
    tags=["pipelines"],
    responses={404: {"description": "Not found"}}
)

@pipelines_router.get("/")
async def router_list_pipelines():
    return {"pipelines": []}

@pipelines_router.get("/{id}")
async def router_get_pipeline(id: int):
    return {"id": id}

# Include router in main app
app.include_router(pipelines_router)

# ============================================================
# PROJECT STRUCTURE
# ============================================================
"""
my_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── dependencies.py      # Shared dependencies
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pipelines.py     # Pipeline endpoints
│   │   ├── jobs.py          # Job endpoints
│   │   └── users.py         # User endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pipeline.py      # SQLAlchemy models
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── pipeline.py      # Pydantic schemas
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pipeline_service.py
│   │   └── auth_service.py
│   └── core/
│       ├── __init__.py
│       ├── config.py        # Settings
│       └── security.py      # Auth helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures
│   └── test_pipelines.py
├── requirements.txt
└── Dockerfile
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
