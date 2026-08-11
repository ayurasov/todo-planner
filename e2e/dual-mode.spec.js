import { test, expect } from '@playwright/test'

/**
 * Smoke-checklist шаг 7 — переключение mock ↔ http только через .env, без правкок в src/.
 *
 * Полный прогон этого шага требует двух сборок приложения (VITE_API_MODE=mock и http) и
 * выходит за рамки одной docker-compose CI-сессии. Здесь проверяется та, что
 * http-сборка (та, которая реально едет в docker-compose стеке из Промпта 22) действительно
 * говорит с backend (а не с mock/localStorage): данные совпадают с seed_e2e_data.py и переживают
 * перезагрузку с очисткой localStorage (в mock-режиме такое поведение было бы невозможно).
 * Паритет самих правил (PermissionService.js ↔ permission_service.py) уже покрыт отдельными
 * Vitest/pytest-тестами (см. README — Roadmap, "Role-matrix integration tests").
 */
test.describe('Dual-mode smoke (шаг 7)', () => {
  test('http-сборка берёт данные из реального backend (E2E: Smoke присутствует и с очищенным localStorage)', async ({ page }) => {
    await page.goto('/login')
    await page.evaluate(() => window.localStorage.clear())
    await page.reload()

    await page.getByLabel('Логин').fill('e2e-owner')
    await page.getByLabel('Пароль').fill(process.env.E2E_SEED_PASSWORD || 'E2E-test-pass-123!')
    await page.getByRole('button', { name: /войти/i }).click()
    await expect(page).toHaveURL(/\/my-tasks$/)

    await page.goto('/lists-manager')
    await expect(page.getByText(/E2E: Smoke/i)).toBeVisible()
  })
})
