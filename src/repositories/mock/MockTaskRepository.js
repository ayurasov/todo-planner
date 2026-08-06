import { TaskRepository } from '../contracts/TaskRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedTasks } from './seedData'
import { nextId } from '../../domain/entities/factories'
import { TaskStatus } from '../../domain/entities/enums'

const storage = new LocalStorageAdapter('tasks')

export class MockTaskRepository extends TaskRepository {
  constructor() {
    super()
    this._tasks = storage.load(seedTasks)
  }

  _persist() {
    storage.save(this._tasks)
  }

  async getAll(filters = {}) {
    let result = [...this._tasks]
    if (filters.listId) result = result.filter((t) => t.listId === filters.listId)
    if (filters.listIds) result = result.filter((t) => filters.listIds.includes(t.listId))
    if (filters.assigneeId) result = result.filter((t) => t.assigneeId === filters.assigneeId)
    if (filters.status && filters.status.length) result = result.filter((t) => filters.status.includes(t.status))
    if (filters.parentTaskId !== undefined) result = result.filter((t) => t.parentTaskId === filters.parentTaskId)
    if (filters.tags && filters.tags.length) result = result.filter((t) => t.tags.some((tag) => filters.tags.includes(tag)))
    return result
  }

  async getById(id) {
    return this._tasks.find((t) => t.id === id) || null
  }

  async getChildren(parentTaskId) {
    return this._tasks.filter((t) => t.parentTaskId === parentTaskId)
  }

  async getDescendantIds(taskId) {
    const children = this._tasks.filter((t) => t.parentTaskId === taskId)
    let ids = children.map((c) => c.id)
    for (const child of children) {
      ids = ids.concat(await this.getDescendantIds(child.id))
    }
    return ids
  }

  async create(taskData) {
    const task = {
      id: nextId('task'),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastActivityAt: new Date().toISOString(),
      status: TaskStatus.OPEN,
      watcherIds: [],
      tags: [],
      pinned: false,
      completedAt: null,
      parentTaskId: null,
      ...taskData,
    }
    this._tasks.push(task)
    this._persist()
    return task
  }

  async update(id, patch) {
    const idx = this._tasks.findIndex((t) => t.id === id)
    if (idx === -1) throw new Error(`Task ${id} not found`)
    const updated = {
      ...this._tasks[idx],
      ...patch,
      updatedAt: new Date().toISOString(),
      lastActivityAt: new Date().toISOString(),
    }
    this._tasks[idx] = updated
    this._persist()
    return updated
  }

  async remove(id) {
    const descendantIds = await this.getDescendantIds(id)
    const idsToRemove = new Set([id, ...descendantIds])
    this._tasks = this._tasks.filter((t) => !idsToRemove.has(t.id))
    this._persist()
    return true
  }

  async complete(id) {
    return this.update(id, { status: TaskStatus.DONE, completedAt: new Date().toISOString() })
  }

  async reopen(id) {
    return this.update(id, { status: TaskStatus.OPEN, completedAt: null })
  }

  async reschedule(id, newDueDate) {
    return this.update(id, { dueDate: newDueDate })
  }

  async assign(id, assigneeId) {
    return this.update(id, { assigneeId })
  }
}

export const mockTaskRepository = new MockTaskRepository()
