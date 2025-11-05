'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Target } from 'lucide-react';

export default function QuestsPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Quests</h1>
        <p className="text-neutral-600">
          Track your goals and complete quests to earn rewards.
        </p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Quest System
          </CardTitle>
          <CardDescription>
            View active quests, daily challenges, and long-term goals
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[300px] flex items-center justify-center bg-neutral-50">
          <div className="text-center">
            <Target className="w-16 h-16 mx-auto mb-4 text-neutral-400" />
            <p className="text-neutral-500">Quest interface placeholder</p>
            <p className="text-sm text-neutral-400 mt-2">
              Quest tracking and management will be here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
