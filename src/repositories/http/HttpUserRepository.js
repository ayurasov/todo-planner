import { UserRepository } from '../contracts/UserRepository'
import { apiClient, apiUploadUrl, csrfHeaders } from './apiClient'

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

  /**
   * Только для admin: полный список включая системных пользователей.
   * Соответствует GET /api/users/admin/all на backend.
   */
  async getAllAdmin() {
    return apiClient.get('/users/admin/all')
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

  async deleteUser(id) {
    return apiClient.delete(`/users/${id}`)
  }

  /**
   * multipart/form-data не проходит через общий apiClient.request (там всегда
   * Content-Type: application/json) -- поэтому здесь отдельный fetch с тем же
   * набором session/CSRF-заголовков, что и apiClient. См. backend/app/users/routes.py
   * upload_avatar (ожидает файл в поле "avatar").
   */
  async uploadAvatar(id, file) {
    const formData = new FormData()
    formData.append('avatar', file)
    const res = await fetch(apiUploadUrl(`/users/${id}/avatar`), {
      method: 'POST',
      credentials: 'include',
      headers: csrfHeaders(),
      body: formData,
    })
    return handleUploadResponse(res)
  }

  async deleteAvatar(id) {
    return apiClient.delete(`/users/${id}/avatar`)
  }

  async changePassword(payload) {
    return apiClient.post('/auth/change-password', payload)
  }
}

async function handleUploadResponse(res) {
  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    const err = new Error(payload?.message || `HTTP ${res.status}`)
    err.status = res.status
    err.payload = payload
    throw err
  }
  return payload
}

export const httpUserRepository = new HttpUserRepository()
