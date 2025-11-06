import { Scene } from 'phaser';
import type { PetState } from '@/types/pet.types';

export class UIScene extends Scene {
  private statsText?: Phaser.GameObjects.Text;
  private petState?: PetState;

  constructor() {
    super({ key: 'UIScene' });
  }

  create() {
    // Create UI elements (runs parallel to MainScene)
    this.createStatsDisplay();

    // Listen for data updates from React
    this.game.events.on('dataUpdated', this.handleDataUpdate, this);
    
    // Load initial data
    this.handleDataUpdate();
  }

  private createStatsDisplay() {
    // Stats panel in top-left corner
    const padding = 20;
    
    this.statsText = this.add.text(padding, padding, '', {
      fontSize: '16px',
      color: '#333333',
      backgroundColor: '#ffffff',
      padding: { x: 12, y: 8 },
      align: 'left',
    });
    
    this.statsText.setScrollFactor(0); // Fixed to camera
    this.statsText.setDepth(1000); // Always on top
  }

  private handleDataUpdate() {
    const petData = this.registry.get('petData') as PetState | undefined;
    if (petData) {
      this.petState = petData;
      this.updateStatsDisplay();
    }
  }

  private updateStatsDisplay() {
    if (!this.statsText || !this.petState) return;

    const stats = [
      `Level: ${this.petState.level}`,
      `HP: ${this.petState.health}/100`,
      `Energy: ${this.petState.energy}/100`,
      `Hunger: ${this.petState.hunger}/100`,
      `Mood: ${this.petState.mood}`,
    ];

    this.statsText.setText(stats.join('\n'));
  }

  shutdown() {
    this.game.events.off('dataUpdated', this.handleDataUpdate, this);
  }
}
