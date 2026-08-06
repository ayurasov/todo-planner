import { HistoryRepository } from '../contracts/HistoryRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { seedHistory } from './seedData'
import { nextId } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('history')

export class MockHistoryRepository extends HistoryRepository {
  constructor() {
    super()
    this._entries = storage.load(seedHistory)
  }

  _persist() { storage.save(this._entries) }

  async getByTaskId(taskId) {
    return this._entries
      .filter((e) => e.taskId === taskId)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  }

  async getByListId(listId, taskIdsInList) {
    return this._entries
      .filter((e) => taskIdsInList.includes(e.taskId))
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  }

  async getByUserId(userId) {
    return this._entries
      .filter((e) => e.actorId === userId)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  }

  async append(entry) {
    const full = { id: nextId('hist'), timestamp: new Date().toISOString(), ...entry }
    this._entries.push(full)
    this._persist()
    return full
  }
}

export const mockHistoryRepository = new MockHistoryRepository()
