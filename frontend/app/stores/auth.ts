import { defineStore } from 'pinia'

export interface AuthUser {
  id: string
  email: string
  role: 'admin' | 'architect' | 'expert' | 'ai_agent'
  is_active: boolean
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  isLoading: boolean
  error: string | null
}

const TOKEN_KEY = 'app_token'

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    user: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.token,
    authHeader: (state): Record<string, string> =>
      state.token ? { Authorization: `Bearer ${state.token}` } : {},
  },

  actions: {
    loadFromStorage() {
      if (import.meta.client) {
        const stored = localStorage.getItem(TOKEN_KEY)
        if (stored) {
          this.token = stored
        }
      }
    },

    async login(email: string, password: string): Promise<void> {
      this.isLoading = true
      this.error = null
      try {
        const config = useRuntimeConfig()
        const data = await $fetch<{ access_token: string; token_type: string }>(
          `${config.public.apiBase}/api/v1/auth/login`,
          {
            method: 'POST',
            body: { email, password },
          }
        )
        this.token = data.access_token
        if (import.meta.client) {
          localStorage.setItem(TOKEN_KEY, data.access_token)
        }
        await this.fetchMe()
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Login failed'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async fetchMe(): Promise<void> {
      if (!this.token) return
      try {
        const config = useRuntimeConfig()
        const data = await $fetch<AuthUser>(
          `${config.public.apiBase}/api/v1/auth/me`,
          {
            headers: { Authorization: `Bearer ${this.token}` },
          }
        )
        this.user = data
      } catch {
        // Token expired or invalid — clear auth
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.error = null
      if (import.meta.client) {
        localStorage.removeItem(TOKEN_KEY)
      }
      navigateTo('/login')
    },
  },
})
