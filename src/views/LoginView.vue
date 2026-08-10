<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

/**
 * Минимальный экран входа для http-режима. Актуален только когда VITE_API_MODE=http
 * и backend вернул 401 на GET /api/auth/me (см. main.js). Не переделывает UI-кит --
 * использует те же классы card/btn, что и остальные views.
 */
const authStore = useAuthStore()
const router = useRouter()

const login = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(login.value, password.value)
    router.push('/my-tasks')
  } catch (err) {
    error.value = err.payload?.message || 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-screen">
    <form class="card login-card" @submit.prevent="submit">
      <h2>Вход в ToDo Planner</h2>
      <label class="login-field">
        <span>Логин</span>
        <input v-model="login" type="text" autocomplete="username" required />
      </label>
      <label class="login-field">
        <span>Пароль</span>
        <input v-model="password" type="password" autocomplete="current-password" required />
      </label>
      <p v-if="error" class="login-error">{{ error }}</p>
      <button class="btn btn-sm" type="submit" :disabled="loading">{{ loading ? 'Вход...' : 'Войти' }}</button>
    </form>
  </div>
</template>

<style scoped>
.login-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--color-bg, #f4f5f8); }
.login-card { width: 320px; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
.login-card h2 { margin: 0 0 6px; font-size: 17px; }
.login-field { display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; }
.login-field input { padding: 7px 9px; border: 1px solid var(--color-border, #d8dbe3); border-radius: 6px; font-size: 13px; }
.login-error { color: var(--color-danger, #d64545); font-size: 12.5px; margin: 0; }
</style>
