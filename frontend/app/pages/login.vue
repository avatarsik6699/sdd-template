<script setup lang="ts">
import { useAuthStore } from '@features/auth/model/auth-store';
import { ref, onMounted } from 'vue';

definePageMeta({ layout: 'blank' });

const authStore = useAuthStore();

const email = ref('');
const password = ref('');
const errorMsg = ref<string | null>(null);

// If already authenticated, redirect to dashboard.
onMounted(() => {
  authStore.loadFromStorage();
  if (authStore.isAuthenticated) {
    navigateTo('/dashboard');
  }
});

async function handleLogin() {
  if (!email.value.trim() || !password.value) {
    errorMsg.value = 'Email and password are required.';
    return;
  }
  errorMsg.value = null;
  try {
    await authStore.login(email.value.trim(), password.value);
    navigateTo('/dashboard');
  } catch {
    errorMsg.value = 'Invalid email or password. Please try again.';
  }
}
</script>

<template>
  <div class="w-full max-w-sm bg-white rounded-xl shadow-md p-8 space-y-6">
    <div class="text-center">
      <h1 class="text-2xl font-bold text-indigo-600">[PROJECT_NAME]</h1>
      <p class="text-sm text-gray-500 mt-1">Sign in to your account</p>
    </div>

    <form class="space-y-4" @submit.prevent="handleLogin">
      <div>
        <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="admin@example.com"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition"
        />
      </div>

      <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>

      <button
        type="submit"
        :disabled="authStore.isLoading"
        class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50"
      >
        {{ authStore.isLoading ? 'Signing in…' : 'Sign in' }}
      </button>
    </form>

    <p class="text-xs text-center text-gray-400">
      Default: <span class="font-mono">admin@example.com</span> /
      <span class="font-mono">changeme123</span>
    </p>
  </div>
</template>
