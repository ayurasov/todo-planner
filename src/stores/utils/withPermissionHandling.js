import { PermissionDeniedError, AuthRequiredError } from '../../repositories/http/apiClient'

/**
 * Готча для mutating store actions в http-режиме. Задача -- обрабатывать
 * PermissionDeniedError/AuthRequiredError единообразно во всех stores:
 *  - откатывает optimistic-изменение (callback rollback, если передан);
 *  - кажет toast через уже существующий in-app-механизм (notificationsStore.items) --
 *    тот же паттерн, что и в router/index.js для requiresAdmin;
 *  - ретроуит ошибку, чтобы UI (кнопка/модалка) мог своим образом обработать catch,
 *    например вернуть checkbox/кнопку в исходное состояние.
 *
 * В mock-режиме PermissionDeniedError/AuthRequiredError никогда не выбрасываются (там всё
 * разрешено), поэтому эта готча прозрачна для mock и ничего в UX не меняет.
 */
export async function withPermissionHandling(action, { rollback, notificationsStore, router } = {}) {
  try {
    return await action()
  } catch (err) {
    if (err instanceof PermissionDeniedError) {
      rollback?.()
      notificationsStore?.items?.unshift({
        id: `local_${Date.now()}`,
        userId: null,
        type: 'status_changed',
        taskId: null,
        listId: null,
        title: 'Недостаточно прав',
        body: err.payload?.message || 'Действие запрещено политикой доступа.',
        createdAt: new Date().toISOString(),
        read: false,
        actorId: null,
      })
      throw err
    }
    if (err instanceof AuthRequiredError) {
      rollback?.()
      router?.push('/login')
      throw err
    }
    throw err
  }
}
