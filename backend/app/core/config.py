from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str  # Must be set in environment variables
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh tokens last 7 days
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Machi Quest API"
    
    # CORS Settings
    FRONTEND_URL: str = "http://localhost:3000"  # Next.js default
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
