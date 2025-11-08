import { Scene } from 'phaser';
import type { Goal } from '@/types/goal.types';

export class UIScene extends Scene {
  private statsText?: Phaser.GameObjects.Text;
  private currentGoal?: Goal;

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
    const goalData = this.registry.get('goalData') as Goal | undefined;
    if (goalData) {
      this.currentGoal = goalData;
      this.updateStatsDisplay();
    }
  }

  private updateStatsDisplay() {
    if (!this.statsText || !this.currentGoal) return;

    const progressPercent = Math.round(
      (this.currentGoal.current_progress / this.currentGoal.target_value) * 100
    );

    const stats = [
      `Goal: ${this.currentGoal.name}`,
      `Progress: ${this.currentGoal.current_progress}/${this.currentGoal.target_value} ${this.currentGoal.unit || ''}`,
      `${progressPercent}% Complete`,
      `Stage: ${this.currentGoal.growth_stage}/5`,
      `Type: ${this.currentGoal.goal_type}`,
    ];

    if (this.currentGoal.is_crowned) {
      stats.push('👑 CROWNED');
    }

    this.statsText.setText(stats.join('\n'));
  }

  shutdown() {
    this.game.events.off('dataUpdated', this.handleDataUpdate, this);
  }
}
