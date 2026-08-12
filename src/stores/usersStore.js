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

    /**
     * Загрузка аватара. Доступно самому пользователю (свой профиль, см.
     * ProfileModal.vue) и администратору для любого пользователя (см.
     * UsersView.vue) -- backend сам решает, разрешено ли конкретному
     * user_id менять аватар данного id (см. backend/app/users/routes.py).
     * Синхронизирует локальный список и currentUser, если меняется свой аватар.
     */
    async uploadAvatar(id, file) {
      return withPermissionHandling(async () => {
        const updated = await userRepository.uploadAvatar(id, file)
        const idx = this.users.findIndex((u) => u.id === id)
        if (idx !== -1) this.users[idx] = updated
        if (this.currentUser?.id === id) this.currentUser = updated
        return updated
      }, { notificationsStore: useNotificationsStore(), router })
    },

    /** Сброс аватара на стандартный (заглушка с инициалами). */
    async deleteAvatar(id) {
      return withPermissionHandling(async () => {
        const updated = await userRepository.deleteAvatar(id)
        const idx = this.users.findIndex((u) => u.id === id)
        if (idx !== -1) this.users[idx] = updated
        if (this.currentUser?.id === id) this.currentUser = updated
        return updated
      }, { notificationsStore: useNotificationsStore(), router })
    },

    /**
     * Смена пароля текущим авторизованным пользователем (свой профиль).
     * Принимает { currentPassword, newPassword } -- см. ProfileModal.vue.
     * Ошибки (неверный текущий пароль, слишком короткий новый) прокидываются
     * вызывающему коду как есть, чтобы форма могла показать сообщение.
     */
    async changePassword(payload) {
      return userRepository.changePassword(payload)
    },
  },
})
