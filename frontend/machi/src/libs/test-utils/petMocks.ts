import type { Pet, PetState } from '@/types/pet.types';



export const createMockPetState = (): PetState => ({
    energy: 100,
    hunger: 20,
    happiness: 80,
    health: 100,
    level: 1,
    xp: 0,
    xp_to_next_level: 100,
    mood: 'content',
    status_effects: [],
    skills: {
        coding: { name: 'Coding', level: 1, xp: 0 },
        fitness: { name: 'Fitness', level: 1, xp: 0 },
    },
    appearance: {
        color: 'blue',
        pattern: 'spots',
        accessories: [],
        size_modifier: 1.0,
    },
    inventory: [],
    stats: {
        strength: 10,
        intelligence: 10,
        agility: 10,
        endurance: 10,
        charisma: 10,
    },
    achievements: [],
    total_events_completed: 0,
    total_time_played_minutes: 0,
    bond_level: 1,
    bond_xp: 0,
    traits: {},
    daily_login_streak: 0,
});


export const createMockPet = (overrides: Partial<Pet> = {}): Pet => ({
  id: 'mock-pet-id',
  user_id: 'mock-user-id',
  name: 'Mochi',
  species: 'cat',
  description: 'A friendly productivity',
  state_json: createMockPetState(),
  version: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});