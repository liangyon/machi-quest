'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Trophy } from 'lucide-react';

export default function AchievementsPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Achievements</h1>
        <p className="text-neutral-600">
          View your unlocked achievements and track your progress.
        </p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="w-5 h-5" />
            Achievement Gallery
          </CardTitle>
          <CardDescription>
            Browse all achievements and see what you&apos;ve unlocked
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[300px] flex items-center justify-center bg-neutral-50">
          <div className="text-center">
            <Trophy className="w-16 h-16 mx-auto mb-4 text-neutral-400" />
            <p className="text-neutral-500">Achievements display placeholder</p>
            <p className="text-sm text-neutral-400 mt-2">
              Achievement tracking and rewards will be here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
