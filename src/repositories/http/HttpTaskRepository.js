import { TaskRepository } from '../contracts/TaskRepository'
import { apiClient } from './apiClient'

/**
 * HTTP-аналог MockTaskRepository. Контракт идентичен -- tasksStore/useTaskPermissions
 * не знают, что за реализацией стоит за `taskRepository` (см. src/repositories/index.js).
 * getDescendantIds/reopen в контракте TaskRepository отсутствуют, но используются MockTaskRepository/tasksStore --
 * реализуем их также, чтобы tasksStore.removeTask/reopenTask работали без изменения store.
 */
export class HttpTaskRepository extends TaskRepository {
  async getAll(filters = {}) {
    const params = {
      listId: filters.listId,
      listIds: filters.listIds?.join(','),
      assigneeId: filters.assigneeId,
      status: filters.status?.join(','),
      parentTaskId: filters.parentTaskId,
      tags: filters.tags?.join(','),
    }
    return apiClient.get('/tasks', params)
  }

  async getById(id) {
    return apiClient.get(`/tasks/${id}`)
  }

  async getChildren(parentTaskId) {
    return apiClient.get('/tasks', { parentTaskId })
  }

  async getDescendantIds(taskId) {
    const children = await this.getChildren(taskId)
    let ids = children.map((c) => c.id)
    for (const child of children) {
      ids = ids.concat(await this.getDescendantIds(child.id))
    }
    return ids
  }

  async create(taskData) {
    return apiClient.post('/tasks', taskData)
  }

  async update(id, patch) {
    return apiClient.patch(`/tasks/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/tasks/${id}`)
    return true
  }

  async complete(id) {
    return apiClient.patch(`/tasks/${id}`, { status: 'done', completedAt: new Date().toISOString() })
  }

  async reopen(id) {
    return apiClient.patch(`/tasks/${id}`, { status: 'open', completedAt: null })
  }

  async reschedule(id, newDueDate) {
    return apiClient.patch(`/tasks/${id}`, { dueDate: newDueDate })
  }

  async assign(id, assigneeId) {
    return apiClient.patch(`/tasks/${id}`, { assigneeId })
  }
}

export const httpTaskRepository = new HttpTaskRepository()
