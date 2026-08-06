import { defineStore } from 'pinia'
import { LocalStorageAdapter } from '../repositories/storage/LocalStorageAdapter'

const sidebarStorage = new LocalStorageAdapter('sidebar-collapsed')

export const useUiStore = defineStore('ui', {
  state: () => ({
    openTaskId: null,
    quickCreateContext: null,
    sidebarCollapsed: sidebarStorage.load(false),
  }),
  actions: {
    openTask(id) { this.openTaskId = id },
    closeTask() { this.openTaskId = null },
    openQuickCreate(context = {}) { this.quickCreateContext = context },
    closeQuickCreate() { this.quickCreateContext = null },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
      sidebarStorage.save(this.sidebarCollapsed)
    },
  },
})
