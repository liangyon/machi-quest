
export type MoodType = 'happy' | 'content' | 'neutral' | 'tired' | 'hungry' | 'sad' | 'excited';

export interface PetSkill {
  name: string;
  level: number;
  xp: number;
}

export interface PetAppearance {
  color: string;
  pattern?: string;
  accessories: string[];
  size_modifier: number;
}

export interface PetInventoryItem {
  item_id: string;
  quantity: number;
  equipped: boolean;
}

export interface PetStats {
  strength: number;
  intelligence: number;
  agility: number;
  endurance: number;
  charisma: number;
}

export interface PetState {
  // Basic vitals
  energy: number;
  hunger: number;
  happiness: number;
  health: number;
  

  level: number;
  xp: number;
  xp_to_next_level: number;
  

  mood: MoodType;
  status_effects: string[];
  

  skills: Record<string, PetSkill>;
  

  appearance: PetAppearance;
  
  // Inventory
  inventory: PetInventoryItem[];
  

  stats: PetStats;
  

  achievements: string[];
  total_events_completed: number;
  total_time_played_minutes: number;
  
  // Activity tracking
  last_event_id?: string;
  last_fed_at?: string;
  last_played_at?: string;
  last_update?: string;
  
  // Relationship
  bond_level: number;
  bond_xp: number;
  
  // Custom traits
  traits: Record<string, any>;
  
  // Streaks
  daily_login_streak: number;
  last_login_date?: string;
}


export interface Pet {
  id: string;
  user_id: string;
  name: string;
  species: string;
  description?: string;
  state_json: PetState;
  version: number;
  created_at: string;
  updated_at: string;
}


export interface PetCreate {
  name?: string;
  species?: string;
  description?: string;
}

export interface PetUpdate {
  name?: string;
  species?: string;
  description?: string;
  state_json?: PetState;
}

export interface PetStatsResponse {
  pet_id: string;
  name: string;
  species: string;
  level: number;
  xp: number;
  health: number;
  energy: number;
  happiness: number;
  bond_level: number;
  total_events_completed: number;
  achievements_count: number;
  mood: MoodType;
}

export interface PetFeedRequest {
  food_item: string;
  quantity?: number;
}

export interface PetPlayRequest {
  activity: string;
  duration_minutes?: number;
}
