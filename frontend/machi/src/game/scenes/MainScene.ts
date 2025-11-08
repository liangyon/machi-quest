import { Scene } from 'phaser';
import type { Goal } from '@/types/goal.types';

export class MainScene extends Scene {
  private goalSprite?: Phaser.GameObjects.Sprite;
  private currentGoal?: Goal;
  private background?: Phaser.GameObjects.Rectangle;
  
  // Constants
  private readonly GOAL_INITIAL_SCALE = 1;

  constructor() {
    super({ key: 'MainScene' });
  }

  init() {
    // Initialize scene data (called before preload)
  }

  preload() {

  }

  create() {
    // Create background
    this.background = this.add.rectangle(
      0,
      0,
      this.scale.width,
      this.scale.height,
      0xC1E1C1
    );
    this.background.setOrigin(0, 0);

    // Create placeholder goal visual (replace with actual sprite later)
    this.createGoalVisual();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Load initial data from React
    this.handleDataUpdate();
  }

  private createGoalVisual() {
    // Create a visible placeholder until sprites are loaded
    const graphics = this.add.graphics({ x: 0, y: 0 });
    graphics.fillStyle(0x4a90e2, 1);
    graphics.fillCircle(0, 0, 50);
    graphics.setName('goalGraphics');
    
    // Create sprite (will be invisible until texture loaded)
    this.goalSprite = this.add.sprite(
      this.scale.width / 2,
      this.scale.height / 2,
      ''
    );
    this.goalSprite.setScale(this.GOAL_INITIAL_SCALE);
    this.goalSprite.setData('graphics', graphics); // Link graphics to goal for easy repositioning
    
    // Make interactive
    this.goalSprite.setInteractive({ useHandCursor: true });
    this.goalSprite.on('pointerdown', this.onGoalClick, this);
    this.goalSprite.on('pointerover', () => this.goalSprite?.setTint(0xcccccc));
    this.goalSprite.on('pointerout', () => this.goalSprite?.clearTint());
    
    // Position graphics with goal
    graphics.setPosition(this.goalSprite.x, this.goalSprite.y);
  }

  private setupEventListeners() {
    // Listen for data updates from React
    this.game.events.on('dataUpdated', this.handleDataUpdate, this);
    
    // Handle window resize
    this.scale.on('resize', this.handleResize, this);
  }

  private handleDataUpdate() {
    const goalData = this.registry.get('goalData') as Goal | undefined;
    if (goalData) {
      this.currentGoal = goalData;
      this.updateGoalDisplay();
    }
  }

  private updateGoalDisplay() {
    if (!this.goalSprite || !this.currentGoal) return;

    // Update goal appearance based on state
    // TODO: Change sprite/animation based on growth stage, progress, etc.
    
    // Example: Scale based on growth stage (0-3: Baby, Teen, Adult, Crowned)
    const baseScale = 0.5;
    const scaleIncrement = 0.25;
    const scale = baseScale + (this.currentGoal.growth_stage * scaleIncrement);
    this.goalSprite.setScale(scale);
    
    // Update graphics color based on progress
    const graphics = this.goalSprite.getData('graphics') as Phaser.GameObjects.Graphics;
    if (graphics) {
      graphics.clear();
      
      // Color changes with progress
      const progressPercent = this.currentGoal.current_progress / this.currentGoal.target_value;
      let color = 0x4a90e2; // Blue
      
      if (progressPercent >= 1) {
        color = 0x4caf50; // Green (completed)
      } else if (progressPercent >= 0.75) {
        color = 0x8bc34a; // Light green
      } else if (progressPercent >= 0.5) {
        color = 0xffc107; // Amber
      }
      
      if (this.currentGoal.is_crowned) {
        color = 0xffd700; // Gold
      }
      
      graphics.fillStyle(color, 1);
      graphics.fillCircle(0, 0, 50);
    }
  }

  private onGoalClick() {
    // Emit action to React
    this.game.events.emit('gameAction', 'goalClicked', {
      timestamp: Date.now(),
      goalId: this.currentGoal?.id,
    });

    // Play click animation
    if (this.goalSprite) {
      this.tweens.add({
        targets: this.goalSprite,
        scaleX: this.goalSprite.scaleX * 1.1,
        scaleY: this.goalSprite.scaleY * 1.1,
        duration: 100,
        yoyo: true,
      });
    }
  }

  private handleResize(gameSize: Phaser.Structs.Size) {
    // Reposition elements on resize
    if (this.background) {
      this.background.setSize(gameSize.width, gameSize.height);
    }

    if (this.goalSprite) {
      const newX = gameSize.width / 2;
      const newY = gameSize.height / 2;
      
      this.goalSprite.setPosition(newX, newY);
      
      // Also reposition the graphics placeholder
      const graphics = this.goalSprite.getData('graphics') as Phaser.GameObjects.Graphics;
      if (graphics) {
        graphics.setPosition(newX, newY);
      }
    }
  }

  update(_time: number, _delta: number) {
    // Game loop - update animations, physics, etc.
  }

  shutdown() {
    // Cleanup
    this.game.events.off('dataUpdated', this.handleDataUpdate, this);
    this.scale.off('resize', this.handleResize, this);
  }
}
