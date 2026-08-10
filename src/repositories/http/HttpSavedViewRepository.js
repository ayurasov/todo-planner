import { SavedViewRepository } from '../contracts/SavedViewRepository'
import { apiClient } from './apiClient'

export class HttpSavedViewRepository extends SavedViewRepository {
  async getAll(userId) {
    return apiClient.get('/saved-views', { userId })
  }

  async create(viewData) {
    return apiClient.post('/saved-views', viewData)
  }

  async update(id, patch) {
    return apiClient.patch(`/saved-views/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/saved-views/${id}`)
    return true
  }
}

export const httpSavedViewRepository = new HttpSavedViewRepository()
