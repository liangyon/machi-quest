'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { setAccessToken, getAccessToken } from '@/libs/axios';
import type { User } from '@/types/user.types';

import { authApi } from '@/libs/api/authApi';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const token = getAccessToken();
      
      if (!token) {
        // No token in memory, try to refresh from httpOnly cookie
        try {
          await authApi.refreshToken();
        } catch {
          // No valid refresh token
          setUser(null);
          return;
        }
      }

      // Fetch user data
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to restore session:', error);
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  // Load user on mount - try to restore session from httpOnly cookie
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      await refreshUser();
      setIsLoading(false);
    };

    initAuth();
  }, [refreshUser]);



  const login = useCallback(async (email: string, password: string) => {
    try {
      await authApi.login(email, password);
      
      await refreshUser();
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }, [refreshUser]);




  const signup = useCallback(async (email: string, password: string, displayName?: string) => {
    try {
      await authApi.signup(
        email,
        password,
        displayName);

      await refreshUser();
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  }, [refreshUser]);

  const logout = useCallback(async () => {
    try {
      // Backend will clear the httpOnly refresh token cookie
      await authApi.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      // Clear in-memory access token
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
