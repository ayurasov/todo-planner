import { defineStore } from 'pinia'
import { apiClient, setCsrfToken } from '../repositories/http/apiClient'
import { apiMode } from '../repositories'

/**
 * Авторизационный bootstrap для http-режима. В mock-режиме этот store не используется --
 * usersStore.getCurrentUser() продолжает работать через seed-данные, как раньше.
 */
export const useAuthStore = defineStore('auth', {
  state: () => ({
    checked: false,
    authenticated: false,
  }),
  actions: {
    /**
     * Вызывается один раз до монтирования app-shell в http-режиме:
     * 1) берёт CSRF-токен и кладёт в apiClient,
     * 2) дергает /api/auth/me, чтобы узнать, есть ли активная сессия.
     * При 401 authenticated остаётся false -- вызывающий код (main.js/router) должен
     * показать LoginView и не монтировать authenticated app-shell.
     */
    async bootstrap() {
      if (apiMode !== 'http') {
        this.checked = true
        this.authenticated = true
        return true
      }

      try {
        const csrf = await apiClient.get('/auth/csrf-token')
        setCsrfToken(csrf?.csrfToken || csrf?.token)
      } catch {
        // csrf-token эндпоинт мог быть недоступен до авторизации -- продолжаем, /auth/me всё равно вернёт 401 если нет сессии.
      }

      try {
        await apiClient.get('/auth/me')
        this.authenticated = true
      } catch (err) {
        this.authenticated = false
      } finally {
        this.checked = true
      }
      return this.authenticated
    },

    async login(login, password) {
      await apiClient.post('/auth/login', { login, password })
      this.authenticated = true
    },

    async logout() {
      try {
        await apiClient.post('/auth/logout')
      } finally {
        this.authenticated = false
      }
    },
  },
})
