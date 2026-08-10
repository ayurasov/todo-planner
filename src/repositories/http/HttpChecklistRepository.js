import { apiClient } from './apiClient'

/**
 * Аналог MockChecklistRepository (у него нет отдельного contracts/ClasResistanceListRepository.js --
 * контракт неявный, задан фактически через использование в tasksStore).
 */
export class HttpChecklistRepository {
  async getByTaskId(taskId) {
    return apiClient.get(`/tasks/${taskId}/checklist-items`)
  }

  async create(itemData) {
    const { taskId, ...rest } = itemData
    return apiClient.post(`/tasks/${taskId}/checklist-items`, rest)
  }

  async update(id, patch) {
    return apiClient.patch(`/checklist-items/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/checklist-items/${id}`)
    return true
  }
}

export const httpChecklistRepository = new HttpChecklistRepository()
