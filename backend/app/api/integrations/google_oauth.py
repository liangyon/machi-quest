"""
Google OAuth Integration

Handles "Sign in with Google" authentication flow.
This is separate from GitHub - users can sign in with either GitHub or Google.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
import httpx
import uuid

from ...core.config import settings
from ...core.security import create_access_token, create_refresh_token
from ...core.dependencies import get_db
from ...db.models import User, AuditLog

router = APIRouter()

# Configure OAuth for Google
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    },
)


@router.get("/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth flow.
    Redirects user to Google for authentication.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Exchange authorization code for access token and create/update user.
    """
    try:
        # Exchange code for token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(
                status_code=400,
                detail="Failed to get user info from Google"
            )
        
        google_id = user_info.get('sub')  # Google's unique user ID
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        if not google_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Missing required user information from Google"
            )
        
        # Check if user exists by Google ID
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Check if user exists by email
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Link existing user to Google
                user.google_id = google_id
                if not user.avatar_url and picture:
                    user.avatar_url = picture
            else:
                # Create new user
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    display_name=name or email.split('@')[0],
                    avatar_url=picture,
                    google_id=google_id
                )
                db.add(user)
        else:
            # Update existing user info
            user.email = email
            if name:
                user.display_name = name
            if picture:
                user.avatar_url = picture
        
        db.commit()
        
        # Audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="google_login",
            target_type="auth",
            meta_data={
                "ip_address": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        db.add(audit_log)
        db.commit()
        
        # Create JWT tokens for our application
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Create redirect response with refresh token in httpOnly cookie
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}"
        response = RedirectResponse(url=redirect_url)
        
        # Set refresh token in httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=604800  # 7 days
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth error: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_google(
    request: Request,
    db: Session = Depends(get_db),
    # TODO: Add get_current_user dependency when implemented
):
    """
    Disconnect Google account for the current user.
    This removes the google_id linkage but keeps the user account.
    """
    # TODO: Implement once get_current_user dependency is available
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - requires authentication middleware"
    )
