import { apiClient } from './apiClient'

export class HttpNoteRepository {
  async getByTaskId(taskId) {
    return apiClient.get(`/tasks/${taskId}/notes`)
  }

  async create(noteData) {
    const { taskId, ...rest } = noteData
    return apiClient.post(`/tasks/${taskId}/notes`, rest)
  }

  async update(id, patch) {
    return apiClient.patch(`/notes/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/notes/${id}`)
    return true
  }
}

export const httpNoteRepository = new HttpNoteRepository()
