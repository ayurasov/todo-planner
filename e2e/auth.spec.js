import { test, expect } from '@playwright/test'
import { loginAs, logout, E2E_USERS } from './fixtures'

/**
 * Smoke-checklist шаги 1 — 3 из корневого README.md:
 *  1. Login/logout.
 *  2. CSRF-токен вытягивается до login и присутствует в мутирующих запросах.
 *  3. Невалидная/отсутствующая сессия (401) → экран логина, а не белый экран.
 */
test.describe('Auth smoke (шаги 1-3)', () => {
  test('неавторизованный заход на / редиректит на /login', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: /вход/i })).toBeVisible()
  })

  test('login → /my-tasks, запросы содержат X-CSRF-Token, logout → /login', async ({ page }) => {
    const mutatingRequestsWithCsrf = []
    page.on('request', (req) => {
      if (['POST', 'PATCH', 'DELETE'].includes(req.method()) && req.url().includes('/api/')) {
        mutatingRequestsWithCsrf.push(!!req.headers()['x-csrf-token'])
      }
    })

    const csrfRequest = page.waitForRequest((req) => req.url().includes('/api/auth/csrf-token'))
    await loginAs(page, 'owner')
    await csrfRequest

    expect(mutatingRequestsWithCsrf.length).toBeGreaterThan(0)
    expect(mutatingRequestsWithCsrf.every(Boolean)).toBe(true)

    await logout(page)
    await page.goto('/my-tasks')
    await expect(page).toHaveURL(/\/login$/)
  })

  test('401 (истёкшая/удалённая cookie) показывает LoginView, а не белый экран', async ({ page, context }) => {
    await loginAs(page, 'viewer')
    await context.clearCookies()
    await page.reload()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: /вход/i })).toBeVisible()
  })
})
