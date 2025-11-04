from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
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
from ..repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    
    if await user_repo.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        display_name=user_data.display_name,
        avatar_url=user_data.avatar_url
    )
    
    new_user = await user_repo.create(new_user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=604800
    )
    
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
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(form_data.username)
    
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
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
@limiter.limit("5/minute")
async def login(
    user_credentials: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(user_credentials.email)
    
    if not user or not user.hashed_password or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=604800
    )
    
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
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(refresh_token_cookie)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
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
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    response.delete_cookie(key="refresh_token")
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="logout",
        target_type="auth",
        meta_data={}
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
