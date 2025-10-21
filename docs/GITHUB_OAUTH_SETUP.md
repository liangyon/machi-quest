# GitHub OAuth Setup Guide

This guide walks you through setting up GitHub OAuth authentication for Machi Quest, including secure token storage using encryption.

## Overview

The implementation includes:
- **Secure Token Storage**: OAuth tokens are encrypted using Fernet (symmetric encryption) before being stored in the database
- **Latest Packages**: Using `authlib`, `httpx`, and `cryptography` for modern OAuth implementation
- **User Linking**: Automatically links GitHub accounts to existing users or creates new ones
- **Token Management**: Stores both access and refresh tokens securely

## Prerequisites

1. Python 3.10+ with pip
2. Node.js 18+ with pnpm
3. PostgreSQL database
4. A GitHub account

## Step 1: Create a GitHub OAuth App

1. Go to [GitHub Settings > Developer Settings > OAuth Apps](https://github.com/settings/developers)
2. Click **"New OAuth App"**
3. Fill in the application details:
   - **Application name**: `Machi Quest` (or your preferred name)
   - **Homepage URL**: `http://localhost:3000` (for development)
   - **Authorization callback URL**: `http://localhost:8000/api/v1/auth/github/callback`
4. Click **"Register application"**
5. On the next page, note your **Client ID**
6. Click **"Generate a new client secret"** and save the secret (you won't be able to see it again)

## Step 2: Generate Encryption Key

The encryption key is used to encrypt OAuth tokens before storing them in the database.

Run this command to generate a secure encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save the output - you'll need it in the next step.

## Step 3: Configure Environment Variables

Create or update your `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/machi_quest
REDIS_URL=redis://localhost:6379

# JWT Authentication
SECRET_KEY=your_secure_secret_key_here

# OAuth Token Encryption
ENCRYPTION_KEY=your_generated_encryption_key_from_step_2

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id_from_step_1
GITHUB_CLIENT_SECRET=your_github_client_secret_from_step_1
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback
```

**Security Notes:**
- Never commit the `.env` file to version control
- Use different keys for development and production
- Store production secrets in a secure secret management system (e.g., AWS Secrets Manager, HashiCorp Vault)

## Step 4: Install Backend Dependencies

```bash
cd machi-quest/backend
pip install -r requirements.txt
```

New packages added:
- `cryptography` - For Fernet encryption of OAuth tokens
- `authlib` - Modern OAuth library with better async support
- `httpx` - Async HTTP client for making requests to GitHub API

## Step 5: Run Database Migrations

Apply the database migration to add GitHub OAuth fields:

```bash
cd machi-quest/backend
alembic upgrade head
```

This migration adds:
- `github_id` - Unique identifier for GitHub users
- `github_username` - GitHub username for display
- Makes `hashed_password` nullable (for OAuth-only users)

## Step 6: Start the Backend Server

```bash
cd machi-quest/backend
uvicorn app.main:app --reload --port 8000
```

The server should start on `http://localhost:8000`

## Step 7: Start the Frontend

```bash
cd machi-quest/frontend/machi
pnpm install
pnpm dev
```

The frontend should start on `http://localhost:3000`

## Step 8: Test the OAuth Flow

1. Add the GitHub OAuth button to your login page:

```tsx
import GitHubOAuthButton from '@/components/GitHubOAuthButton';

export default function LoginPage() {
  return (
    <div>
      <h1>Sign In</h1>
      <GitHubOAuthButton />
    </div>
  );
}
```

2. Click the "Continue with GitHub" button
3. Authorize the application on GitHub
4. You should be redirected back to the app and automatically logged in

## How It Works

### Backend Flow

1. **Login Endpoint** (`/api/v1/auth/github/login`):
   - Redirects user to GitHub's authorization page
   - Requests `user:email` and `read:user` scopes

2. **Callback Endpoint** (`/api/v1/auth/github/callback`):
   - Receives authorization code from GitHub
   - Exchanges code for access token
   - Fetches user profile and email from GitHub API
   - Creates or updates user in database
   - Encrypts and stores OAuth tokens
   - Issues JWT tokens for app authentication
   - Redirects to frontend with tokens

3. **Token Storage**:
   - OAuth tokens are encrypted using Fernet before storage
   - Encryption key is stored securely in environment variables
   - Only encrypted data is stored in the database

### Frontend Flow

1. **OAuth Button Component**:
   - Initiates OAuth flow by redirecting to backend
   - Shows loading state during redirect

2. **Callback Page** (`/auth/callback`):
   - Receives JWT tokens from backend
   - Stores tokens in localStorage (consider httpOnly cookies for production)
   - Redirects to main app

## Security Considerations

### Token Encryption
- OAuth tokens are encrypted using Fernet (symmetric encryption)
- Encryption key must be 32 url-safe base64-encoded bytes
- Never log or expose encrypted tokens
- Rotate encryption keys periodically

### Token Storage
- **Development**: Tokens stored in localStorage for simplicity
- **Production**: Consider using httpOnly cookies:
  - More secure against XSS attacks
  - Automatically included in requests
  - Cannot be accessed by JavaScript

### Best Practices
1. Use HTTPS in production
2. Implement token refresh mechanism
3. Add rate limiting to OAuth endpoints
4. Monitor for suspicious OAuth activity
5. Implement CSRF protection
6. Use short-lived JWT access tokens (15 minutes)
7. Store refresh tokens securely

## Production Deployment

For production, update the following:

1. **GitHub OAuth App**:
   - Update Homepage URL to your production domain
   - Update Authorization callback URL to `https://yourdomain.com/api/v1/auth/github/callback`

2. **Environment Variables**:
   - Update `GITHUB_REDIRECT_URI`
   - Update `FRONTEND_URL` and `BACKEND_CORS_ORIGINS`
   - Use production secret management

3. **Security Headers**:
   - Enable HTTPS only
   - Add security headers (CSP, HSTS, etc.)
   - Implement rate limiting

## Troubleshooting

### "Authentication failed: Missing tokens"
- Check that `GITHUB_REDIRECT_URI` matches your OAuth app settings
- Verify environment variables are set correctly

### "OAuth error" in backend logs
- Check GitHub OAuth app credentials
- Verify encryption key is properly formatted
- Check database connection

### Database connection errors
- Ensure PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Check database user permissions

### Token decryption errors
- Verify `ENCRYPTION_KEY` hasn't changed
- Ensure key is 32 bytes url-safe base64
- Check that tokens were encrypted with the same key

## API Endpoints

### `GET /api/v1/auth/github/login`
Initiates GitHub OAuth flow

### `GET /api/v1/auth/github/callback`
Handles GitHub OAuth callback
- **Query Params**: `code` (authorization code from GitHub)
- **Returns**: Redirect to frontend with JWT tokens

### `POST /api/v1/auth/github/disconnect`
Disconnects GitHub integration for current user
- **Auth Required**: Yes
- **Returns**: Success message

## Database Schema

### Users Table (Updated)
```sql
- github_id VARCHAR(100) UNIQUE     -- GitHub user ID
- github_username VARCHAR(100)       -- GitHub username
- hashed_password TEXT NULL          -- Now nullable for OAuth-only users
```

### Integrations Table (Existing)
```sql
- provider VARCHAR(50)                      -- 'github'
- access_token_encrypted BYTEA              -- Encrypted OAuth access token
- refresh_token_encrypted BYTEA             -- Encrypted OAuth refresh token
- metadata JSONB                            -- GitHub username, scopes, etc.
```

## Additional Resources

- [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [Authlib Documentation](https://docs.authlib.org/)
- [Cryptography (Fernet) Documentation](https://cryptography.io/en/latest/fernet/)
- [FastAPI OAuth Documentation](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
