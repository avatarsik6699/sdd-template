import { navigateTo, useNuxtApp } from '#imports';
import { defineStore } from 'pinia';
import { safeCookie } from '@shared/lib/safe-cookie';

export const AUTH_COOKIE_CONFIG = {
  key: 'app_token',
  version: '1.0',
};

export interface AuthUser {
  id: string;
  email: string;
  role: 'admin' | 'architect' | 'expert' | 'ai_agent';
  is_active: boolean;
}

interface AuthState {
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (): boolean =>
      !!safeCookie.getItem<string>({ keyWithVersion: AUTH_COOKIE_CONFIG }),
    token: (): string | undefined =>
      safeCookie.getItem<string>({ keyWithVersion: AUTH_COOKIE_CONFIG }),
  },

  actions: {
    loadFromStorage() {
      // Cookies are automatically loaded, nothing to do here
    },

    async login(email: string, password: string): Promise<void> {
      this.isLoading = true;
      this.error = null;
      try {
        const { $api } = useNuxtApp();

        // Use URLSearchParams because FastAPI OAuth2 expects application/x-www-form-urlencoded
        const data = await $api<{ access_token: string; token_type: string }>(
          '/api/v1/auth/login',
          {
            method: 'POST',
            body: {
              email: email,
              password: password,
            },
          }
        );

        safeCookie.setItem({
          keyWithVersion: AUTH_COOKIE_CONFIG,
          value: data.access_token,
          options: {
            maxAge: 60 * 60 * 24 * 7, // 7 days
            path: '/',
          },
        });

        await this.fetchMe();
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Login failed';
        throw err;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchMe(): Promise<void> {
      if (!this.isAuthenticated) return;
      try {
        const { $api } = useNuxtApp();
        const data = await $api<AuthUser>('/api/v1/auth/me');
        this.user = data;
      } catch {
        // Token expired or invalid — clear auth
        this.logout();
      }
    },

    logout() {
      this.user = null;
      this.error = null;
      safeCookie.removeItem({ keyWithVersion: AUTH_COOKIE_CONFIG });
      navigateTo('/login');
    },
  },
});
