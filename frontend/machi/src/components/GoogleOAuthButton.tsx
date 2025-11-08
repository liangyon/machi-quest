"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { authApi } from '@/lib/api/authApi';

interface GoogleOAuthButtonProps {
  className?: string;
}

export default function GoogleOAuthButton({ className = '' }: GoogleOAuthButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = () => {
    setIsLoading(true);
    // Redirect to backend Google OAuth login endpoint
    window.location.href = authApi.getGoogleLoginURL();
  };

  return (
    <Button onClick={handleGoogleLogin} disabled={isLoading} variant="outline" className={className}>
      <svg className="mr-2 h-4 w-4" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden>
        <path fill="#EA4335" d="M24 9.5c3.9 0 7 1.6 9.2 3.1l6.8-6.8C36.9 2.6 30.9 0 24 0 14.7 0 6.9 5.6 3 13.6l7 5.4C12.9 14.1 18 9.5 24 9.5z" />
        <path fill="#34A853" d="M46.5 24.5c0-1.7-.1-3.4-.4-5H24v9.6h12.6c-.5 3-2.6 5.6-5.6 7.3l8.6 6.6C44.8 38.1 46.5 31.7 46.5 24.5z" />
        <path fill="#4A90E2" d="M10.9 28.9A14.5 14.5 0 0 1 10 24c0-1.3.2-2.6.5-3.9L3.5 14.7A24 24 0 0 0 0 24c0 3.9.9 7.6 2.6 10.9l8.3-6z" />
        <path fill="#FBBC05" d="M24 48c6.5 0 12.2-2.1 16.2-5.7l-8.6-6.6c-2.4 1.6-5.4 2.6-7.6 2.6-5.9 0-10.8-3.9-12.6-9.2l-8.3 6A24 24 0 0 0 24 48z" />
      </svg>
      {isLoading ? 'Connecting...' : 'Continue with Google'}
    </Button>
  );
}
