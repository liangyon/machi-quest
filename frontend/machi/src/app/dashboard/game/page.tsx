'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Gamepad2 } from 'lucide-react';

export default function GamePage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Game</h1>
        <p className="text-neutral-600">
          Interact with your virtual pets and explore the game world.
        </p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gamepad2 className="w-5 h-5" />
            Game Canvas
          </CardTitle>
          <CardDescription>
            This is where your Phaser game graphics will be displayed
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[400px] flex items-center justify-center bg-neutral-50">
          <div className="text-center">
            <Gamepad2 className="w-16 h-16 mx-auto mb-4 text-neutral-400" />
            <p className="text-neutral-500">Game canvas placeholder</p>
            <p className="text-sm text-neutral-400 mt-2">
              Phaser game will be integrated here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
