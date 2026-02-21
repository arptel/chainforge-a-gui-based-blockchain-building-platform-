import { create } from 'zustand';
import axios from 'axios';

interface User {
    username: string;
    email: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    login: (token: string, username: string) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    token: null,
    isAuthenticated: false,
    login: (token, username) => {
        localStorage.setItem('token', token);
        set({
            token,
            user: { username, email: '' },
            isAuthenticated: true
        });
    },
    logout: () => {
        localStorage.removeItem('token');
        set({
            token: null,
            user: null,
            isAuthenticated: false
        });
    },
}));
