import { defineNuxtPlugin, useRuntimeConfig, navigateTo } from '#imports';
import { safeCookie } from '@shared/lib/safe-cookie';
import { AUTH_COOKIE_CONFIG } from '@features/auth/model/auth-store';

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();

  const api = $fetch.create({
    baseURL: (config.public.apiBase as string) || 'http://localhost:8000',

    onRequest({ options }) {
      const token = safeCookie.getItem<string>({
        keyWithVersion: AUTH_COOKIE_CONFIG,
      });

      if (token) {
        options.headers = options.headers || {};

        // Nuxt's $fetch headers can be Headers init, record, or array
        if (options.headers instanceof Headers) {
          options.headers.set('Authorization', `Bearer ${token}`);
        } else if (Array.isArray(options.headers)) {
          (options.headers as [string, string][]).push(['Authorization', `Bearer ${token}`]);
        } else {
          (options.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
        }
      }
    },

    onResponseError({ response }) {
      if (response.status === 401) {
        // Clear token
        safeCookie.removeItem({ keyWithVersion: AUTH_COOKIE_CONFIG });

        // Redirect to login if on client
        if (import.meta.client) {
          navigateTo('/login');
        }
      }
    },
  });

  return {
    provide: {
      api,
    },
  };
});
