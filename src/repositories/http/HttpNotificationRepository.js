import { NotificationRepository } from '../contracts/NotificationRepository'
import { apiClient } from './apiClient'

export class HttpNotificationRepository extends NotificationRepository {
  async getByUserId(userId) {
    return apiClient.get('/notifications', { userId })
  }

  async create(data) {
    return apiClient.post('/notifications', data)
  }

  async markRead(id) {
    return apiClient.patch(`/notifications/${id}`, { read: true })
  }

  async markAllRead(_userId) {
    return apiClient.post('/notifications/mark-all-read')
  }

  async remove(id) {
    await apiClient.delete(`/notifications/${id}`)
    return true
  }
}

export const httpNotificationRepository = new HttpNotificationRepository()
