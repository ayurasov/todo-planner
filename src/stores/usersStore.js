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

    /**
     * Обновление пользователя администратором (роль, активность).
     * Синхронизирует локальный список и currentUser, если админ меняет себя.
     */
    async updateUser(id, patch) {
      const updated = await userRepository.updateUser(id, patch)
      const idx = this.users.findIndex((u) => u.id === id)
      if (idx !== -1) this.users[idx] = updated
      if (this.currentUser?.id === id) this.currentUser = updated
      return updated
    },
  },
})
