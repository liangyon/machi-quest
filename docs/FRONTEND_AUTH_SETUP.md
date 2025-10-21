# Frontend Authentication Setup

This document describes the secure authentication implementation for the Machi Quest frontend.

## Architecture Overview

### Security Best Practices Implemented

1. **Secure Token Storage**
   - Tokens stored in localStorage (consider httpOnly cookies for production)
   - Automatic token refresh on 401 responses
   - Token cleanup on logout/errors

2. **AuthContext Pattern**
   - Centralized auth state management
   - Single source of truth for user data
   - Automatic user refresh on mount

3. **Protected Routes**
   - Homepage automatically redirects unauthenticated users
   - Loading states prevent flash of incorrect content
   - Auth check happens before rendering protected content

4. **Error Handling**
   - Graceful degradation on auth failures
   - User-friendly error messages
   - Automatic cleanup of invalid tokens

## Components

### API Client (`src/lib/api-client.ts`)
- Centralized HTTP client for backend communication
- Automatic token injection for authenticated requests
- Token refresh logic with retry mechanism
- Type-safe API methods

**Key Features:**
- Automatic 401 handling with token refresh
- Request retry after successful token refresh
- Secure token storage management

### AuthContext (`src/contexts/AuthContext.tsx`)
- React Context for global auth state
- Provides authentication methods to entire app
- Handles user data fetching and caching

**Available Methods:**
- `login(email, password)` - Email/password authentication
- `signup(email, password, displayName)` - User registration
- `logout()` - Clear session and tokens
- `refreshUser()` - Reload current user data

**Available State:**
- `user` - Current user object or null
- `isLoading` - Initial load state
- `isAuthenticated` - Boolean auth status

### Pages

#### Auth Page (`src/app/auth/page.tsx`)
- Combined login/signup form
- GitHub OAuth button
- Form validation
- Error handling
- shadcn/ui components

**Features:**
- Toggle between login and signup modes
- Client-side validation
- Loading states
- Error messages

#### Callback Page (`src/app/auth/callback/page.tsx`)
- Handles OAuth redirects
- Processes tokens from URL
- Updates AuthContext
- Redirects to homepage

**Security:**
- Validates token presence
- Uses AuthContext for state updates
- Graceful error handling

#### Home Page (`src/app/page.tsx`)
- Protected route
- Displays user profile
- Dashboard with stats
- Logout functionality

**Features:**
- Auto-redirect if not authenticated
- Loading states
- User profile display
- Stats cards

## Usage

### Protecting a Route

```tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function ProtectedPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  return <div>Protected Content</div>;
}
```

### Using Auth Methods

```tsx
'use client';

import { useAuth } from '@/contexts/AuthContext';

export default function MyComponent() {
  const { user, login, logout } = useAuth();

  const handleLogin = async () => {
    try {
      await login('user@example.com', 'password');
      // User is now logged in
    } catch (error) {
      // Handle error
    }
  };

  return (
    <div>
      {user ? (
        <div>
          <p>Welcome, {user.display_name}!</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
    </div>
  );
}
```

### Making Authenticated API Calls

```tsx
import { apiClient } from '@/lib/api-client';

// The API client automatically includes auth tokens
async function fetchData() {
  try {
    const data = await apiClient.getCurrentUser();
    return data;
  } catch (error) {
    // Token refresh is automatic
    // Error thrown only if refresh fails
    console.error('Failed to fetch user:', error);
  }
}
```

## Security Considerations

### Current Implementation
- ✅ Tokens in localStorage (accessible to JavaScript)
- ✅ Automatic token refresh
- ✅ XSS protection via React's built-in escaping
- ✅ HTTPS should be used in production
- ✅ Token validation on every request

### Production Enhancements

1. **Use httpOnly Cookies**
   ```typescript
   // Update backend to set httpOnly cookies instead of returning tokens
   // Remove localStorage usage
   // Cookies automatically included in requests
   ```

2. **Implement CSRF Protection**
   - Add CSRF tokens for state-changing operations
   - Validate tokens on backend

3. **Add Rate Limiting**
   - Limit login attempts
   - Prevent brute force attacks

4. **Implement Token Rotation**
   - Rotate refresh tokens on each use
   - Detect token reuse (potential attack)

5. **Add Security Headers**
   ```typescript
   // next.config.ts
   headers: [
     {
       key: 'X-Frame-Options',
       value: 'DENY',
     },
     {
       key: 'X-Content-Type-Options',
       value: 'nosniff',
     },
     // ... more headers
   ]
   ```

## Environment Variables

Create `.env.local` in the frontend directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, update to your production API URL.

## Testing the Flow

1. **Start the backend**:
   ```bash
   cd machi-quest/backend
   uvicorn app.main:app --reload
   ```

2. **Start the frontend**:
   ```bash
   cd machi-quest/frontend/machi
   pnpm dev
   ```

3. **Test the flow**:
   - Visit http://localhost:3000
   - You'll be redirected to `/auth`
   - Try signing up with email/password
   - Or click "Continue with GitHub"
   - After authentication, you'll see the homepage
   - Your session persists on page refresh

## Common Issues

### "Session expired" errors
- Access token has expired (15 min default)
- Refresh token should automatically renew it
- If refresh token is also expired, user must log in again

### Redirect loops
- Check that protected routes properly handle loading state
- Ensure AuthContext is properly initialized
- Verify tokens are being stored correctly

### OAuth callback fails
- Check `GITHUB_REDIRECT_URI` matches your OAuth app settings
- Verify backend environment variables are set
- Check browser console for errors

## shadcn/ui Components Used

- `Button` - For all interactive buttons
- `Card` - For content containers
- `Input` - For form fields
- `Label` - For form labels

## File Structure

```
src/
├── app/
│   ├── auth/
│   │   ├── page.tsx           # Login/signup page
│   │   └── callback/
│   │       └── page.tsx       # OAuth callback handler
│   ├── layout.tsx             # Root layout with AuthProvider
│   └── page.tsx               # Protected homepage
├── components/
│   ├── ui/                    # shadcn/ui components
│   └── GitHubOAuthButton.tsx  # OAuth button component
├── contexts/
│   └── AuthContext.tsx        # Auth state management
└── lib/
    ├── api-client.ts          # HTTP client
    └── utils.ts               # Utility functions
