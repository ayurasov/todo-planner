import { DepartmentRepository } from '../contracts/DepartmentRepository'
import { apiClient } from './apiClient'

export class HttpDepartmentRepository extends DepartmentRepository {
  async getAll() {
    return apiClient.get('/departments')
  }

  async create(payload) {
    return apiClient.post('/departments', payload)
  }

  async update(id, patch) {
    return apiClient.patch(`/departments/${id}`, patch)
  }

  async remove(id) {
    return apiClient.delete(`/departments/${id}`)
  }

  async getManagers(departmentId) {
    return apiClient.get(`/departments/${departmentId}/managers`)
  }

  async setManagers(departmentId, userIds) {
    return apiClient.put(`/departments/${departmentId}/managers`, { userIds })
  }
}

export const httpDepartmentRepository = new HttpDepartmentRepository()
