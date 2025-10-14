from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import init_db


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


@app.get("/")
async def root():
    return {"status": "ok", "message": "Machi Quest API is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }
