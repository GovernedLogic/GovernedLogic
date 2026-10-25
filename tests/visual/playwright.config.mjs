import { defineConfig } from "@playwright/test";

const siteRoot = process.env.SITE_ROOT;
if (!siteRoot) {
  throw new Error("SITE_ROOT must point to the verified release artifact.");
}

export default defineConfig({
  testDir: ".",
  testMatch: ["substantive.spec.mjs", "site-shell.spec.mjs"],
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 30_000,
  outputDir: "../../visual-qa/test-results",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../../visual-qa/report", open: "never" }]
  ],
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:4173",
    browserName: "chromium",
    launchOptions: process.env.CHROMIUM_BIN ? { executablePath: process.env.CHROMIUM_BIN } : {},
    colorScheme: "dark",
    deviceScaleFactor: 1,
    locale: "en-US",
    reducedMotion: "reduce",
    serviceWorkers: "block",
    timezoneId: "UTC",
    trace: "retain-on-failure"
  },
  webServer: process.env.BASE_URL ? undefined : {
    command: JSON.stringify(process.env.PYTHON_BIN || "python3") + " -m http.server 4173 --bind 127.0.0.1 --directory " + JSON.stringify(siteRoot),
    url: "http://127.0.0.1:4173/",
    reuseExistingServer: false,
    timeout: 30_000
  },
  projects: [
    {
      name: "desktop-1440",
      use: { viewport: { width: 1440, height: 1000 } }
    },
    {
      name: "mobile-320",
      use: { viewport: { width: 320, height: 800 } }
    },
    {
      name: "mobile-390",
      use: { viewport: { width: 390, height: 844 } }
    }
  ]
});
