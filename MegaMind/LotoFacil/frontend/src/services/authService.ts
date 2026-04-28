import api from './api';
import type { LoginRequest, LoginResponse } from '../types';

export const authService = {
    async login(credentials: LoginRequest): Promise<LoginResponse> {
        const { data } = await api.post<LoginResponse>('/auth/login', credentials);
        localStorage.setItem('lotomind_token', data.token);
        return data;
    },

    logout(): void {
        localStorage.removeItem('lotomind_token');
        window.location.href = '/login';
    },

    getToken(): string | null {
        return localStorage.getItem('lotomind_token');
    },

    isAuthenticated(): boolean {
        return !!localStorage.getItem('lotomind_token');
    },
};
