import axiosInstance, { setAccessToken } from "../axios";
import type { User } from "@/types/user.types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const authApi = {
    async login(email: string, password: string) {
        try {
            const { data } = await axiosInstance.post('/api/v1/auth/login', {
                email,
                password,
            });
            setAccessToken(data.access_token);
            return data;
        } catch (error: any) {
            throw new Error(extractErrorMessage(error));
        }
    },

    async signup(email: string, password: string, displayName?: string) {
        try {
            const { data } = await axiosInstance.post('/api/v1/auth/signup', {
                email,
                password,
                display_name: displayName,
            });
            setAccessToken(data.access_token);
            return data;
        } catch (error: any) {
            throw new Error(extractErrorMessage(error));
        }
    },

    async logout() {
        await axiosInstance.post('/api/v1/auth/logout');
        setAccessToken(null);
    },

    async refreshToken() {
        const { data } = await axiosInstance.post('/api/v1/auth/refresh', {}, {
            skipAuthRefresh: true  // Prevent interceptor from retrying on 401
        } as any);
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
};

/**
 * Extract user-friendly error message from API response
 */
function extractErrorMessage(error: any): string {
    // Handle 422 validation errors from FastAPI/Pydantic
    if (error.response?.status === 422) {
        const details = error.response.data?.detail;
        
        if (Array.isArray(details) && details.length > 0) {
            // Extract validation error messages
            const messages = details
                .map((err: any) => {
                    console.log(err)
                    return "something went wrong";
                })
                .filter(Boolean);
            
            if (messages.length > 0) {
                return messages.join('. ');
            }
        }
        
        return 'Invalid input. Please check your data and try again.';
    }
    
    // Handle other error responses
    if (error.response?.data?.detail) {
        return typeof error.response.data.detail === 'string'
            ? error.response.data.detail
            : 'An error occurred';
    }
    
    // Network or other errors
    if (error.message) {
        return error.message;
    }
    
    return 'An unexpected error occurred';
}
