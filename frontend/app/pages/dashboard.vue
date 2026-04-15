<script setup lang="ts">
definePageMeta({ layout: 'default' })
</script>

<template>
  <div class="max-w-3xl space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-sm text-gray-500 mt-1">[PROJECT_NAME] — add your project description here</p>
    </div>

    <div class="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-400">
      <p class="text-sm">Add your dashboard content here.</p>
      <p class="text-xs mt-1">Add nav links in <code class="font-mono">layouts/default.vue</code> and pages in <code class="font-mono">pages/</code>.</p>
    </div>
  </div>
</template>
