/**
 * Game event types for React <-> Phaser communication
 */

export interface GameAction {
  action: string;
  data: any;
}

export interface PetClickedEvent {
  timestamp: number;
}

export interface FeedPetEvent {
  petId: string;
  foodItem: string;
}

export interface PlayWithPetEvent {
  petId: string;
  activity: string;
}

/**
 * Type map for game actions
 */
export type GameActionMap = {
  petClicked: PetClickedEvent;
  feedPet: FeedPetEvent;
  playWithPet: PlayWithPetEvent;
};

export type GameActionType = keyof GameActionMap;
