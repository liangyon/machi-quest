'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-neutral-600">
          Manage your account settings and preferences.
        </p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Settings Panel
          </CardTitle>
          <CardDescription>
            Configure your account, notifications, and integrations
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[300px] flex items-center justify-center bg-neutral-50">
          <div className="text-center">
            <Settings className="w-16 h-16 mx-auto mb-4 text-neutral-400" />
            <p className="text-neutral-500">Settings interface placeholder</p>
            <p className="text-sm text-neutral-400 mt-2">
              User settings and configuration will be here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
