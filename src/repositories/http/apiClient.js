/**
 * Единый HTTP-клиент для backend v2 (Flask + SQLite).
 * Инкапсулирует базовый URL, сессионные cookie, CSRF-заголовок и
 * унифицированную обработку ошибок доступа (401/403), которые в mock-режиме
 * попросту не существуют (там любые операции считаются разрешёнными).
 *
 * ВАЖНО: этот файл не используется, пока VITE_API_MODE !== 'http'
 * (см. src/repositories/index.js). Он подготовлен заранее, чтобы переход
 * на реальный backend не требовал переписывания stores/services/UI --
 * только смены реализации репозиториев.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.status = status
    this.payload = payload
  }
}

export class PermissionDeniedError extends ApiError {}
export class AuthRequiredError extends ApiError {}

let csrfToken = null

export function setCsrfToken(token) {
  csrfToken = token
}

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(BASE_URL + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, v)
    })
  }

  const headers = { 'Content-Type': 'application/json' }
  if (csrfToken && method !== 'GET') headers['X-CSRF-Token'] = csrfToken

  const res = await fetch(url.toString(), {
    method,
    headers,
    credentials: 'include', // session cookie
    body: body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    const payload = await safeJson(res)
    throw new AuthRequiredError('Требуется авторизация', 401, payload)
  }
  if (res.status === 403) {
    const payload = await safeJson(res)
    throw new PermissionDeniedError('Недостаточно прав для этого действия', 403, payload)
  }
  if (!res.ok) {
    const payload = await safeJson(res)
    throw new ApiError(payload?.message || `HTTP ${res.status}`, res.status, payload)
  }
  if (res.status === 204) return null
  return safeJson(res)
}

async function safeJson(res) {
  try { return await res.json() } catch { return null }
}

export const apiClient = {
  get: (path, params) => request(path, { method: 'GET', params }),
  post: (path, body) => request(path, { method: 'POST', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}

/**
 * Абсолютный URL для ручных fetch-запросов (multipart/form-data загрузка файлов),
 * которые не могут идти через request() выше -- там всегда ставится
 * Content-Type: application/json и body всегда JSON.stringify. См. HttpUserRepository.uploadAvatar.
 */
export function apiUploadUrl(path) {
  return new URL(BASE_URL + path, window.location.origin).toString()
}

/**
 * Заголовки с CSRF-токеном для ручных fetch-запросов (без Content-Type --
 * браузер сам выставит корректный multipart-заголовок с boundary для FormData).
 */
export function csrfHeaders() {
  return csrfToken ? { 'X-CSRF-Token': csrfToken } : {}
}
