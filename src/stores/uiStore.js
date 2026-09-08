import { defineStore } from 'pinia'
import { LocalStorageAdapter } from '../repositories/storage/LocalStorageAdapter'

const sidebarStorage = new LocalStorageAdapter('sidebar-collapsed')

export const useUiStore = defineStore('ui', {
  state: () => ({
    openTaskId: null,
    openTaskSnapshot: null,
    quickCreateContext: null,
    sidebarCollapsed: sidebarStorage.load(false),
    profileModalOpen: false,
  }),
  actions: {
    // Keep the clicked task as a fallback for views that render a task which
    // is not present in the global task collection (for example, occurrence views).
    openTask(id, task = null) {
      this.openTaskId = id
      this.openTaskSnapshot = task
    },
    closeTask() {
      this.openTaskId = null
      this.openTaskSnapshot = null
    },
    openQuickCreate(context = {}) { this.quickCreateContext = context },
    closeQuickCreate() { this.quickCreateContext = null },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
      sidebarStorage.save(this.sidebarCollapsed)
    },
    openProfile() { this.profileModalOpen = true },
    closeProfile() { this.profileModalOpen = false },
  },
})
