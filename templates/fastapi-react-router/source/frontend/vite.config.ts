import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [reactRouter(), tailwindcss()],
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
  server: {
    port: 3000,
    host: "0.0.0.0",
  },
});
