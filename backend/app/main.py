from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .db import init_db
from .routes import auth, users, avatars, goals
from .api import admin
from .api.integrations import github_oauth, google_oauth, github_app
from .api.webhooks import github, strava
from .core.config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes database on startup.
    """
    # Startup
    init_db()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="Machi Quest API",
    description="Backend API for Machi Quest - A gamified productivity companion",
    version="0.1.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add session middleware for OAuth (required by Authlib)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type"],  # Only needed headers
    max_age=600,  # Cache preflight for 10 minutes
)

# Include routers with API v1 prefix
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(avatars.router, prefix=settings.API_V1_STR)
app.include_router(goals.router, prefix=settings.API_V1_STR)

# Authentication integrations (sign-in methods)
app.include_router(github_oauth.router, prefix=f"{settings.API_V1_STR}/auth/github", tags=["auth-github"])
app.include_router(google_oauth.router, prefix=f"{settings.API_V1_STR}/auth/google", tags=["auth-google"])

# Activity tracking integrations
app.include_router(github_app.router, prefix=f"{settings.API_V1_STR}/integrations/github-app", tags=["integrations-github"])

# Webhooks
app.include_router(github.router, tags=["webhooks-github"])
app.include_router(strava.router, tags=["webhooks-strava"])

# Admin
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "Machi Quest API is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }
