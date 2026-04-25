import { defineConfig } from "vitest/config";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./app", import.meta.url)),
      "@shared": fileURLToPath(new URL("./app/shared", import.meta.url)),
      "@entities": fileURLToPath(new URL("./app/entities", import.meta.url)),
      "@features": fileURLToPath(new URL("./app/features", import.meta.url)),
      "@widgets": fileURLToPath(new URL("./app/widgets", import.meta.url)),
      "@pages": fileURLToPath(new URL("./app/pages", import.meta.url)),
    },
  },
  test: {
    environment: "node",
    globals: true,
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
  },
});
