import { defineStore } from 'pinia'
import { LocalStorageAdapter } from '../repositories/storage/LocalStorageAdapter'

const sidebarStorage = new LocalStorageAdapter('sidebar-collapsed')

export const useUiStore = defineStore('ui', {
  state: () => ({
    openTaskId: null,
    openTaskSnapshot: null,
    quickCreateContext: null,
    sidebarCollapsed: sidebarStorage.load(false),
    // Модалка собственного профиля (см. ProfileModal.vue) -- открывается кликом
    // на имя/аватар в AppTopBar.vue. Состояние глобальное (а не локальное в AppTopBar),
    // чтобы в будущем открывать её также из других мест (например, пункт в меню).
    profileModalOpen: false,
  }),
  actions: {
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
