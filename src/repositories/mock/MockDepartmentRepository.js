import { DepartmentRepository } from '../contracts/DepartmentRepository'
import { seedDepartments } from './seedData'
import { nextId } from '../../domain/entities/factories'

/**
 * Mock-реализация справочника отделов/служб (плоский список, без
 * иерархии). Список руководителей отдела ведётся непосредственно в
 * user.managerDepartmentIds (аналог ManagerDepartmentORM на backend), чтобы не дублировать
 * источник истины -- один руководитель может руководить несколькими отделами.
 */
export class MockDepartmentRepository extends DepartmentRepository {
  constructor(usersRepository) {
    super()
    this._departments = seedDepartments
    this._usersRepository = usersRepository
  }

  async getAll() {
    return [...this._departments]
  }

  async create({ name }) {
    const now = new Date().toISOString()
    const dep = { id: nextId('dept'), name, createdAt: now, updatedAt: now }
    this._departments.push(dep)
    return { ...dep }
  }

  async update(id, { name }) {
    const dep = this._departments.find((d) => d.id === id)
    if (!dep) throw new Error('Department not found')
    if (name !== undefined) dep.name = name
    dep.updatedAt = new Date().toISOString()
    return { ...dep }
  }

  async remove(id) {
    const idx = this._departments.findIndex((d) => d.id === id)
    if (idx === -1) throw new Error('Department not found')
    this._departments.splice(idx, 1)
    for (const u of this._usersRepository._users) {
      if (u.departmentId === id) u.departmentId = null
      if (Array.isArray(u.managerDepartmentIds)) {
        u.managerDepartmentIds = u.managerDepartmentIds.filter((depId) => depId !== id)
      }
    }
  }

  async getManagers(departmentId) {
    return this._usersRepository._users
      .filter((u) => Array.isArray(u.managerDepartmentIds) && u.managerDepartmentIds.includes(departmentId))
      .map((u) => u.id)
  }

  async setManagers(departmentId, userIds) {
    for (const u of this._usersRepository._users) {
      const has = Array.isArray(u.managerDepartmentIds) && u.managerDepartmentIds.includes(departmentId)
      const shouldHave = userIds.includes(u.id)
      if (shouldHave && !has) {
        u.managerDepartmentIds = [...(u.managerDepartmentIds || []), departmentId]
      } else if (!shouldHave && has) {
        u.managerDepartmentIds = u.managerDepartmentIds.filter((depId) => depId !== departmentId)
      }
    }
    return this.getManagers(departmentId)
  }
}
