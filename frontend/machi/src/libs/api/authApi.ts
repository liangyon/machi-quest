import axiosInstance, { setAccessToken } from "../axios";
import type { User } from "@/types/user.types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const authApi = {
    async login(email: string, password: string) {
        const { data } = await axiosInstance.post('/api/v1/auth/login', {
            email,
            password,
        });
        setAccessToken(data.access_token);
        return data;
    },

    async signup(email: string, password: string, displayName?: string) {
        const { data } = await axiosInstance.post('/api/v1/auth/signup', {
            email,
            password,
            display_name: displayName,
        });
        setAccessToken(data.access_token);
        return data;
    },

    async logout() {
        await axiosInstance.post('/api/v1/auth/logout');
        setAccessToken(null);
    },

    async refreshToken() {
        const { data } = await axiosInstance.post('/api/v1/auth/refresh');
        setAccessToken(data.access_token);
        return data;
    },

    async getCurrentUser(): Promise<User> {
        const { data } = await axiosInstance.get<User>('/api/v1/users/me');
        return data;
    },

    getGitHubLoginURL(): string {
    return `${API_BASE_URL}/api/v1/auth/github/login`;
  },
}