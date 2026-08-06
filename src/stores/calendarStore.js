import { defineStore } from 'pinia'
import { calendarProvider } from '../integrations/calendar/MockCalendarProvider'

export const useCalendarStore = defineStore('calendar', {
  state: () => ({ status: 'disconnected', lastSyncedAt: null, busySlots: [], recurringMeetings: [] }),
  actions: {
    async refreshStatus() {
      const s = await calendarProvider.getStatus()
      this.status = s.status
      this.lastSyncedAt = s.lastSyncedAt
    },
    async connect(config) {
      await calendarProvider.connect(config)
      await this.refreshStatus()
      await this.loadData()
    },
    async disconnect() {
      await calendarProvider.disconnect()
      await this.refreshStatus()
      this.busySlots = []
      this.recurringMeetings = []
    },
    async loadData() {
      this.busySlots = await calendarProvider.getBusySlots()
      this.recurringMeetings = await calendarProvider.getRecurringMeetings()
    },
    async resync() {
      await calendarProvider.manualResync()
      await this.refreshStatus()
      await this.loadData()
    },
  },
})
