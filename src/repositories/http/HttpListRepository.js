import { ListRepository } from '../contracts/ListRepository'
import { apiClient } from './apiClient'

export class HttpListRepository extends ListRepository {
  async getAll(_userId) {
    // userId берётся backend-ом из текущей сессии -- видимы только доступные списки
    // (permission_service.get_accessible_list_ids), как и в MockListRepository.getAll(userId).
    return apiClient.get('/lists')
  }

  async getAccessibleListIds(userId) {
    const lists = await this.getAll(userId)
    return lists.map((l) => l.id)
  }

  async getUserRole(listId, userId) {
    const members = await this.getMembers(listId)
    const membership = members.find((m) => m.userId === userId)
    return membership ? membership.role : null
  }

  async getById(id) {
    return apiClient.get(`/lists/${id}`)
  }

  async create(listData) {
    return apiClient.post('/lists', listData)
  }

  async update(id, patch) {
    return apiClient.patch(`/lists/${id}`, patch)
  }

  async remove(id) {
    await apiClient.delete(`/lists/${id}`)
    return true
  }

  async getMembers(listId) {
    return apiClient.get(`/lists/${listId}/memberships`)
  }

  async addMember(listId, userId, role) {
    return apiClient.post(`/lists/${listId}/memberships`, { userId, role })
  }

  async updateMemberRole(listId, userId, role) {
    return apiClient.post(`/lists/${listId}/memberships`, { userId, role })
  }

  async removeMember(listId, userId) {
    await apiClient.delete(`/lists/${listId}/memberships/${userId}`)
    return true
  }
}

export const httpListRepository = new HttpListRepository()
