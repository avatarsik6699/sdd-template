import type { Config } from "@react-router/dev/config";

export default {
  appDirectory: "app",
  ssr: true,
  async prerender() {
    return ["/"];
  },
} satisfies Config;
