from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from authlib.integrations.starlette_client import OAuth
from typing import Optional
import httpx

from ...core.config import settings
from ...core.security import create_access_token, create_refresh_token, encrypt_token
from ...core.dependencies import get_db
from ...models import User, Integration, AuditLog
import uuid

router = APIRouter()

# Configure OAuth
oauth = OAuth()
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params={'scope': 'user:email read:user'},
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    client_kwargs={'scope': 'user:email read:user'},
)


@router.get("/login")
async def github_login(request: Request):
    """
    Initiate GitHub OAuth flow.
    Redirects user to GitHub for authentication.
    """
    redirect_uri = settings.GITHUB_REDIRECT_URI
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def github_callback(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle GitHub OAuth callback.
    Exchange authorization code for access token and create/update user.
    """
    try:
        # Exchange code for token
        token = await oauth.github.authorize_access_token(request)
        
        # Get user info from GitHub
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {token["access_token"]}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get user profile
            user_response = await client.get(
                'https://api.github.com/user',
                headers=headers
            )
            user_response.raise_for_status()
            github_user = user_response.json()
            
            # Get user emails
            emails_response = await client.get(
                'https://api.github.com/user/emails',
                headers=headers
            )
            emails_response.raise_for_status()
            emails = emails_response.json()
            
            # Find primary email
            primary_email = next(
                (email['email'] for email in emails if email['primary']),
                github_user.get('email')
            )
            
            if not primary_email:
                raise HTTPException(
                    status_code=400,
                    detail="No email found in GitHub account"
                )
        
        # Check if user exists by GitHub ID
        result = await db.execute(
            select(User).where(User.github_id == str(github_user['id']))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Check if user exists by email
            result = await db.execute(
                select(User).where(User.email == primary_email)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Link existing user to GitHub
                user.github_id = str(github_user['id'])
                user.github_username = github_user['login']
                user.avatar_url = github_user.get('avatar_url')
            else:
                # Create new user
                user = User(
                    id=uuid.uuid4(),
                    email=primary_email,
                    display_name=github_user.get('name') or github_user['login'],
                    avatar_url=github_user.get('avatar_url'),
                    github_id=str(github_user['id']),
                    github_username=github_user['login']
                )
                db.add(user)
        else:
            # Update existing user info
            user.email = primary_email
            user.display_name = github_user.get('name') or github_user['login']
            user.avatar_url = github_user.get('avatar_url')
            user.github_username = github_user['login']
        
        await db.commit()
        await db.refresh(user)
        
        # Store or update GitHub integration with encrypted tokens
        result = await db.execute(
            select(Integration).where(
                Integration.user_id == user.id,
                Integration.provider == 'github'
            )
        )
        integration = result.scalar_one_or_none()
        
        encrypted_access_token = encrypt_token(token['access_token'])
        encrypted_refresh_token = None
        if token.get('refresh_token'):
            encrypted_refresh_token = encrypt_token(token['refresh_token'])
        
        if integration:
            integration.access_token_encrypted = encrypted_access_token
            integration.refresh_token_encrypted = encrypted_refresh_token
            integration.meta_data = {
                'github_username': github_user['login'],
                'github_id': github_user['id'],
                'scope': token.get('scope', ''),
            }
        else:
            integration = Integration(
                id=uuid.uuid4(),
                user_id=user.id,
                provider='github',
                access_token_encrypted=encrypted_access_token,
                refresh_token_encrypted=encrypted_refresh_token,
                meta_data={
                    'github_username': github_user['login'],
                    'github_id': github_user['id'],
                    'scope': token.get('scope', ''),
                }
            )
            db.add(integration)
        
        await db.commit()
        
        # Audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="github_login",
            target_type="auth",
            meta_data={
                "ip_address": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "github_username": github_user['login']
            }
        )
        db.add(audit_log)
        await db.commit()
        
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
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth error: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_github(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_db)  # You'll need to implement get_current_user dependency
):
    """
    Disconnect GitHub integration for the current user.
    """
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.provider == 'github'
        )
    )
    integration = result.scalar_one_or_none()
    
    if integration:
        await db.delete(integration)
        await db.commit()
    
    return {"message": "GitHub integration disconnected successfully"}
