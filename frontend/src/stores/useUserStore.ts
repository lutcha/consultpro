// ============================================
// USER STORE - Zustand
// ============================================

import { create } from 'zustand';
import type { User } from '@/types';
import { apiLogin, apiGetMe, clearTokens } from '@/lib/api';
import { mapMeResponse } from '@/lib/apiMappers';

// Demo accounts that work without a backend
const ENABLE_DEMO_LOGIN =
  import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO_LOGIN === 'true';

const DEMO_ACCOUNTS: Record<string, User> = {
  'admin@consultpro.pt:adminpass123': {
    id: 'user-admin', name: 'Admin ConsultPro', email: 'admin@consultpro.pt',
    role: 'admin', skills: ['Gestão', 'Liderança'], availability: 'available', languages: ['Portugues', 'Ingles'],
  },
  'ana.silva@consultpro.com:password123': {
    id: 'user-1', name: 'Ana Silva', email: 'ana.silva@consultpro.com',
    role: 'consultant', skills: ['Saude Publica', 'Gestao de Projetos', 'M&E'], availability: 'available', languages: ['Portugues', 'Ingles', 'Frances'],
  },
};

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiLogin(email, password);
      const me = await apiGetMe();
      const user = mapMeResponse(me);
      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch {
      // Backend offline — try demo accounts
      const demoUser = ENABLE_DEMO_LOGIN
        ? DEMO_ACCOUNTS[`${email}:${password}`]
        : undefined;
      if (demoUser) {
        set({ user: demoUser, isAuthenticated: true, isLoading: false, error: null });
        return true;
      }
      set({
        error: ENABLE_DEMO_LOGIN
          ? 'Credenciais invalidas. Backend offline - use uma conta de demo.'
          : 'Credenciais invalidas ou sessao expirada. Entre novamente.',
        isLoading: false,
        isAuthenticated: false,
        user: null,
      });
      return false;
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false, error: null });
  },

  fetchMe: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }
    try {
      const me = await apiGetMe();
      const user = mapMeResponse(me);
      set({ user, isAuthenticated: true });
    } catch {
      clearTokens();
      set({ user: null, isAuthenticated: false });
    }
  },
}));
