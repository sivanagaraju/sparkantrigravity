"""
============================================================
FASTAPI ADVANCED PATTERNS - Lead Engineer Interview
============================================================
Topic: Database, Testing, Performance, WebSockets, Deployment
============================================================
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import asyncio

app = FastAPI()

# ============================================================
# 1. DATABASE WITH SQLALCHEMY (Async)
# ============================================================
"""
pip install sqlalchemy[asyncio] asyncpg  # PostgreSQL
pip install sqlalchemy aiosqlite         # SQLite
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.future import select
from datetime import datetime

# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# PostgreSQL: "postgresql+asyncpg://user:password@localhost/dbname"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Async session factory
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base model
class Base(DeclarativeBase):
    pass

# SQLAlchemy Model
class PipelineModel(Base):
    __tablename__ = "pipelines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    schedule = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    runs = relationship("PipelineRunModel", back_populates="pipeline")

class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    status = Column(String(20))
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    
    pipeline = relationship("PipelineModel", back_populates="runs")

# Pydantic schemas
class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schedule: str

class PipelineRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schedule: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2

# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# CRUD operations
@app.post("/pipelines", response_model=PipelineRead)
async def create_pipeline(
    pipeline: PipelineCreate,
    db: AsyncSession = Depends(get_db)
):
    db_pipeline = PipelineModel(**pipeline.dict())
    db.add(db_pipeline)
    await db.commit()
    await db.refresh(db_pipeline)
    return db_pipeline

@app.get("/pipelines", response_model=List[PipelineRead])
async def list_pipelines(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PipelineModel).offset(skip).limit(limit)
    )
    return result.scalars().all()

@app.get("/pipelines/{pipeline_id}", response_model=PipelineRead)
async def get_pipeline(
    pipeline_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PipelineModel).where(PipelineModel.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

# ============================================================
# 2. CONNECTION POOLING
# ============================================================

from sqlalchemy.pool import NullPool, QueuePool

# Configure pool
engine_with_pool = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Number of connections to maintain
    max_overflow=10,       # Extra connections when pool exhausted
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=1800,     # Recycle connections after 30 min
    pool_pre_ping=True     # Check connection health before use
)

# For serverless (AWS Lambda), use NullPool
engine_serverless = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool  # No connection pooling
)

# ============================================================
# 3. CACHING WITH REDIS
# ============================================================
"""
pip install redis aioredis
"""

import json
from functools import wraps

# Redis client
"""
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")

async def get_from_cache(key: str):
    data = await redis_client.get(key)
    return json.loads(data) if data else None

async def set_cache(key: str, value: dict, expire_seconds: int = 300):
    await redis_client.set(key, json.dumps(value), ex=expire_seconds)

# Cache decorator
def cached(expire_seconds: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            cached_data = await get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await set_cache(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

# Usage
@app.get("/pipelines/{id}/stats")
@cached(expire_seconds=60)
async def get_pipeline_stats(id: int):
    # Expensive computation
    return {"id": id, "stats": "computed stats"}
"""

# Simple in-memory cache
from functools import lru_cache
import time

class TTLCache:
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

cache = TTLCache(ttl_seconds=60)

# ============================================================
# 4. TESTING WITH TESTCLIENT
# ============================================================

from fastapi.testclient import TestClient

"""
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# tests/test_pipelines.py
def test_create_pipeline(client):
    response = client.post(
        "/pipelines",
        json={"name": "test", "schedule": "0 * * * *"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "test"

def test_get_pipeline_not_found(client):
    response = client.get("/pipelines/999")
    assert response.status_code == 404

def test_list_pipelines(client):
    # Create some pipelines
    client.post("/pipelines", json={"name": "p1", "schedule": "* * * * *"})
    client.post("/pipelines", json={"name": "p2", "schedule": "* * * * *"})
    
    response = client.get("/pipelines")
    assert response.status_code == 200
    assert len(response.json()) == 2
"""

# ============================================================
# 5. ASYNC TESTING
# ============================================================
"""
# For async tests
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/pipelines")
        assert response.status_code == 200
"""

# ============================================================
# 6. WEBSOCKETS
# ============================================================

from fastapi import WebSocket, WebSocketDisconnect
from typing import List as TypingList

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: TypingList[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: int):
    """WebSocket endpoint for real-time pipeline updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process and respond
            await websocket.send_text(f"Pipeline {pipeline_id}: {data}")
            
            # Broadcast to all clients
            await manager.broadcast(f"Pipeline {pipeline_id} update: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client disconnected from pipeline {pipeline_id}")

# ============================================================
# 7. STREAMING RESPONSES
# ============================================================

from fastapi.responses import StreamingResponse
import asyncio

async def generate_data():
    """Generate data in chunks."""
    for i in range(10):
        yield f"data: chunk {i}\n\n"
        await asyncio.sleep(0.5)

@app.get("/stream")
async def stream_data():
    """Server-Sent Events (SSE) endpoint."""
    return StreamingResponse(
        generate_data(),
        media_type="text/event-stream"
    )

# Stream file download
@app.get("/download/{file_id}")
async def download_file(file_id: int):
    async def file_generator():
        # Simulate reading large file in chunks
        for i in range(100):
            yield f"Line {i}\n".encode()
            await asyncio.sleep(0.01)
    
    return StreamingResponse(
        file_generator(),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=file_{file_id}.txt"}
    )

# ============================================================
# 8. BACKGROUND TASKS WITH CELERY
# ============================================================
"""
pip install celery redis

# celery_app.py
from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

@celery_app.task
def run_pipeline_task(pipeline_id: int):
    # Long-running task
    time.sleep(60)
    return {"pipeline_id": pipeline_id, "status": "completed"}

# In FastAPI endpoint
@app.post("/pipelines/{pipeline_id}/run-async")
async def run_pipeline_async(pipeline_id: int):
    task = run_pipeline_task.delay(pipeline_id)
    return {"task_id": task.id}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": task.status, "result": task.result}
"""

# ============================================================
# 9. OBSERVABILITY
# ============================================================

# Structured logging with loguru
"""
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    compression="zip"
)

# Usage
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello"}
"""

# Prometheus metrics
"""
from prometheus_fastapi_instrumentator import Instrumentator

# Add metrics endpoint
Instrumentator().instrument(app).expose(app)

# Access metrics at /metrics
"""

# OpenTelemetry tracing
"""
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to OTLP (Jaeger, Zipkin, etc.)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
"""

# ============================================================
# 10. DOCKER DEPLOYMENT
# ============================================================

"""
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app

# Run with Gunicorn + Uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]

# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7

volumes:
  postgres_data:
"""

# ============================================================
# 11. KUBERNETES DEPLOYMENT
# ============================================================

"""
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: myapp:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
"""

# Health check endpoints
@app.get("/health")
async def health_check():
    """Liveness probe - is the app running?"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness probe - is the app ready to serve?"""
    # Check database, cache, etc.
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
