import { defineStore } from 'pinia'
import { notificationRepository } from '../repositories'
import { useUsersStore } from './usersStore'
import { LocalStorageAdapter } from '../repositories/storage/LocalStorageAdapter'

const settingsStorage = new LocalStorageAdapter('notification_settings')

const DEFAULT_SETTINGS = {
  channels: { in_app: true, email: false },
  types: {
    assigned: true,
    due_soon: true,
    overdue: true,
    comment: true,
    mention: true,
    status_changed: false,
    rescheduled: true,
    subtask_completed: false,
    list_invite: true,
  },
  dueSoonThresholdHours: 24,
  quietHoursEnabled: false,
  quietHoursStart: '21:00',
  quietHoursEnd: '09:00',
  digestMode: 'instant',
}

function isWithinQuietHours(settings) {
  if (!settings.quietHoursEnabled) return false
  const now = new Date()
  const [startH, startM] = settings.quietHoursStart.split(':').map(Number)
  const [endH, endM] = settings.quietHoursEnd.split(':').map(Number)
  const nowMinutes = now.getHours() * 60 + now.getMinutes()
  const start = startH * 60 + startM
  const end = endH * 60 + endM
  if (start < end) return nowMinutes >= start && nowMinutes < end
  return nowMinutes >= start || nowMinutes < end
}

export const useNotificationsStore = defineStore('notifications', {
  state: () => ({
    items: [],
    settings: settingsStorage.load(DEFAULT_SETTINGS),
    loaded: false,
  }),
  getters: {
    unreadCount: (state) => state.items.filter((n) => !n.read).length,
    sorted: (state) => [...state.items].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)),
  },
  actions: {
    async load() {
      const usersStore = useUsersStore()
      if (!usersStore.currentUser) return
      this.items = await notificationRepository.getByUserId(usersStore.currentUser.id)
      this.loaded = true
    },

    saveSettings(patch) {
      this.settings = { ...this.settings, ...patch }
      settingsStorage.save(this.settings)
    },

    toggleType(type) {
      this.saveSettings({ types: { ...this.settings.types, [type]: !this.settings.types[type] } })
    },

    toggleChannel(channel) {
      this.saveSettings({ channels: { ...this.settings.channels, [channel]: !this.settings.channels[channel] } })
    },

    async notify({ userId, type, taskId = null, listId = null, title, body = '', actorId = null }) {
      if (!this.settings.types[type]) return null
      if (!this.settings.channels.in_app) return null
      const notification = await notificationRepository.create({ userId, type, taskId, listId, title, body, actorId })
      const usersStore = useUsersStore()
      if (userId === usersStore.currentUser?.id) {
        this.items.unshift(notification)
      }
      return notification
    },

    isQuiet() {
      return isWithinQuietHours(this.settings)
    },

    async markRead(id) {
      await notificationRepository.markRead(id)
      const idx = this.items.findIndex((n) => n.id === id)
      if (idx !== -1) this.items[idx] = { ...this.items[idx], read: true }
    },

    async markAllRead() {
      const usersStore = useUsersStore()
      await notificationRepository.markAllRead(usersStore.currentUser.id)
      this.items = this.items.map((n) => ({ ...n, read: true }))
    },

    async remove(id) {
      await notificationRepository.remove(id)
      this.items = this.items.filter((n) => n.id !== id)
    },
  },
})
