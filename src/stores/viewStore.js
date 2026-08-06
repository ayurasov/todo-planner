import { defineStore } from 'pinia'
import { savedViewRepository } from '../repositories'
import { useUsersStore } from './usersStore'

export const useViewStore = defineStore('view', {
  state: () => ({
    activeFilters: { status: ['open', 'in_progress'], listIds: null, assigneeId: null, tags: [] },
    sort: { field: 'score', dir: 'desc' },
    savedViews: [],
  }),
  actions: {
    setStatusFilter(status) { this.activeFilters.status = status },
    setListFilter(listIds) { this.activeFilters.listIds = listIds },
    resetFilters() { this.activeFilters = { status: ['open', 'in_progress'], listIds: null, assigneeId: null, tags: [] } },

    async loadSavedViews() {
      const usersStore = useUsersStore()
      this.savedViews = await savedViewRepository.getAll(usersStore.currentUser.id)
    },

    async saveCurrentAsView(name) {
      const usersStore = useUsersStore()
      const view = await savedViewRepository.create({
        userId: usersStore.currentUser.id, name, filters: { ...this.activeFilters }, sort: { ...this.sort },
      })
      this.savedViews.push(view)
      return view
    },

    applyView(view) {
      this.activeFilters = { ...view.filters }
      this.sort = { ...view.sort }
    },
  },
})
