import { defineStore } from 'pinia'
import { userRepository } from '../repositories'
import { useNotificationsStore } from './notificationsStore'
import { withPermissionHandling } from './utils/withPermissionHandling'
import { router } from '../router'

export const useUsersStore = defineStore('users', {
  state: () => ({ users: [], currentUser: null, loaded: false }),
  getters: {
    byId: (state) => (id) => state.users.find((u) => u.id === id) || null,
  },
  actions: {
    async load() {
      if (this.loaded) return
      this.users = await userRepository.getAll()
      // getCurrentUser() в http-режиме всегда идёт через GET /api/auth/me
      // (HttpUserRepository), а не из seed/mock-данных — см. src/repositories/http/HttpUserRepository.js.
      this.currentUser = await userRepository.getCurrentUser()
      this.loaded = true
    },

    /**
     * Обновление пользователя администратором (роль, активность).
     * Синхронизирует локальный список и currentUser, если админ меняет себя.
     */
    async updateUser(id, patch) {
      return withPermissionHandling(async () => {
        const updated = await userRepository.updateUser(id, patch)
        const idx = this.users.findIndex((u) => u.id === id)
        if (idx !== -1) this.users[idx] = updated
        if (this.currentUser?.id === id) this.currentUser = updated
        return updated
      }, { notificationsStore: useNotificationsStore(), router })
    },

    /**
     * Создание нового пользователя администратором.
     * Возвращает { ...user, temporaryPassword } -- вызывающий UI должен
     * показать temporaryPassword один раз и не сохранять его.
     */
    async createUser(payload) {
      return withPermissionHandling(async () => {
        const created = await userRepository.createUser(payload)
        this.users.push(created)
        return created
      }, { notificationsStore: useNotificationsStore(), router })
    },

    /**
     * Сброс пароля пользователя администратором.
     * Возвращает { ...user, temporaryPassword } -- аналогично createUser.
     */
    async resetPassword(id) {
      return withPermissionHandling(async () => {
        return userRepository.resetPassword(id)
      }, { notificationsStore: useNotificationsStore(), router })
    },

    /** Полное удаление пользователя администратором. */
    async deleteUser(id) {
      return withPermissionHandling(async () => {
        await userRepository.deleteUser(id)
        this.users = this.users.filter((u) => u.id !== id)
      }, { notificationsStore: useNotificationsStore(), router })
    },
  },
})
