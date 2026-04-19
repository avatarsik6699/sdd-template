import { defineNuxtRouteMiddleware, navigateTo } from '#imports';
import { useAuthStore } from '~/stores/auth';

export default defineNuxtRouteMiddleware((to) => {
  // Skip auth check on login page.
  if (to.path === '/login') return;

  const authStore = useAuthStore();

  // On client: load token from localStorage before checking.
  if (import.meta.client) {
    authStore.loadFromStorage();
  }

  if (!authStore.isAuthenticated) {
    return navigateTo('/login');
  }
});
