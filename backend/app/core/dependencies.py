from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from .security import decode_token, verify_token_type
from .token_blacklist import get_token_blacklist
from ..db.database import get_db
from ..models import User
# OAuth2 scheme - this will show the login form in Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

logger = logging.getLogger(__name__)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Use this in any endpoint that requires authentication.
    
    Checks:
    Token is valid JWT
    token type is "access"
    Token is not blacklisted
    User is not blacklisted
    User exists in database
    """
    # Decode and validate access token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token type
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token blacklist (optional - requires Redis)
    try:
        blacklist = get_token_blacklist()
        if blacklist.is_revoked(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is globally blacklisted
        if blacklist.is_user_blacklisted(user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User session has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (ConnectionError, Exception) as e:
        logger.warning(f"Redis blacklist check failed: {e}")
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
