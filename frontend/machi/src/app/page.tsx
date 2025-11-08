'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Zap, Target, Trophy } from 'lucide-react';

export default function HeroPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-neutral-200">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="flex flex-col items-center justify-center text-center space-y-8 max-w-4xl mx-auto">
          {/* Logo/Title */}
          <div className="space-y-4">
            <h1 className="text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-neutral-900 to-neutral-600">
              Machi Quest
            </h1>
            <p className="text-xl text-neutral-600 max-w-2xl">
              Transform your productivity into an adventure. Track your goals, grow your productivity garden, and watch your achievements bloom.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex gap-4 flex-wrap justify-center">
            <Button asChild size="lg" className="text-lg px-8">
              <Link href="/auth">Get Started</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="text-lg px-8">
              <Link href="/dashboard">Go to Dashboard</Link>
            </Button>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 w-full">
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Track Goals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Set and track your productivity goals with our powerful quest system. Turn your daily tasks into exciting missions.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Earn Rewards
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Complete quests to earn experience points and rewards. Watch your goals flourish as you make progress towards your targets.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  Level Up
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Progress through levels and unlock new features. Compete with friends and celebrate your achievements.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-16 border-t">
        <div className="flex justify-center text-sm text-neutral-500">
          <p>&copy; 2025 Machi Quest. Start your productivity adventure today.</p>
        </div>
      </footer>
    </div>
  );
}
