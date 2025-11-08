'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useGoal } from '@/contexts/GoalContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Target, TrendingUp, Award, Crown } from 'lucide-react';

export default function DashboardPage() {
  const { user, isLoading, isAuthenticated } = useAuth();
  const { goals, activeGoals, stats, createGoal, isLoading: goalLoading } = useGoal();
  const router = useRouter();

  useEffect(() => {
    // Redirect to auth page if not authenticated
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleCreateGoal = async () => {
    try {
      await createGoal({
        name: `Goal ${goals.length + 1}`,
        goal_type: 'short_term',
        target_value: 10,
        tracking_type: 'numeric',
        unit: 'tasks',
      });
    } catch (error) {
      console.error('Failed to create goal:', error);
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

  const getProgressPercentage = (current: number, target: number) => {
    return Math.min(100, (current / target) * 100);
  };

  const getGrowthStageLabel = (stage: number) => {
    const stages = ['Baby', 'Teen', 'Adult', 'Crowned'];
    return stages[stage] || 'Unknown';
  };

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold mb-2">
          Welcome back, {user.display_name || 'Adventurer'}!
        </h1>
        <p className="text-neutral-600">
          Track your goals and watch your productivity garden grow.
        </p>
      </div>

      {/* Quick Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Goals</CardTitle>
              <Target className="h-4 w-4 text-neutral-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_goals}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Goals</CardTitle>
              <TrendingUp className="h-4 w-4 text-neutral-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_goals}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <Award className="h-4 w-4 text-neutral-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.completed_goals}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
              <Crown className="h-4 w-4 text-neutral-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.current_streak} days</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Goals Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Your Goals</h2>
          <Button onClick={handleCreateGoal} disabled={goalLoading}>
            <Plus className="w-4 h-4 mr-2" />
            Create Goal
          </Button>
        </div>

        {goalLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neutral-900"></div>
          </div>
        ) : goals.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-neutral-600 mb-4">You don&apos;t have any goals yet.</p>
              <Button onClick={handleCreateGoal}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Goal
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {goals.map((goal) => (
              <Card key={goal.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center gap-2">
                        {goal.name}
                        {goal.is_crowned && <Crown className="w-4 h-4 text-yellow-500" />}
                      </CardTitle>
                      <CardDescription className="capitalize">
                        {goal.goal_type.replace('_', ' ')} • {goal.integration_source}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Progress */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1">
                        <Target className="w-4 h-4 text-blue-500" />
                        Progress
                      </span>
                      <span className="font-medium">
                        {goal.current_progress}/{goal.target_value} {goal.unit || 'pts'}
                      </span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{
                          width: `${getProgressPercentage(goal.current_progress, goal.target_value)}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Growth Stage */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-600">Growth Stage</span>
                    <span className="font-medium">{getGrowthStageLabel(goal.growth_stage)}</span>
                  </div>

                  {/* Medallions */}
                  {goal.total_medallions_produced > 0 && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600">Medallions</span>
                      <span className="font-medium flex items-center gap-1">
                        <Award className="w-4 h-4 text-yellow-500" />
                        {goal.total_medallions_produced}
                      </span>
                    </div>
                  )}

                  {/* Status Badges */}
                  <div className="flex gap-2">
                    {goal.is_completed && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Completed
                      </span>
                    )}
                    {goal.is_crowned && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Crowned
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
