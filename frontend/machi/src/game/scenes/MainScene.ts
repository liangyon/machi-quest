import { Scene } from 'phaser';
import type { PetState } from '@/types/pet.types';

export class MainScene extends Scene {
  private pet?: Phaser.GameObjects.Sprite;
  private petState?: PetState;
  private background?: Phaser.GameObjects.Rectangle;
  
  // Constants
  private readonly PET_INITIAL_SCALE = 1;
  private readonly CLICK_ANIMATION_DURATION = 100;

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

    // Create placeholder pet (replace with actual sprite later)
    this.createPet();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Load initial data from React
    this.handleDataUpdate();
  }

  private createPet() {
    // Create a visible placeholder until sprites are loaded
    const graphics = this.add.graphics({ x: 0, y: 0 });
    graphics.fillStyle(0x4a90e2, 1);
    graphics.fillCircle(0, 0, 50);
    graphics.setName('petGraphics');
    
    // Create sprite (will be invisible until texture loaded)
    this.pet = this.add.sprite(
      this.scale.width / 2,
      this.scale.height / 2,
      ''
    );
    this.pet.setScale(this.PET_INITIAL_SCALE);
    this.pet.setData('graphics', graphics); // Link graphics to pet for easy repositioning
    
    // Make interactive
    this.pet.setInteractive({ useHandCursor: true });
    this.pet.on('pointerdown', this.onPetClick, this);
    this.pet.on('pointerover', () => this.pet?.setTint(0xcccccc));
    this.pet.on('pointerout', () => this.pet?.clearTint());
    
    // Position graphics with pet
    graphics.setPosition(this.pet.x, this.pet.y);
  }

  private setupEventListeners() {
    // Listen for data updates from React
    this.game.events.on('dataUpdated', this.handleDataUpdate, this);
    
    // Handle window resize
    this.scale.on('resize', this.handleResize, this);
  }

  private handleDataUpdate() {
    const petData = this.registry.get('petData') as PetState | undefined;
    if (petData) {
      this.petState = petData;
      this.updatePetDisplay();
    }
  }

  private updatePetDisplay() {
    if (!this.pet || !this.petState) return;

    // Update pet appearance based on state
    // TODO: Change sprite/animation based on mood, hunger, etc.
    
    // Example: Scale based on energy
    const scale = 0.5 + (this.petState.energy / 200);
    this.pet.setScale(scale);
  }

  private onPetClick() {
    // Emit action to React
    this.game.events.emit('gameAction', 'petClicked', {
      timestamp: Date.now(),
    });

    // Play click animation
    if (this.pet) {
      this.tweens.add({
        targets: this.pet,
        scaleX: this.pet.scaleX * 1.1,
        scaleY: this.pet.scaleY * 1.1,
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

    if (this.pet) {
      const newX = gameSize.width / 2;
      const newY = gameSize.height / 2;
      
      this.pet.setPosition(newX, newY);
      
      // Also reposition the graphics placeholder
      const graphics = this.pet.getData('graphics') as Phaser.GameObjects.Graphics;
      if (graphics) {
        graphics.setPosition(newX, newY);
      }
    }
  }

  update(time: number, delta: number) {
    // Game loop - update animations, physics, etc.
  }

  shutdown() {
    // Cleanup
    this.game.events.off('dataUpdated', this.handleDataUpdate, this);
    this.scale.off('resize', this.handleResize, this);
  }
}
