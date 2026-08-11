import { defineConfig } from '@playwright/test'

/**
 * Конфиг Playwright для Промпта 24 — smoke-сьют прогоняется против
 * docker-compose стека из Промпта 22 (frontend + backend + postgres, VITE_API_MODE=http).
 * BASE_URL по умолчанию совпадает с nginx-входом compose-стека (http://localhost).
 * Предварительно нужно выполнить backend/seed_e2e_data.py (см. e2e/README.md).
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
})
