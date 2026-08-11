import { defineStore } from 'pinia'
import { apiClient, setCsrfToken, ApiError, AuthRequiredError } from '../repositories/http/apiClient'
import { apiMode } from '../repositories'

/**
 * Авторизационный bootstrap для http-режима. В mock-режиме этот store не используется --
 * usersStore.getCurrentUser() продолжает работать через seed-данные, как раньше.
 */
export const useAuthStore = defineStore('auth', {
  state: () => ({
    checked: false,
    authenticated: false,
    // Промпт 24: отличаем "нет сессии (401)" от "backend недоступен" (сетевая ошибка/5xx),
    // чтобы LoginView/App.vue могли показать понятную ошибку вместо тихого редиректа на /login.
    networkError: false,
  }),
  actions: {
    /**
     * Вызывается один раз до монтирования app-shell в http-режиме:
     * 1) берёт CSRF-токен и кладёт в apiClient,
     * 2) дергает /api/auth/me, чтобы узнать, есть ли активная сессия.
     * При 401 authenticated остаётся false -- вызывающий код (main.js/router) должен
     * показать LoginView и не монтировать authenticated app-shell.
     * При сетевой ошибке (backend недоступен) authenticated тоже false, но networkError
     * становится true -- LoginView должен отличать это от простого "неверный пароль".
     */
    async bootstrap() {
      if (apiMode !== 'http') {
        this.checked = true
        this.authenticated = true
        return true
      }

      this.networkError = false

      try {
        const csrf = await apiClient.get('/auth/csrf-token')
        setCsrfToken(csrf?.csrfToken || csrf?.token)
      } catch (err) {
        if (isNetworkFailure(err)) this.networkError = true
        // csrf-token эндпоинт мог быть недоступен до авторизации -- продолжаем, /auth/me всё равно вернёт 401/сеть-ошибку если что-то не так.
      }

      try {
        await apiClient.get('/auth/me')
        this.authenticated = true
      } catch (err) {
        this.authenticated = false
        if (isNetworkFailure(err)) this.networkError = true
      } finally {
        this.checked = true
      }
      return this.authenticated
    },

    async login(login, password) {
      this.networkError = false
      try {
        await apiClient.post('/auth/login', { login, password })
        this.authenticated = true
      } catch (err) {
        if (isNetworkFailure(err)) this.networkError = true
        throw err
      }
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

/**
 * true для "backend недоступен" (fetch reject / TypeError сети, либо 5xx), false для
 * ожидаемых доменных ошибок доступа (401/403), которые обрабатываются отдельно.
 */
function isNetworkFailure(err) {
  if (err instanceof AuthRequiredError) return false
  if (err instanceof ApiError) return typeof err.status === 'number' && err.status >= 500
  return true
}
