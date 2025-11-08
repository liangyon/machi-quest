'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { goalApi } from '@/lib/api/goalApi';
import type { Goal, GoalCreate, GoalUpdate, GoalStats } from '@/types/goal.types';

interface GoalContextType {
  goals: Goal[];
  activeGoals: Goal[];
  currentGoal: Goal | null;
  stats: GoalStats | null;
  isLoading: boolean;
  error: string | null;
  createGoal: (goalData: GoalCreate) => Promise<Goal>;
  updateGoal: (goalId: string, goalUpdate: GoalUpdate) => Promise<Goal>;
  deleteGoal: (goalId: string) => Promise<void>;
  crownGoal: (goalId: string) => Promise<Goal>;
  selectGoalById: (goalId: string) => void;
  refreshGoals: () => Promise<void>;
}

const GoalContext = createContext<GoalContextType | undefined>(undefined);

export function GoalProvider({ children }: { children: React.ReactNode }) {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [activeGoals, setActiveGoals] = useState<Goal[]>([]);
  const [currentGoalId, setCurrentGoalId] = useState<string | null>(null);
  const [stats, setStats] = useState<GoalStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { isAuthenticated } = useAuth();
  
  // Derived state - no sync issues
  const currentGoal = goals.find(g => g.id === currentGoalId) ?? null;

  // Load goals on auth
  const loadGoals = useCallback(async () => {
    if (!isAuthenticated) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      // Load all goals and active goals in parallel
      const [allGoalsData, activeGoalsData, statsData] = await Promise.all([
        goalApi.getAll(),
        goalApi.getActive(),
        goalApi.getStats()
      ]);
      
      setGoals(allGoalsData);
      setActiveGoals(activeGoalsData);
      setStats(statsData);
      
      // Auto-select first active goal if none selected
      if (activeGoalsData.length > 0 && !currentGoalId) {
        setCurrentGoalId(activeGoalsData[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load goals');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, currentGoalId]);

  useEffect(() => {
    loadGoals();
  }, [isAuthenticated]); // Only run on auth change, not on currentGoalId change

  // Create goal
  const createGoal = useCallback(async (goalData: GoalCreate): Promise<Goal> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const newGoal = await goalApi.create(goalData);
      
      setGoals(prev => {
        const updated = [...prev, newGoal];
        // Set as current if first goal
        if (prev.length === 0) {
          setCurrentGoalId(newGoal.id);
        }
        return updated;
      });
      
      // Refresh active goals and stats
      await loadGoals();
      
      return newGoal;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create goal';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadGoals]);

  // Update goal
  const updateGoal = useCallback(async (goalId: string, goalUpdate: GoalUpdate): Promise<Goal> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const updated = await goalApi.update(goalId, goalUpdate);
      setGoals(prev => prev.map(g => g.id === goalId ? updated : g));
      
      // Refresh active goals and stats
      await loadGoals();
      
      return updated;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update goal';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadGoals]);

  // Crown goal
  const crownGoal = useCallback(async (goalId: string): Promise<Goal> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const crowned = await goalApi.crown(goalId);
      setGoals(prev => prev.map(g => g.id === goalId ? crowned : g));
      
      // Refresh active goals and stats
      await loadGoals();
      
      return crowned;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to crown goal';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [loadGoals]);

  // Delete goal
  const deleteGoal = useCallback(async (goalId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await goalApi.delete(goalId);
      
      setGoals(prev => {
        const filtered = prev.filter(g => g.id !== goalId);
        // Switch to first goal if current was deleted
        if (currentGoalId === goalId && filtered.length > 0) {
          setCurrentGoalId(filtered[0].id);
        } else if (filtered.length === 0) {
          setCurrentGoalId(null);
        }
        return filtered;
      });
      
      // Refresh active goals and stats
      await loadGoals();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete goal';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [currentGoalId, loadGoals]);

  // Select goal
  const selectGoalById = useCallback((goalId: string) => {
    if (goals.some(g => g.id === goalId)) {
      setCurrentGoalId(goalId);
    }
  }, [goals]);

  const value: GoalContextType = {
    goals,
    activeGoals,
    currentGoal,
    stats,
    isLoading,
    error,
    createGoal,
    updateGoal,
    deleteGoal,
    crownGoal,
    selectGoalById,
    refreshGoals: loadGoals,
  };

  return <GoalContext.Provider value={value}>{children}</GoalContext.Provider>;
}

export function useGoal() {
  const context = useContext(GoalContext);
  if (!context) {
    throw new Error('useGoal must be used within a GoalProvider');
  }
  return context;
}
