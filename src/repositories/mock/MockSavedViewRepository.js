import { SavedViewRepository } from '../contracts/SavedViewRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { nextId } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('saved_views')

export class MockSavedViewRepository extends SavedViewRepository {
  constructor() {
    super()
    this._views = storage.load([])
  }

  _persist() { storage.save(this._views) }

  async getAll(userId) {
    return this._views.filter((v) => v.userId === userId)
  }

  async create(viewData) {
    const view = { id: nextId('view'), pinned: false, ...viewData }
    this._views.push(view)
    this._persist()
    return view
  }

  async update(id, patch) {
    const idx = this._views.findIndex((v) => v.id === id)
    if (idx === -1) throw new Error('View not found')
    this._views[idx] = { ...this._views[idx], ...patch }
    this._persist()
    return this._views[idx]
  }

  async remove(id) {
    this._views = this._views.filter((v) => v.id !== id)
    this._persist()
    return true
  }
}

export const mockSavedViewRepository = new MockSavedViewRepository()
