'use client';

import { useEffect, useRef, useCallback } from 'react';
import { createGameConfig } from '@/game/config';
import { usePet } from '@/contexts/PetContext';
import { useAuth } from '@/contexts/AuthContext';

export function PhaserGame() {
  const gameRef = useRef<any>(null);
  const { currentPet } = usePet();
  const { user } = useAuth();

  // Handle actions from Phaser
  const handleGameAction = useCallback((action: string, data: any) => {
    console.log('Game action:', action, data);
    
    switch (action) {
      case 'petClicked':
        // Handle pet click
        console.log('Pet was clicked at', data.timestamp);
        break;
      case 'feedPet':
        // Call API to feed pet
        break;
      case 'playWithPet':
        // Call API to play with pet
        break;
      default:
        console.warn('Unknown game action:', action);
    }
  }, []);

  // Initialize Phaser game (only once)
  useEffect(() => {
    if (typeof window === 'undefined') return; // SSR guard
    if (gameRef.current) return; // Prevent double initialization

    // Dynamically import Phaser to avoid SSR issues
    const initGame = async () => {
      const container = document.getElementById('phaser-game');
      if (!container || container.offsetWidth === 0) {
        // Container not ready, retry
        setTimeout(initGame, 100);
        return;
      }
      
      const Phaser = await import('phaser');
      const config = await createGameConfig();
      
      gameRef.current = new Phaser.Game(config);
      
      // Force immediate resize after init
      setTimeout(() => {
        gameRef.current?.scale.resize(
          container.offsetWidth,
          container.offsetHeight
        );
      }, 100);
    };

    initGame();

    // Cleanup on unmount
    return () => {
      if (gameRef.current) {
        // gameRef.current.events.off('gameAction', handleGameAction);
        gameRef.current.destroy(true);
        gameRef.current = null;
      }
    };
  }, []); // Empty deps - only run once

  // Update event handler separately when it changes
  useEffect(() => {
    if (!gameRef.current) return;
    
    gameRef.current.events.off('gameAction', handleGameAction);
    gameRef.current.events.on('gameAction', handleGameAction);
  }, [handleGameAction]);

  // Send pet data to Phaser when it changes
  useEffect(() => {
    if (!gameRef.current || !currentPet) return;

    gameRef.current.registry.set('petData', currentPet.state_json);
    gameRef.current.registry.set('userData', user);
    gameRef.current.events.emit('dataUpdated');
  }, [currentPet, user]);

  // Handle visibility changes (pause when tab is hidden)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!gameRef.current) return;

      if (document.hidden) {
        // Pause game when tab is hidden
        gameRef.current.pause();
      } else {
        // Resume game when tab is visible
        gameRef.current.resume();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return (
    <div 
      id="phaser-game" 
      className="w-screen h-screen"
      style={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
      }}
    />
  );
}
