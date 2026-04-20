<script setup lang="ts">
import { useAuthStore } from '@features/auth/model/auth-store';

const authStore = useAuthStore();
const { locale, locales, setLocale, t } = useI18n();
const colorMode = useColorMode();

const availableLocales = locales.value.map((item) => item.code);

onMounted(() => {
  authStore.loadFromStorage();
  if (authStore.isAuthenticated && !authStore.user) {
    authStore.fetchMe();
  }
});

const isDark = computed({
  get() {
    return colorMode.value === 'dark';
  },
  set() {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark';
  },
});
</script>

<template>
  <aside
    class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col p-4 shrink-0"
  >
    <div
      class="text-lg font-bold text-primary-600 dark:text-primary-400 mb-6 flex items-center justify-between"
    >
      <span>[PROJECT_NAME]</span>
      <UButton
        :icon="isDark ? 'i-heroicons-moon-20-solid' : 'i-heroicons-sun-20-solid'"
        color="neutral"
        variant="ghost"
        aria-label="Theme"
        @click="isDark = !isDark"
      />
    </div>

    <!-- Navigation -->
    <nav class="flex flex-col gap-1 flex-1">
      <NuxtLink
        to="/dashboard"
        class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/50 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
        active-class="bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-300"
      >
        {{ t('welcome') }}
      </NuxtLink>
    </nav>

    <!-- Settings / Lang -->
    <div class="flex flex-col gap-4 mt-auto pt-4 border-t border-gray-100 dark:border-gray-700">
      <div class="flex items-center gap-2">
        <UIcon name="i-heroicons-language" class="text-gray-400" />
        <USelect
          option-attribute="name"
          size="xs"
          value-attribute="code"
          :model-value="locale"
          :items="availableLocales"
          @update:model-value="setLocale"
        />
      </div>

      <!-- User section -->
      <div v-if="authStore.user" class="mb-2">
        <p class="text-xs text-gray-500 truncate">{{ authStore.user.email }}</p>
        <UBadge size="xs" variant="subtle" class="mt-1">
          {{ authStore.user.role }}
        </UBadge>
      </div>
      <UButton
        color="error"
        variant="ghost"
        block
        size="sm"
        icon="i-heroicons-arrow-left-on-rectangle"
        @click="authStore.logout()"
      >
        {{ t('login') }} (Logout)
      </UButton>
    </div>
  </aside>
</template>
