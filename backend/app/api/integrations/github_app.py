"""
GitHub App Integration

Handles GitHub App installation for activity tracking.
This is SEPARATE from GitHub OAuth (which is just for sign-in).

GitHub App Flow:
1. User clicks "Track My GitHub Activity" 
2. They're redirected to install your GitHub App
3. GitHub redirects back with installation_id
4. We store installation_id and can now track ALL their repo activity

Docs: https://docs.github.com/en/apps
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import jwt
import time
import uuid
from datetime import datetime, timedelta

from ...core.config import settings
from ...core.security import encrypt_token
from ...core.dependencies import get_db
from ...models import User, Integration

router = APIRouter()


def generate_github_app_jwt() -> str:
    """
    Generate a JWT token for authenticating as the GitHub App.
    
    GitHub Apps use JWT tokens (not OAuth tokens) signed with a private key.
    These tokens are short-lived (10 minutes max) and used to authenticate
    as the app itself to request installation tokens.
    
    Returns:
        JWT token string
    """
    if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
        raise HTTPException(
            status_code=503,
            detail="GitHub App is not configured. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
        )
    
    # JWT payload
    now = int(time.time())
    payload = {
        'iat': now,  # Issued at time
        'exp': now + 600,  # Expires in 10 minutes (max allowed)
        'iss': settings.GITHUB_APP_ID  # GitHub App ID
    }
    
    # Sign with private key
    token = jwt.encode(
        payload,
        settings.GITHUB_APP_PRIVATE_KEY,
        algorithm='RS256'
    )
    
    return token


async def get_installation_token(installation_id: int) -> str:
    """
    Get an installation access token for a specific installation.
    
    Installation tokens are short-lived (1 hour) and have access to
    repositories the app is installed on for that specific user/org.
    
    Args:
        installation_id: The GitHub App installation ID
        
    Returns:
        Installation access token
    """
    app_jwt = generate_github_app_jwt()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'https://api.github.com/app/installations/{installation_id}/access_tokens',
            headers={
                'Authorization': f'Bearer {app_jwt}',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        response.raise_for_status()
        data = response.json()
        return data['token']


@router.get("/install")
async def github_app_install(request: Request):
    """
    Redirect user to install the GitHub App.
    
    After user is already signed in (via GitHub or Google OAuth),
    they can click "Track My GitHub Activity" which brings them here.
    """
    if not settings.GITHUB_APP_ID:
        raise HTTPException(
            status_code=503,
            detail="GitHub App is not configured. Set GITHUB_APP_ID."
        )
    
    # Redirect to GitHub App installation page
    # The state parameter helps us identify the user after they return
    # TODO: Add state parameter with user session data for security
    install_url = f"https://github.com/apps/YOUR_APP_NAME/installations/new"
    
    return RedirectResponse(url=install_url)


@router.get("/callback")
async def github_app_callback(
    installation_id: int = Query(...),
    setup_action: str = Query(...),
    db: Session = Depends(get_db),
    # TODO: Add current_user dependency to identify which user is installing
):
    """
    Handle GitHub App installation callback.
    
    After user installs the app, GitHub redirects here with:
    - installation_id: Unique ID for this installation
    - setup_action: 'install' or 'update'
    
    We need to:
    1. Identify which user is installing (from session/state)
    2. Get installation access token
    3. Store installation_id in Integration table
    4. Set up webhook automatically (GitHub does this for us!)
    """
    try:
        # TODO: Get current_user from session/JWT
        # For now, this is a placeholder showing the structure
        
        # Get installation token to verify access
        installation_token = await get_installation_token(installation_id)
        
        # Get installation details
        app_jwt = generate_github_app_jwt()
        async with httpx.AsyncClient() as client:
            # Get installation info
            install_response = await client.get(
                f'https://api.github.com/app/installations/{installation_id}',
                headers={
                    'Authorization': f'Bearer {app_jwt}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            install_response.raise_for_status()
            install_data = install_response.json()
            
            # Get the user/org who installed
            account = install_data.get('account', {})
            account_login = account.get('login')
            account_type = account.get('type')  # 'User' or 'Organization'
        
        # TODO: Find the user who initiated the installation
        # This requires implementing a state parameter or session management
        # For now, we'll need to match by GitHub username
        user = db.query(User).filter(User.github_username == account_login).first()
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail=f"Could not find user with GitHub username: {account_login}. Please sign in with GitHub first."
            )
        
        # Check if integration already exists
        integration = db.query(Integration).filter(
            Integration.user_id == user.id,
            Integration.provider == 'github_app'
        ).first()
        
        # Encrypt the installation token (will be refreshed periodically)
        encrypted_token = encrypt_token(installation_token)
        
        if integration:
            # Update existing integration
            integration.access_token_encrypted = encrypted_token
            integration.meta_data = {
                'installation_id': installation_id,
                'account_login': account_login,
                'account_type': account_type,
                'setup_action': setup_action,
                'token_expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            }
        else:
            # Create new integration
            integration = Integration(
                id=uuid.uuid4(),
                user_id=user.id,
                provider='github_app',
                access_token_encrypted=encrypted_token,
                meta_data={
                    'installation_id': installation_id,
                    'account_login': account_login,
                    'account_type': account_type,
                    'setup_action': setup_action,
                    'token_expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                }
            )
            db.add(integration)
        
        db.commit()
        
        # Redirect back to frontend
        redirect_url = f"{settings.FRONTEND_URL}/settings/integrations?github_app=success"
        return RedirectResponse(url=redirect_url)
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Installation error: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_github_app(
    request: Request,
    db: Session = Depends(get_db),
    # TODO: Add get_current_user dependency
):
    """
    Disconnect GitHub App integration for the current user.
    This removes activity tracking but keeps the user's account.
    """
    # TODO: Implement once get_current_user dependency is available
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - requires authentication middleware"
    )


@router.get("/status")
async def github_app_status(
    db: Session = Depends(get_db),
    # TODO: Add get_current_user dependency
):
    """
    Check if the current user has GitHub App installed.
    Returns installation status and metadata.
    """
    # TODO: Implement once get_current_user dependency is available
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - requires authentication middleware"
    )
