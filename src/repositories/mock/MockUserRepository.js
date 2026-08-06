import { UserRepository } from '../contracts/UserRepository'
import { seedUsers, CURRENT_USER_ID } from './seedData'

export class MockUserRepository extends UserRepository {
  constructor() {
    super()
    this._users = seedUsers
  }

  async getAll() {
    return [...this._users]
  }

  async getById(id) {
    return this._users.find((u) => u.id === id) || null
  }

  async getCurrentUser() {
    return this._users.find((u) => u.id === CURRENT_USER_ID)
  }
}

export const mockUserRepository = new MockUserRepository()
