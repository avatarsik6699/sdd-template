import type { Config } from 'tailwindcss';

export default {
  content: [
    './app/**/*.{vue,ts,tsx}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './components/**/*.vue',
  ],
} satisfies Config;
