import js from '@eslint/js';
import pluginVue from 'eslint-plugin-vue';
import prettierRecommended from 'eslint-plugin-prettier/recommended';
import globals from 'globals';
import vueParser from 'vue-eslint-parser';
import tseslint from 'typescript-eslint';

export default [
  { ignores: ['.nuxt/**', '.output/**', 'node_modules/**', 'dist/**'] },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],

  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },

  // Must be last — disables rules that conflict with Prettier and adds prettier/prettier rule
  prettierRecommended,

  {
    rules: {
      'vue/multi-word-component-names': 'off',

      '@typescript-eslint/no-namespace': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      // TypeScript compiler handles undefined-variable checking
      'no-undef': 'off',
    },
  },
];
