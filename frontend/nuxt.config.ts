// https://nuxt.com/docs/api/configuration/nuxt-config
import { fileURLToPath } from 'node:url';

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  future: {
    compatibilityVersion: 4,
  },

  modules: ['@nuxt/ui', '@nuxtjs/i18n', '@pinia/nuxt'],
  css: ['~/assets/css/main.css'],

  // FSD layer path aliases
  alias: {
    '@shared': fileURLToPath(new URL('./app/shared', import.meta.url)),
    '@features': fileURLToPath(new URL('./app/features', import.meta.url)),
    '@widgets': fileURLToPath(new URL('./app/widgets', import.meta.url)),
  },

  // Auto-import composables/stores from FSD directories (paths relative to srcDir)
  imports: {
    dirs: ['shared/api', 'shared/lib', 'shared/model', 'features/auth/model'],
  },

  // Auto-import components from FSD widget layer
  components: [{ path: '~/widgets', pathPrefix: false }],

  i18n: {
    locales: [
      { code: 'en', language: 'en-US', file: 'en.json', name: 'English' },
      { code: 'ru', language: 'ru-RU', file: 'ru.json', name: 'Русский' },
    ],
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
    langDir: 'locales',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
    },
  },

  colorMode: {
    preference: 'system',
    fallback: 'light',
    classSuffix: '',
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE_URL ?? 'http://localhost:8000',
    },
  },
});
