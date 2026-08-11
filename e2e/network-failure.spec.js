import { test, expect } from '@playwright/test'
import { loginAs, E2E_USERS } from './fixtures'

/**
 * Промпт 24, пункт 2 — silent-failure сценарий: недоступность backend (сетевая ошибка,
 * не 401/403) должна давать понятное сообщение в UI, а не белый экран/бесконечный спиннер.
 * Недоступность эмулируется через page.route() abort (без остановки контейнера backend).
 */
test.describe('Silent-failure smoke (Промпт 24, пункт 2)', () => {
  test('обрыв сети после логина (при загрузке authenticated-данных) показывает экран ошибки с кнопкой ретрая', async ({ page }) => {
    await loginAs(page, 'viewer')

    await page.route('**/api/tasks**', (route) => route.abort('internetdisconnected'))
    await page.route('**/api/lists**', (route) => route.abort('internetdisconnected'))
    await page.route('**/api/notifications**', (route) => route.abort('internetdisconnected'))
    await page.route('**/api/users**', (route) => route.abort('internetdisconnected'))

    await page.reload()

    await expect(page.getByText(/не удаётся связаться с сервером/i)).toBeVisible({ timeout: 10_000 })
    await expect(page.getByRole('button', { name: /повторить/i })).toBeVisible()

    const bodyText = await page.locator('body').innerText()
    expect(bodyText.trim().length).toBeGreaterThan(0)
  })

  test('недоступность backend во время login показывает отдельное сообщение, а не «neверный логин»', async ({ page }) => {
    await page.route('**/api/auth/login', (route) => route.abort('internetdisconnected'))

    await page.goto('/login')
    await page.getByLabel('Логин').fill(E2E_USERS.viewer.login)
    await page.getByLabel('Пароль').fill(E2E_USERS.viewer.password)
    await page.getByRole('button', { name: /войти/i }).click()

    await expect(page.getByText(/не удаётся связаться с сервером/i)).toBeVisible()
    await expect(page.getByText(/неверный логин/i)).toHaveCount(0)
  })
})
