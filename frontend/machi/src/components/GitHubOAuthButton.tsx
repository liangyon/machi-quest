'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Github } from 'lucide-react';
import { authApi } from '@/libs/api/authApi';

interface GitHubOAuthButtonProps {
  className?: string;
}

export default function GitHubOAuthButton({ className = '' }: GitHubOAuthButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleGitHubLogin = () => {
    setIsLoading(true);
    window.location.href = authApi.getGitHubLoginURL();
  };

  return (
    <Button
      onClick={handleGitHubLogin}
      disabled={isLoading}
      variant="outline"
      className={className}
    >
      <Github className="mr-2 h-4 w-4" />
      {isLoading ? 'Connecting...' : 'Continue with GitHub'}
    </Button>
  );
}
