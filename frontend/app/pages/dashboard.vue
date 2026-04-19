<script setup lang="ts">
import { useI18n } from '#imports';
const { t } = useI18n();

definePageMeta({ layout: 'default' });
</script>

<template>
  <div class="max-w-3xl space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('welcome') }}</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        [PROJECT_NAME] — add your project description here
      </p>
    </div>

    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Dashboard</h3>
      </template>

      <div class="text-center text-gray-500 dark:text-gray-400 py-8">
        <UIcon name="i-heroicons-rocket-launch" class="w-12 h-12 mx-auto mb-4 text-primary-500" />
        <p class="text-sm">Add your dashboard content here.</p>
        <p class="text-xs mt-1">
          Add nav links in <code class="font-mono text-primary-600">layouts/default.vue</code> and
          pages in <code class="font-mono text-primary-600">pages/</code>.
        </p>
      </div>
    </UCard>
  </div>
</template>
