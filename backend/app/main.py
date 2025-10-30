from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from .db import init_db
from .api import auth, users, pets, github_oauth, github_webhooks, admin, strava_webhooks
from .core.config import settings


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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API v1 prefix
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(pets.router, prefix=settings.API_V1_STR)
app.include_router(github_oauth.router, prefix=f"{settings.API_V1_STR}/auth/github", tags=["github-oauth"])
app.include_router(github_webhooks.router, tags=["github-webhooks"])
app.include_router(strava_webhooks.router, tags=["strava-webhooks"])
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
