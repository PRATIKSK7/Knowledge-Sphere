import { create } from 'zustand';
import { User } from '../types';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, refreshToken: string, user: User) => void;
  updateUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  // Try loading initial state from localStorage
  const savedToken = localStorage.getItem('ks_token');
  const savedRefreshToken = localStorage.getItem('ks_refresh');
  const savedUser = localStorage.getItem('ks_user');

  return {
    token: savedToken,
    refreshToken: savedRefreshToken,
    user: savedUser ? JSON.parse(savedUser) : null,
    isAuthenticated: !!savedToken,
    setAuth: (token, refreshToken, user) => {
      localStorage.setItem('ks_token', token);
      localStorage.setItem('ks_refresh', refreshToken);
      localStorage.setItem('ks_user', JSON.stringify(user));
      set({ token, refreshToken, user, isAuthenticated: true });
    },
    updateUser: (user) => {
      localStorage.setItem('ks_user', JSON.stringify(user));
      set({ user });
    },
    logout: () => {
      localStorage.removeItem('ks_token');
      localStorage.removeItem('ks_refresh');
      localStorage.removeItem('ks_user');
      set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
    }
  };
});
