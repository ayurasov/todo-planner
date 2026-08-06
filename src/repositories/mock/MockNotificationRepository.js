import { NotificationRepository } from '../contracts/NotificationRepository'
import { LocalStorageAdapter } from '../storage/LocalStorageAdapter'
import { createNotification } from '../../domain/entities/factories'

const storage = new LocalStorageAdapter('notifications')

export class MockNotificationRepository extends NotificationRepository {
  constructor() {
    super()
    this._items = storage.load([])
  }

  _persist() { storage.save(this._items) }

  async getByUserId(userId) {
    return this._items
      .filter((n) => n.userId === userId)
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
  }

  async create(data) {
    const notification = createNotification(data)
    this._items.push(notification)
    this._persist()
    return notification
  }

  async markRead(id) {
    const idx = this._items.findIndex((n) => n.id === id)
    if (idx === -1) return null
    this._items[idx] = { ...this._items[idx], read: true }
    this._persist()
    return this._items[idx]
  }

  async markAllRead(userId) {
    this._items = this._items.map((n) => (n.userId === userId ? { ...n, read: true } : n))
    this._persist()
  }

  async remove(id) {
    this._items = this._items.filter((n) => n.id !== id)
    this._persist()
    return true
  }
}

export const mockNotificationRepository = new MockNotificationRepository()
