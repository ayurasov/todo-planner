import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    openTaskId: null,
    quickCreateContext: null,
  }),
  actions: {
    openTask(id) { this.openTaskId = id },
    closeTask() { this.openTaskId = null },
    openQuickCreate(context = {}) { this.quickCreateContext = context },
    closeQuickCreate() { this.quickCreateContext = null },
  },
})
