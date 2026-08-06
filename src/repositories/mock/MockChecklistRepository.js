import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedChecklistItems } from './seedData'
import { nextId } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('checklist_items')

export class MockChecklistRepository {
  constructor() {
    this._items = storage.load(seedChecklistItems)
  }

  _persist() { storage.save(this._items) }

  async getByTaskId(taskId) {
    return this._items.filter((i) => i.taskId === taskId).sort((a, b) => a.order - b.order)
  }

  async create(itemData) {
    const item = { id: nextId('checklist'), done: false, order: 0, recurrenceScope: 'instance_only', ...itemData }
    this._items.push(item)
    this._persist()
    return item
  }

  async update(id, patch) {
    const idx = this._items.findIndex((i) => i.id === id)
    if (idx === -1) throw new Error('Checklist item not found')
    this._items[idx] = { ...this._items[idx], ...patch }
    this._persist()
    return this._items[idx]
  }

  async remove(id) {
    this._items = this._items.filter((i) => i.id !== id)
    this._persist()
    return true
  }
}

export const mockChecklistRepository = new MockChecklistRepository()
