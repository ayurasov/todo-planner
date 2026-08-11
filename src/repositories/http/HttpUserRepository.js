import { UserRepository } from '../contracts/UserRepository'
import { apiClient } from './apiClient'

/**
 * getCurrentUser() в http-режиме всегда идёт через GET /api/auth/me
 * (а не seed/mock-данные), чтобы usersStore.currentUser в http-режиме наполнялся
 * текущим server-side session user'ом. Сам 401 здесь не перехватывается -- он обрабатывается
 * на уровне main.js до того, как app-shell смонтируется.
 */
export class HttpUserRepository extends UserRepository {
  async getAll() {
    return apiClient.get('/users')
  }

  async getById(id) {
    return apiClient.get(`/users/${id}`)
  }

  async getCurrentUser() {
    const payload = await apiClient.get('/auth/me')
    return payload?.user ?? payload
  }

  async updateUser(id, patch) {
    return apiClient.patch(`/users/${id}`, patch)
  }

  async createUser(payload) {
    return apiClient.post('/users', payload)
  }

  async resetPassword(id) {
    return apiClient.post(`/users/${id}/reset-password`, {})
  }
}

export const httpUserRepository = new HttpUserRepository()
