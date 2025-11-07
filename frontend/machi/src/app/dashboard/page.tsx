'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { usePet } from '@/contexts/PetContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Heart, Zap, Utensils } from 'lucide-react';

export default function DashboardPage() {
  const { user, isLoading, isAuthenticated } = useAuth();
  const { pets, createPet, isLoading: petLoading } = usePet();
  const router = useRouter();

  useEffect(() => {
    // Redirect to auth page if not authenticated
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleCreatePet = async () => {
    try {
      await createPet({
        name: `Pet ${pets.length + 1}`,
        species: 'default',
      });
    } catch (error) {
      console.error('Failed to create pet:', error);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900"></div>
      </div>
    );
  }

  // Don't render content if not authenticated (will redirect)
  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold mb-2">
          Welcome back, {user.display_name || 'Adventurer'}!
        </h1>
        <p className="text-neutral-600">
          Manage your pets and track your productivity journey.
        </p>
      </div>

      {/* Pets Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Your Pets</h2>
          <Button onClick={handleCreatePet} disabled={petLoading}>
            <Plus className="w-4 h-4 mr-2" />
            Create Pet
          </Button>
        </div>

        {petLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neutral-900"></div>
          </div>
        ) : pets.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-neutral-600 mb-4">You don&apos;t have any pets yet.</p>
              <Button onClick={handleCreatePet}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Pet
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pets.map((pet) => (
              <Card key={pet.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle>{pet.name}</CardTitle>
                  <CardDescription>Level {pet.state_json.level}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Pet Stats */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1">
                        <Heart className="w-4 h-4 text-red-500" />
                        Health
                      </span>
                      <span className="font-medium">{pet.state_json.health}/100</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-red-500 h-2 rounded-full transition-all"
                        style={{ width: `${pet.state_json.health}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1">
                        <Zap className="w-4 h-4 text-yellow-500" />
                        Energy
                      </span>
                      <span className="font-medium">{pet.state_json.energy}/100</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-yellow-500 h-2 rounded-full transition-all"
                        style={{ width: `${pet.state_json.energy}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1">
                        <Utensils className="w-4 h-4 text-green-500" />
                        Hunger
                      </span>
                      <span className="font-medium">{pet.state_json.hunger}/100</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all"
                        style={{ width: `${pet.state_json.hunger}%` }}
                      />
                    </div>
                  </div>

                  {/* XP Progress */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span>XP</span>
                      <span className="text-xs text-neutral-500">
                        {pet.state_json.xp}/{pet.state_json.xp_to_next_level}
                      </span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{
                          width: `${(pet.state_json.xp / pet.state_json.xp_to_next_level) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pets.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quests Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Achievements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Streak</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0 days</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
