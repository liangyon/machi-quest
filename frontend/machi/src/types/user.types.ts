/**
 * User-related types and interfaces
 */

export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  github_username?: string;
  google_id?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  display_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
