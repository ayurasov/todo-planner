import { RecurrenceRepository } from '../contracts/RecurrenceRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedRecurrenceTemplates } from './seedData'
import { nextId } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('recurrence_templates')

export class MockRecurrenceRepository extends RecurrenceRepository {
  constructor() {
    super()
    this._templates = storage.load(seedRecurrenceTemplates)
  }

  _persist() { storage.save(this._templates) }

  async getAll(listId) {
    if (!listId) return [...this._templates]
    return this._templates.filter((t) => t.listId === listId)
  }

  async getById(id) {
    return this._templates.find((t) => t.id === id) || null
  }

  async create(templateData) {
    const template = { id: nextId('rectpl'), generateAheadCount: 1, lastGeneratedInstanceDate: null, checklistTemplate: [], ...templateData }
    this._templates.push(template)
    this._persist()
    return template
  }

  async update(id, patch) {
    const idx = this._templates.findIndex((t) => t.id === id)
    if (idx === -1) throw new Error('Template not found')
    this._templates[idx] = { ...this._templates[idx], ...patch }
    this._persist()
    return this._templates[idx]
  }

  async remove(id) {
    this._templates = this._templates.filter((t) => t.id !== id)
    this._persist()
    return true
  }
}

export const mockRecurrenceRepository = new MockRecurrenceRepository()
