import { HistoryRepository } from '../contracts/HistoryRepository'
import { apiClient } from './apiClient'

/**
 * Backend v2 сам создаёт записи истории как сторонний эффект мутаций задачи,
 * поэтому append() в http-режиме -- no-op (вызовы HistoryService.record* в этом шаге
 * остаются в tasksStore без изменений, но бесполезны -- реальная запись уже создана
 * backend-ом внутри PATCH /api/tasks/:id).
 */
export class HttpHistoryRepository extends HistoryRepository {
  async getByTaskId(taskId) {
    return apiClient.get('/history', { taskId })
  }

  async getByListId(listId) {
    return apiClient.get('/history', { listId })
  }

  async getByUserId(userId) {
    return apiClient.get('/history', { userId })
  }

  async append(_entry) {
    return null
  }
}

export const httpHistoryRepository = new HttpHistoryRepository()
