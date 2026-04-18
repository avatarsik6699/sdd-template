<script setup lang="ts">
const authStore = useAuthStore();

onMounted(() => {
  authStore.loadFromStorage();
  if (authStore.isAuthenticated && !authStore.user) {
    authStore.fetchMe();
  }
});
</script>

<template>
  <div class="min-h-screen flex bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-56 bg-white border-r border-gray-200 flex flex-col p-4 shrink-0">
      <div class="text-lg font-bold text-indigo-600 mb-6">[PROJECT_NAME]</div>

      <!-- Navigation — add your project's links here -->
      <nav class="flex flex-col gap-1 flex-1">
        <NuxtLink
          to="/dashboard"
          class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
          active-class="bg-indigo-50 text-indigo-700"
        >
          Dashboard
        </NuxtLink>
      </nav>

      <!-- User section -->
      <div class="border-t border-gray-100 pt-4 mt-4">
        <div v-if="authStore.user" class="mb-2">
          <p class="text-xs text-gray-500 truncate">{{ authStore.user.email }}</p>
          <span
            class="inline-block text-xs font-medium text-indigo-600 bg-indigo-50 rounded px-1.5 py-0.5 mt-0.5"
          >
            {{ authStore.user.role }}
          </span>
        </div>
        <button
          class="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
          @click="authStore.logout()"
        >
          Sign out
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 p-8 overflow-auto">
      <slot />
    </main>
  </div>
</template>
