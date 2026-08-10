import { RecurrenceRepository } from '../contracts/RecurrenceRepository'
import { apiClient } from './apiClient'

export class HttpRecurrenceRepository extends RecurrenceRepository {
  async getAll(listId) {
    return apiClient.get('/recurrence-templates', { listId })
  }

  async getById(id) {
    return apiClient.get(`/recurrence-templates/${id}`)
  }

  async create(templateData) {
    return apiClient.post('/recurrence-templates', templateData)
  }

  async update(id, patch) {
    return apiClient.patch(`/recurrence-templates/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/recurrence-templates/${id}`)
    return true
  }
}

export const httpRecurrenceRepository = new HttpRecurrenceRepository()
