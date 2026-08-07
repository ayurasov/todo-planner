import { defineStore } from 'pinia'
import { meetingRepository } from '../repositories'
import { useUsersStore } from './usersStore'

export const useMeetingsStore = defineStore('meetings', {
  state: () => ({ meetings: [], loaded: false }),
  getters: {
    meetingById: (state) => (id) => state.meetings.find((m) => m.id === id) || null,
    sortedByDate: (state) => [...state.meetings].filter((m) => !m.archived).sort((a, b) => new Date(b.date) - new Date(a.date)),
    // Сортировка по order используется в подменю сайдбара и на странице встреч
    // как результат пользовательского drag-n-drop, в отличие от sortedByDate.
    activeMeetings: (state) => [...state.meetings].filter((m) => !m.archived).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    archivedMeetings: (state) => [...state.meetings].filter((m) => m.archived).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
  },
  actions: {
    async load() {
      this.meetings = await meetingRepository.getAll()
      this.loaded = true
    },

    async createMeeting(payload) {
      const usersStore = useUsersStore()
      const maxOrder = this.meetings.reduce((max, m) => Math.max(max, m.order ?? 0), -1)
      const meeting = await meetingRepository.create({ createdBy: usersStore.currentUser?.id, order: maxOrder + 1, ...payload })
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

    async archiveMeeting(id) {
      return this.updateMeeting(id, { archived: true })
    },

    async unarchiveMeeting(id) {
      return this.updateMeeting(id, { archived: false })
    },

    async reorderMeetings(orderedIds) {
      await Promise.all(orderedIds.map((id, index) => {
        const meeting = this.meetingById(id)
        if (!meeting || meeting.order === index) return Promise.resolve()
        return this.updateMeeting(id, { order: index })
      }))
    },
  },
})
