from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str  # Must be set in environment variables
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh tokens last 7 days
    
    # Encryption Key for OAuth Tokens (32 bytes for Fernet)
    ENCRYPTION_KEY: str  # Must be set in environment variables
    
    # GitHub OAuth Settings
    GITHUB_CLIENT_ID: str  # Must be set in environment variables
    GITHUB_CLIENT_SECRET: str  # Must be set in environment variables
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"
    
    # GitHub Webhook Settings
    GITHUB_WEBHOOK_SECRET: str  # Must be set in environment variables
    
    # GitHub App Settings (for activity tracking integration)
    GITHUB_APP_ID: str = ""  # Optional - GitHub App ID
    GITHUB_APP_PRIVATE_KEY: str = ""  # Optional - GitHub App private key (PEM format)
    GITHUB_APP_WEBHOOK_SECRET: str = ""  # Optional - GitHub App webhook secret
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = ""  # Optional - set if using Google Sign In
    GOOGLE_CLIENT_SECRET: str = ""  # Optional
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Strava OAuth Settings
    STRAVA_CLIENT_ID: str = ""  # Optional - set if using Strava
    STRAVA_CLIENT_SECRET: str = ""  # Optional
    STRAVA_VERIFY_TOKEN: str = ""  # For webhook validation
    STRAVA_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/strava/callback"
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Machi Quest API"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # CORS Settings
    FRONTEND_URL: str = "http://localhost:3000"  # Next.js default
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Goal System Settings (NEW)
    MEDALLIONS_PER_GOAL_PER_DAY: int = 5  # Max medallions awardable per goal per day
    MAX_ACTIVE_GOALS_PER_USER: int = 5  # Maximum active goals a user can have
    DEFAULT_AVATAR_SPECIES: str = "default"  # Default avatar species on creation
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
