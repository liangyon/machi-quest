'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { setAccessToken } from '@/lib/axios';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get access token from URL (refresh token is in httpOnly cookie)
        const accessToken = searchParams.get('access_token');

        if (!accessToken) {
          setError('Authentication failed: Missing access token');
          setStatus('error');
          return;
        }

        // Store access token in memory
        setAccessToken(accessToken);

        // Fetch user data using the new access token
        await refreshUser();

        setStatus('success');

        // Redirect to dashboard after a brief delay
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        setStatus('error');
      }
    };

    handleCallback();
  }, [searchParams, router, refreshUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        {status === 'loading' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Authenticating...
            </h2>
            <p className="text-gray-600">
              Please wait while we complete your sign in
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="rounded-full bg-green-100 p-3 mx-auto w-16 h-16 flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Success!
            </h2>
            <p className="text-gray-600">
              Redirecting you to the app...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="rounded-full bg-red-100 p-3 mx-auto w-16 h-16 flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Authentication Failed
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              Return to Home
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
