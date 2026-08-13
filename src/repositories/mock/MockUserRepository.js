import { UserRepository } from '../contracts/UserRepository'
import { seedUsers, CURRENT_USER_ID } from './seedData'

export class MockUserRepository extends UserRepository {
  constructor() {
    super()
    this._users = seedUsers
  }

  async getAll() {
    // Обычный список — без системных пользователей (аналог backend GET /api/users)
    return this._users.filter((u) => !u.isSystem)
  }

  /**
   * Полный список включая системных — только для admin.
   * Аналог backend GET /api/users/admin/all.
   */
  async getAllAdmin() {
    return [...this._users]
  }

  async getById(id) {
    return this._users.find((u) => u.id === id) || null
  }

  async getCurrentUser() {
    return this._users.find((u) => u.id === CURRENT_USER_ID)
  }

  async updateUser(id, patch) {
    const idx = this._users.findIndex((u) => u.id === id)
    if (idx === -1) throw new Error('User not found')
    this._users[idx] = { ...this._users[idx], ...patch }
    return { ...this._users[idx] }
  }

  async createUser(payload) {
    const user = {
      id: `mock-user-${Date.now()}`,
      name: payload.name,
      email: payload.email,
      login: payload.login,
      globalRole: payload.globalRole || 'user',
      isActive: true,
      isSystem: payload.isSystem ?? false,
      timezone: 'Europe/Moscow',
      avatarUrl: null,
      position: payload.position || null,
      department: payload.department || null,
      departmentId: payload.departmentId || null,
      managerDepartmentIds: payload.managerDepartmentIds || [],
    }
    this._users.push(user)
    return { ...user, temporaryPassword: payload.password || 'mock-password' }
  }

  async resetPassword(id) {
    const user = this._users.find((u) => u.id === id)
    if (!user) throw new Error('User not found')
    return { ...user, temporaryPassword: 'mock-reset-password' }
  }

  async deleteUser(id) {
    const idx = this._users.findIndex((u) => u.id === id)
    if (idx === -1) throw new Error('User not found')
    this._users.splice(idx, 1)
  }

  /**
   * В mock-режиме нет реальной загрузки на сервер -- используется вред URL.createObjectURL,
   * чтобы выбранный файл сразу было видно в UI (переживает только текущую
   * вкладку/сессию браузера, что абсолютно достаточно для mock-режима без backend).
   */
  async uploadAvatar(id, file) {
    const idx = this._users.findIndex((u) => u.id === id)
    if (idx === -1) throw new Error('User not found')
    this._users[idx] = { ...this._users[idx], avatarUrl: URL.createObjectURL(file) }
    return { ...this._users[idx] }
  }

  async deleteAvatar(id) {
    const idx = this._users.findIndex((u) => u.id === id)
    if (idx === -1) throw new Error('User not found')
    this._users[idx] = { ...this._users[idx], avatarUrl: null }
    return { ...this._users[idx] }
  }

  async changePassword(_payload) {
    return { message: 'password_changed' }
  }
}

export const mockUserRepository = new MockUserRepository()
