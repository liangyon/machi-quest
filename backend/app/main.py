from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db import init_db
from .api import auth, users
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

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Machi Quest API is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }
