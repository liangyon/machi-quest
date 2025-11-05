'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity } from 'lucide-react';

export default function ActivityPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Activity</h1>
        <p className="text-neutral-600">
          Track your productivity activity and integration events.
        </p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Activity Feed
          </CardTitle>
          <CardDescription>
            View your recent activity, completed tasks, and integration events
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[300px] flex items-center justify-center bg-neutral-50">
          <div className="text-center">
            <Activity className="w-16 h-16 mx-auto mb-4 text-neutral-400" />
            <p className="text-neutral-500">Activity timeline placeholder</p>
            <p className="text-sm text-neutral-400 mt-2">
              Activity tracking and event history will be here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
