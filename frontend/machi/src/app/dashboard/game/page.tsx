'use client';
import dynamic from 'next/dynamic';

const PhaserGame = dynamic(() => import('@/components/PhaserGame').then(mod => mod.PhaserGame), {
  ssr: false,
  loading: () =>(
    <div>

    </div>
  )
});

export default function GamePage() {
  return (
    <div className="fixed inset-0 z-0">
      <PhaserGame />
    </div>
  );
}
