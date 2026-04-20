<script setup lang="ts">
// Layout is composed from the SidebarNav widget
</script>

<template>
  <div
    class="min-h-screen flex bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors"
  >
    <SidebarNav />
    <main class="flex-1 p-8 overflow-auto">
      <slot />
    </main>
  </div>
</template>
