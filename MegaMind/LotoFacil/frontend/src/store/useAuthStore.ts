import { create } from 'zustand';
import type { LoginResponse } from '../types';

interface AuthState {
    user: LoginResponse | null;
    isAuthenticated: boolean;
    setUser: (user: LoginResponse) => void;
    clearUser: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isAuthenticated: !!localStorage.getItem('lotomind_token'),

    setUser: (user) => set({ user, isAuthenticated: true }),

    clearUser: () => {
        localStorage.removeItem('lotomind_token');
        set({ user: null, isAuthenticated: false });
    },
}));
