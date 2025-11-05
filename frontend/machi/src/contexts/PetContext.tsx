'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { petApi } from '@/lib/api/petApi';
import type { Pet, PetCreate, PetUpdate } from '@/types/pet.types';

interface PetContextType {
  pets: Pet[];
  currentPet: Pet | null;
  isLoading: boolean;
  error: string | null;
  createPet: (petData: PetCreate) => Promise<Pet>;
  updatePet: (petId: string, petUpdate: PetUpdate) => Promise<Pet>;
  deletePet: (petId: string) => Promise<void>;
  selectPetById: (petId: string) => void;
}

const PetContext = createContext<PetContextType | undefined>(undefined);

export function PetProvider({ children }: { children: React.ReactNode }) {
  const [pets, setPets] = useState<Pet[]>([]);
  const [currentPetId, setCurrentPetId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { isAuthenticated } = useAuth();
  
  // Derived state - no sync issues
  const currentPet = pets.find(p => p.id === currentPetId) ?? null;

  // Load pets on auth
  useEffect(() => {
    if (!isAuthenticated) return;
    
    const loadPets = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const data = await petApi.getAll();
        setPets(data);
        
        // Auto-select first pet if none selected
        if (data.length > 0 && !currentPetId) {
          setCurrentPetId(data[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load pets');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadPets();
  }, [isAuthenticated, currentPetId]);

  // Create pet
  const createPet = useCallback(async (petData: PetCreate): Promise<Pet> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const newPet = await petApi.create(petData);
      
      setPets(prev => {
        const updated = [...prev, newPet];
        // Set as current if first pet
        if (prev.length === 0) {
          setCurrentPetId(newPet.id);
        }
        return updated;
      });
      
      return newPet;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create pet';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Update pet
  const updatePet = useCallback(async (petId: string, petUpdate: PetUpdate): Promise<Pet> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const updated = await petApi.update(petId, petUpdate);
      setPets(prev => prev.map(p => p.id === petId ? updated : p));
      
      return updated;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update pet';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Delete pet
  const deletePet = useCallback(async (petId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await petApi.delete(petId);
      
      setPets(prev => {
        const filtered = prev.filter(p => p.id !== petId);
        // Switch to first pet if current was deleted
        if (currentPetId === petId && filtered.length > 0) {
          setCurrentPetId(filtered[0].id);
        } else if (filtered.length === 0) {
          setCurrentPetId(null);
        }
        return filtered;
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete pet';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [currentPetId]);

  // Select pet
  const selectPetById = useCallback((petId: string) => {
    if (pets.some(p => p.id === petId)) {
      setCurrentPetId(petId);
    }
  }, [pets]);

  const value: PetContextType = {
    pets,
    currentPet,
    isLoading,
    error,
    createPet,
    updatePet,
    deletePet,
    selectPetById,
  };

  return <PetContext.Provider value={value}>{children}</PetContext.Provider>;
}

export function usePet() {
  const context = useContext(PetContext);
  if (!context) {
    throw new Error('usePet must be used within a PetProvider');
  }
  return context;
}
