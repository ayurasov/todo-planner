import { defineStore } from 'pinia'
import { userRepository } from '../repositories'

export const useUsersStore = defineStore('users', {
  state: () => ({ users: [], currentUser: null, loaded: false }),
  getters: {
    byId: (state) => (id) => state.users.find((u) => u.id === id) || null,
  },
  actions: {
    async load() {
      if (this.loaded) return
      this.users = await userRepository.getAll()
      this.currentUser = await userRepository.getCurrentUser()
      this.loaded = true
    },
  },
})
