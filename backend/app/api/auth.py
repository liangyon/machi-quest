from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from uuid import UUID
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..db.database import get_db
from ..db.models import User, AuditLog
from ..schemas.user import UserCreate, UserLogin, UserResponse, Token
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from ..core.dependencies import get_current_user
from ..core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")  # 3 registration attempts per minute
def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Register a new user and return tokens.
    
    Available at both /signup and /register endpoints.
    Returns access token in body, refresh token in httpOnly cookie.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        display_name=user_data.display_name,
        avatar_url=user_data.avatar_url
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    # Set refresh token in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # HTTPS only in production
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    # Audit log
    audit_log = AuditLog(
        user_id=new_user.id,
        action="register",
        target_type="auth",
        meta_data={
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")  # 5 login attempts per minute
def login_for_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login for Swagger UI.
    
    Use your email as the username and your password.
    This endpoint is specifically for the Swagger UI login form.
    """
    # Find user by email (username field in OAuth2 form is the email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check if user exists and password is correct
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set refresh token in httpOnly cookie if Response is available
    if response:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=604800
        )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # 5 login attempts per minute
def login(
    user_credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login user and return JWT access token.
    
    Returns access token in body, refresh token in httpOnly cookie.
    Access tokens are short-lived (15 minutes) for security.
    Refresh tokens are stored in httpOnly cookies for XSS protection.
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    # Check if user exists and password is correct
    if not user or not user.hashed_password or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set refresh token in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # HTTPS only in production
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    # Audit log
    audit_log = AuditLog(
        user_id=user.id,
        action="login",
        target_type="auth",
        meta_data={
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": "password"
        }
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    request: Request,
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from httpOnly cookie.
    
    Returns new access token and sets new refresh token in cookie.
    """
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate refresh token
    payload = decode_token(refresh_token_cookie)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token type
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
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
    
    # Verify user still exists
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    # Set new refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=604800
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by clearing refresh token cookie.
    """
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="logout",
        target_type="auth",
        meta_data={}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user.
    
    Requires a valid access token in the Authorization header.
    """
    return current_user
