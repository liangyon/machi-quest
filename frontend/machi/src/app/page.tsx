'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, Github, User } from 'lucide-react';
import Image from 'next/image';

export default function Home() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect to auth page if not authenticated
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleLogout = async () => {
    await logout();
    router.push('/auth');
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900"></div>
      </div>
    );
  }

  // Don't render content if not authenticated (will redirect)
  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-neutral-900 to-neutral-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">M</span>
              </div>
              <h1 className="text-2xl font-bold text-neutral-900">Machi Quest</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-neutral-600">
                {user.avatar_url ? (
                  <Image
                    src={user.avatar_url}
                    alt={user.display_name}
                    className="w-8 h-8 rounded-full"
                    width={32}
                    height={32}
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-neutral-200 flex items-center justify-center">
                    <User className="w-4 h-4 text-neutral-600" />
                  </div>
                )}
                <span className="font-medium text-neutral-900">{user.display_name}</span>
              </div>
              
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-8">
          {/* Welcome Section */}
          <div>
            <h2 className="text-3xl font-bold text-neutral-900 mb-2">
              Welcome back, {user.display_name}!
            </h2>
            <p className="text-neutral-600">
              Ready to level up your productivity? Let&apos;s get started!
            </p>
          </div>

          {/* User Profile Card */}
          <Card>
            <CardHeader>
              <CardTitle>Your Profile</CardTitle>
              <CardDescription>Manage your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                {user.avatar_url ? (
                  <Image
                    src={user.avatar_url}
                    alt={user.display_name}
                    className="w-16 h-16 rounded-full"
                    width={64}
                    height={64}
                  />
                ) : (
                  <div className="w-16 h-16 rounded-full bg-neutral-200 flex items-center justify-center">
                    <User className="w-8 h-8 text-neutral-600" />
                  </div>
                )}
                <div>
                  <p className="font-semibold text-lg">{user.display_name}</p>
                  <p className="text-sm text-neutral-600">{user.email}</p>
                  {user.github_username && (
                    <div className="flex items-center gap-1 text-sm text-neutral-500 mt-1">
                      <Github className="w-3 h-3" />
                      <span>@{user.github_username}</span>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Your Pets</CardTitle>
                <CardDescription>Virtual companions</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-neutral-900">0</p>
                <p className="text-sm text-neutral-600 mt-1">
                  Create your first pet to get started!
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Goals</CardTitle>
                <CardDescription>Active goals</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-neutral-900">0</p>
                <p className="text-sm text-neutral-600 mt-1">
                  Set your productivity goals
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Streak</CardTitle>
                <CardDescription>Days active</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-neutral-900">1 🔥</p>
                <p className="text-sm text-neutral-600 mt-1">
                  Keep up the great work!
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Getting Started */}
          <Card>
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
              <CardDescription>Follow these steps to begin your journey</CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3 list-decimal list-inside text-neutral-700">
                <li>Create your first virtual pet companion</li>
                <li>Connect your productivity tools (GitHub, etc.)</li>
                <li>Set up your first goal</li>
                <li>Start tracking your progress and watch your pet grow!</li>
              </ol>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
