import { expect } from '@playwright/test'

/**
 * Общие утилиты для Playwright smoke-тестов (Промпт 24). Учётки --
 * детерминированные из backend/seed_e2e_data.py.
 */
export const E2E_PASSWORD = process.env.E2E_SEED_PASSWORD || 'E2E-test-pass-123!'

export const E2E_USERS = {
  admin: { login: 'e2e-admin', password: E2E_PASSWORD },
  owner: { login: 'e2e-owner', password: E2E_PASSWORD },
  viewer: { login: 'e2e-viewer', password: E2E_PASSWORD },
}

export async function loginAs(page, userKey) {
  const { login, password } = E2E_USERS[userKey]
  await page.goto('/login')
  await page.getByLabel('Логин').fill(login)
  await page.getByLabel('Пароль').fill(password)
  await page.getByRole('button', { name: /войти/i }).click()
  await expect(page).toHaveURL(/\/my-tasks$/)
}

export async function logout(page) {
  await page.goto('/settings')
  await page.getByRole('button', { name: /выйти|logout/i }).click()
  await expect(page).toHaveURL(/\/login$/)
}
