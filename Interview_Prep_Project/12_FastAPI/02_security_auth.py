"""
============================================================
FASTAPI SECURITY & AUTHENTICATION - Lead Engineer Interview
============================================================
Topic: OAuth2, JWT, API Keys, CORS, Role-Based Access Control
============================================================
"""

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    APIKeyHeader,
    APIKeyQuery,
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

# JWT library
# pip install python-jose[cryptography] passlib[bcrypt]
from jose import JWTError, jwt
from passlib.context import CryptContext

app = FastAPI()

# ============================================================
# 1. PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

# ============================================================
# 2. JWT TOKEN HANDLING
# ============================================================

# Configuration (use environment variables in production!)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return TokenData(username=username, scopes=scopes)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# ============================================================
# 3. OAUTH2 PASSWORD FLOW
# ============================================================

# This creates the /token endpoint requirement
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "read": "Read access",
        "write": "Write access",
        "admin": "Admin access"
    }
)

# Simulated user database
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("secret"),
        "disabled": False,
        "scopes": ["read", "write", "admin"]
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "hashed_password": get_password_hash("password"),
        "disabled": False,
        "scopes": ["read"]
    }
}

class User(BaseModel):
    username: str
    email: str
    disabled: bool = False
    scopes: List[str] = []

class UserInDB(User):
    hashed_password: str

def get_user(db: dict, username: str) -> Optional[UserInDB]:
    if username in db:
        return UserInDB(**db[username])
    return None

def authenticate_user(db: dict, username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password."""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Token endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """OAuth2 token endpoint."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Extract user from JWT token."""
    token_data = decode_token(token)
    user = get_user(fake_users_db, token_data.username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is not disabled."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Protected endpoint
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return current_user

# ============================================================
# 4. ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================

class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "write"
    VIEWER = "read"

def require_scope(required_scope: str):
    """Create a dependency that checks for a specific scope."""
    async def scope_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required"
            )
        return current_user
    return scope_checker

# Usage
@app.get("/admin-only")
async def admin_endpoint(user: User = Depends(require_scope("admin"))):
    """Only accessible by users with 'admin' scope."""
    return {"message": "Welcome, admin!", "user": user.username}

@app.delete("/pipelines/{id}")
async def delete_pipeline(
    id: int,
    user: User = Depends(require_scope("write"))
):
    """Requires 'write' scope."""
    return {"deleted": id, "by": user.username}

# ============================================================
# 5. API KEY AUTHENTICATION
# ============================================================

API_KEYS = {
    "key-abc123": {"name": "service-a", "scopes": ["read"]},
    "key-xyz789": {"name": "service-b", "scopes": ["read", "write"]}
}

# Header-based API key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Query param API key
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
    api_key_query: str = Security(api_key_query)
) -> dict:
    """Validate API key from header or query param."""
    api_key = api_key_header or api_key_query
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return API_KEYS[api_key]

@app.get("/api/data")
async def get_data(api_key_info: dict = Depends(get_api_key)):
    """Endpoint protected by API key."""
    return {"data": "sensitive data", "client": api_key_info["name"]}

# ============================================================
# 6. CORS (Cross-Origin Resource Sharing)
# ============================================================

from fastapi.middleware.cors import CORSMiddleware

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # React dev server
        "https://myapp.com",         # Production frontend
    ],
    allow_credentials=True,         # Allow cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allowed HTTP methods
    allow_headers=["*"],            # Allowed headers
    expose_headers=["X-Custom-Header"],  # Headers exposed to browser
    max_age=600,                    # Cache preflight for 10 minutes
)

# ============================================================
# 7. CUSTOM MIDDLEWARE
# ============================================================

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request/response details."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        # Add custom header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

app.add_middleware(LoggingMiddleware)

# ============================================================
# 8. EXCEPTION HANDLING
# ============================================================

from fastapi import Request
from fastapi.responses import JSONResponse

class PipelineNotFoundError(Exception):
    def __init__(self, pipeline_id: int):
        self.pipeline_id = pipeline_id

class AuthenticationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

# Custom exception handlers
@app.exception_handler(PipelineNotFoundError)
async def pipeline_not_found_handler(request: Request, exc: PipelineNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "PipelineNotFound",
            "message": f"Pipeline {exc.pipeline_id} not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"error": "AuthenticationError", "message": exc.detail}
    )

# Usage
@app.get("/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: int):
    if pipeline_id == 0:
        raise PipelineNotFoundError(pipeline_id)
    return {"running": pipeline_id}

# ============================================================
# 9. RATE LIMITING
# ============================================================

# Using slowapi: pip install slowapi
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/limited")
@limiter.limit("5/minute")  # 5 requests per minute
async def limited_endpoint(request: Request):
    return {"message": "This endpoint is rate limited"}
"""

# Simple in-memory rate limiter
from collections import defaultdict
import time

class SimpleRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[key] = [
            t for t in self.requests[key] if t > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[key].append(now)
        return True

rate_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)

async def check_rate_limit(request: Request):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

@app.get("/rate-limited", dependencies=[Depends(check_rate_limit)])
async def rate_limited_endpoint():
    return {"message": "Success"}

# ============================================================
# 10. HTTPS/TLS
# ============================================================
"""
Production HTTPS setup:

1. Using Uvicorn directly:
uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem

2. Using Nginx as reverse proxy (recommended):
# nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

3. In cloud (AWS ALB, Azure Front Door):
- Terminate TLS at load balancer
- Internal traffic uses HTTP
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
