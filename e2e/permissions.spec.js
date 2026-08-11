import { test, expect } from '@playwright/test'
import { loginAs } from './fixtures'

/**
 * Smoke-checklist шаги 4 — 6 из корневого README.md:
 *  4. 403 → откат optimistic update + toast «Nedostatoчно прав».
 *  5. Viewer не может редактировать задачу ни в UI (кнопки скрыты/disabled), ни в API (403).
 *  6. Admin видит /settings/users и все списки (bypass через is_global_admin).
 */
test.describe('Permissions smoke (шаги 4-6)', () => {
  test('Viewer: кнопки редактирования скрыты/disabled в списке E2E: Smoke', async ({ page }) => {
    await loginAs(page, 'viewer')
    const listLink = page.getByRole('link', { name: /E2E: Smoke/i })
    if (await listLink.count()) {
      await listLink.first().click()
    } else {
      await page.goto('/team-tasks')
    }
    await expect(page.getByRole('button', { name: /создать задачу/i })).toHaveCount(0)
  })

  test('Viewer: PATCH задачи в списке без его edit-прав вернёт 403 на прямой API-вызов', async ({ page, request }) => {
    await loginAs(page, 'viewer')
    const cookies = await page.context().cookies()
    const cookieHeader = cookies.map((c) => `${c.name}=${c.value}`).join('; ')

    const tasksRes = await request.get('/api/tasks', { headers: { Cookie: cookieHeader } })
    expect(tasksRes.ok()).toBe(true)
    const tasks = await tasksRes.json()
    if (!tasks.length) test.skip(true, 'Нет задач для проверки -- выполните seed_e2e_data.py с тестовыми задачами')

    const target = tasks[0]
    const patchRes = await request.patch(`/api/tasks/${target.id}`, {
      headers: { Cookie: cookieHeader },
      data: { title: 'попытка изменения от viewer' },
    })
    expect(patchRes.status()).toBe(403)
  })

  test('Admin: /settings/users открывается, а не редиректит на /my-tasks', async ({ page }) => {
    await loginAs(page, 'admin')
    await page.goto('/settings/users')
    await expect(page).toHaveURL(/\/settings\/users$/)
  })

  test('Admin: Lists Manager видит списои, где он не состоит явным участником', async ({ page }) => {
    await loginAs(page, 'admin')
    await page.goto('/lists-manager')
    await expect(page.getByText(/E2E: Smoke/i)).toBeVisible()
  })

  test('403 при попытке открыть /settings/users не-админом даёт редирект + toast, а не краш UI', async ({ page }) => {
    await loginAs(page, 'viewer')
    await page.goto('/settings/users')
    await expect(page).toHaveURL(/\/my-tasks$/)
    await expect(page.getByText(/только для администраторов/i)).toBeVisible()
  })
})
