export const createGameConfig = async () => {
  const { MainScene } = await import('./scenes/MainScene');
  const { UIScene } = await import('./scenes/UIScene');

  return {
    type: 0, // Phaser.AUTO
    parent: 'phaser-game',
    backgroundColor: '#f5f5f5',
  scale: {
    mode: 2, // Phaser.Scale.RESIZE - canvas resizes to match parent
    parent: 'phaser-game',
    width: '100%',
    height: '100%',
    autoCenter: 1, // Phaser.Scale.CENTER_BOTH
  },
    physics: {
      default: 'arcade',
      arcade: {
        gravity: { x: 0, y: 0 }, // No gravity for top-down view
        debug: process.env.NODE_ENV === 'development',
      },
    },
    scene: [MainScene, UIScene],
    dom: {
      createContainer: true,
    },
    fps: {
      target: 60,
      forceSetTimeOut: false,
    },
    // Performance optimizations
    render: {
      pixelArt: false,
      antialias: true,
      roundPixels: false,
    },
    // Better for React integration
    disableContextMenu: true,
  };
};
