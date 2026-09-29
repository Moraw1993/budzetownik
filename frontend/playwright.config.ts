import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "https://localhost:8443",
    headless: true,
    channel: process.platform === "win32" ? "msedge" : undefined,
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
  },
});
