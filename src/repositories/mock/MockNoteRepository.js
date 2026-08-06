import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedNotes } from './seedData'
import { nextId } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('notes')

export class MockNoteRepository {
  constructor() {
    this._notes = storage.load(seedNotes)
  }

  _persist() { storage.save(this._notes) }

  async getByTaskId(taskId) {
    return this._notes.filter((n) => n.taskId === taskId)
  }

  async create(noteData) {
    const note = { id: nextId('note'), createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), ...noteData }
    this._notes.push(note)
    this._persist()
    return note
  }

  async update(id, patch) {
    const idx = this._notes.findIndex((n) => n.id === id)
    if (idx === -1) throw new Error('Note not found')
    this._notes[idx] = { ...this._notes[idx], ...patch, updatedAt: new Date().toISOString() }
    this._persist()
    return this._notes[idx]
  }

  async remove(id) {
    this._notes = this._notes.filter((n) => n.id !== id)
    this._persist()
    return true
  }
}

export const mockNoteRepository = new MockNoteRepository()
