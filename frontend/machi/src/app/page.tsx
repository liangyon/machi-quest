'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { usePet } from '@/contexts/PetContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, Github, User, Plus, Heart, Zap, Utensils } from 'lucide-react';
import Image from 'next/image';

import Link from 'next/link';

export default function Home() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const { pets, createPet, isLoading: petLoading } = usePet();
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
                variant="outline"
                size="sm"
              >
                <Link className="w-4 h-4 mr-2" href="/test"/>
                Test
              </Button>
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
                <p className="text-3xl font-bold text-neutral-900">{pets.length}</p>
                <p className="text-sm text-neutral-600 mt-1">
                  {pets.length === 0 ? 'Create your first pet to get started!' : `${pets.length} active ${pets.length === 1 ? 'pet' : 'pets'}`}
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

          {/* Pet Display Section */}
          {pets.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-neutral-900">Your Pets</h3>
                <Button
                  onClick={async () => {
                    const name = prompt('Enter pet name:');
                    if (name) {
                      try {
                        await createPet({ name, species: 'cat' });
                        alert('Pet created!');
                      } catch (err) {
                        alert(err + 'Failed to create pet');
                      }
                    }
                  }}
                  disabled={petLoading}
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Pet
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {pets.map((pet) => (
                  <Card key={pet.id} className="overflow-hidden">
                    <CardHeader className="bg-gradient-to-br from-blue-50 to-purple-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-xl">{pet.name}</CardTitle>
                          <CardDescription className="capitalize">{pet.species}</CardDescription>
                        </div>
                        <div className="text-3xl">
                          {pet.species === 'cat' ? '🐱' : pet.species === 'dog' ? '🐶' : '🐉'}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-neutral-600">Level</span>
                        <span className="font-bold text-neutral-900">{pet.state_json.level}</span>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-1">
                            <Heart className="w-4 h-4 text-red-500" />
                            <span>Health</span>
                          </div>
                          <span className="font-semibold">{pet.state_json.health}%</span>
                        </div>
                        <div className="w-full bg-neutral-200 rounded-full h-2">
                          <div
                            className="bg-red-500 h-2 rounded-full transition-all"
                            style={{ width: `${pet.state_json.health}%` }}
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-1">
                            <Zap className="w-4 h-4 text-yellow-500" />
                            <span>Energy</span>
                          </div>
                          <span className="font-semibold">{pet.state_json.energy}%</span>
                        </div>
                        <div className="w-full bg-neutral-200 rounded-full h-2">
                          <div
                            className="bg-yellow-500 h-2 rounded-full transition-all"
                            style={{ width: `${pet.state_json.energy}%` }}
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-1">
                            <Utensils className="w-4 h-4 text-orange-500" />
                            <span>Hunger</span>
                          </div>
                          <span className="font-semibold">{pet.state_json.hunger}%</span>
                        </div>
                        <div className="w-full bg-neutral-200 rounded-full h-2">
                          <div
                            className="bg-orange-500 h-2 rounded-full transition-all"
                            style={{ width: `${pet.state_json.hunger}%` }}
                          />
                        </div>
                      </div>
                      
                      <div className="pt-2 border-t">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-neutral-600">Mood</span>
                          <span className="font-semibold capitalize text-neutral-900">
                            {pet.state_json.mood}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm mt-1">
                          <span className="text-neutral-600">XP</span>
                          <span className="text-xs text-neutral-500">
                            {pet.state_json.xp} / {pet.state_json.xp_to_next_level}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Getting Started</CardTitle>
                <CardDescription>Create your first pet to begin your journey</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-neutral-700">
                  Welcome to Machi Quest! Create your first virtual pet companion to start tracking your productivity and watch them grow as you accomplish your goals.
                </p>
                <Button
                  onClick={async () => {
                    const name = prompt('Enter your pet\'s name:', 'Mochi');
                    if (name) {
                      try {
                        await createPet({ name, species: 'cat' });
                        alert('Pet created! Welcome to Machi Quest!');
                      } catch (err) {
                        alert(err + 'Failed to create pet. Please try again.');
                      }
                    }
                  }}
                  disabled={petLoading}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {petLoading ? 'Creating...' : 'Create Your First Pet'}
                </Button>
                <div className="pt-4 border-t">
                  <p className="text-sm text-neutral-600 mb-2">Next steps:</p>
                  <ol className="space-y-2 list-decimal list-inside text-sm text-neutral-700">
                    <li>Create your first virtual pet companion</li>
                    <li>Connect your productivity tools (GitHub, etc.)</li>
                    <li>Set up your first goal</li>
                    <li>Start tracking your progress and watch your pet grow!</li>
                  </ol>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
