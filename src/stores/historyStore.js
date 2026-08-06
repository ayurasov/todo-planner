import { defineStore } from 'pinia'
import { historyRepository, userRepository } from '../repositories'

export const useHistoryStore = defineStore('history', {
  state: () => ({ timelineByTask: {}, globalLog: [], usersCache: {} }),
  actions: {
    async loadTaskTimeline(taskId) {
      this.timelineByTask[taskId] = await historyRepository.getByTaskId(taskId)
      await this._hydrateActors(this.timelineByTask[taskId])
    },

    async loadGlobalLog(taskIds) {
      this.globalLog = await historyRepository.getByListId(null, taskIds)
      await this._hydrateActors(this.globalLog)
    },

    async _hydrateActors(entries) {
      for (const e of entries) {
        if (!this.usersCache[e.actorId]) {
          this.usersCache[e.actorId] = await userRepository.getById(e.actorId)
        }
      }
    },

    actorName(actorId) {
      return this.usersCache[actorId]?.name || actorId
    },
  },
})
