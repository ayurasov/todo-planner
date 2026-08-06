import { defineStore } from 'pinia'
import { meetingRepository } from '../repositories'
import { useUsersStore } from './usersStore'

export const useMeetingsStore = defineStore('meetings', {
  state: () => ({ meetings: [], loaded: false }),
  getters: {
    meetingById: (state) => (id) => state.meetings.find((m) => m.id === id) || null,
    sortedByDate: (state) => [...state.meetings].sort((a, b) => new Date(b.date) - new Date(a.date)),
  },
  actions: {
    async load() {
      this.meetings = await meetingRepository.getAll()
      this.loaded = true
    },

    async createMeeting(payload) {
      const usersStore = useUsersStore()
      const meeting = await meetingRepository.create({ createdBy: usersStore.currentUser?.id, ...payload })
      this.meetings.push(meeting)
      return meeting
    },

    async updateMeeting(id, patch) {
      const updated = await meetingRepository.update(id, patch)
      const idx = this.meetings.findIndex((m) => m.id === id)
      if (idx !== -1) this.meetings[idx] = updated
      return updated
    },

    async removeMeeting(id) {
      await meetingRepository.remove(id)
      this.meetings = this.meetings.filter((m) => m.id !== id)
    },
  },
})
