<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import AppIcon from '../components/common/AppIcon.vue'

/**
 * Экран входа для http-режима. Приведён к общей стилистике продукта
 * «По Делу — Менеджер задач и списков»: брендинг, фирменный акцент,
 * полноценная hero-card и аккуратные состояния ошибок/загрузки.
 */
const authStore = useAuthStore()
const router = useRouter()

const login = ref('')
const password = ref('')
const error = ref('')
const isNetworkError = ref(false)
const loading = ref(false)

async function submit() {
  error.value = ''
  isNetworkError.value = false
  loading.value = true
  try {
    await authStore.login(login.value, password.value)
    router.push('/my-tasks')
  } catch (err) {
    // Промпт 24: сетевая недоступность backend -- отдельное, понятное сообщение,
    // а не общее «неверный логин или пароль», чтобы не вводить в заблуждение.
    if (authStore.networkError) {
      isNetworkError.value = true
      error.value = 'Не удаётся связаться с сервером. Проверьте подключение и попробуйте снова.'
    } else {
      error.value = err.payload?.message || 'Неверный логин или пароль'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-screen">
    <div class="login-shell">
      <section class="login-brand card">
        <div class="brand-badge">
          <AppIcon name="brandMark" :size="28" />
        </div>
        <div class="brand-copy">
          <span class="brand-name">По Делу</span>
          <span class="brand-tagline">Менеджер задач и списков</span>
        </div>
        <h1>Рабочие задачи, списки и встречи — в одном месте</h1>
        <p class="brand-description">
          Планируйте личные и командные задачи, ведите списки, фиксируйте договорённости по встречам и держите всё по делу в едином интерфейсе.
        </p>
        <div class="brand-highlights">
          <div class="brand-highlight">
            <AppIcon name="check" :size="14" />
            <span>Единый список задач и встреч</span>
          </div>
          <div class="brand-highlight">
            <AppIcon name="team" :size="14" />
            <span>Совместная работа по ролям</span>
          </div>
          <div class="brand-highlight">
            <AppIcon name="repeat" :size="14" />
            <span>Регулярные встречи и серии задач</span>
          </div>
        </div>
      </section>

      <form class="card login-card" @submit.prevent="submit">
        <div class="login-card-header">
          <div class="login-logo-inline">
            <AppIcon name="brandMark" :size="20" class="login-logo-icon" />
            <div class="login-logo-text">
              <span class="login-logo-title">Вход в систему</span>
              <span class="login-logo-subtitle">По Делу — Менеджер задач и списков</span>
            </div>
          </div>
        </div>

        <label class="login-field">
          <span>Логин</span>
          <input v-model="login" type="text" autocomplete="username" required placeholder="Введите логин" />
        </label>
        <label class="login-field">
          <span>Пароль</span>
          <input v-model="password" type="password" autocomplete="current-password" required placeholder="Введите пароль" />
        </label>
        <p v-if="error" class="login-error" :class="{ 'login-error--network': isNetworkError }">{{ error }}</p>
        <button class="btn btn-primary login-submit" type="submit" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(79, 124, 255, 0.14), transparent 32%),
    radial-gradient(circle at bottom right, rgba(124, 92, 214, 0.12), transparent 28%),
    linear-gradient(180deg, #f7f9fe 0%, #eef3fb 100%);
}

.login-shell {
  width: min(1040px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 380px);
  gap: 22px;
  align-items: stretch;
}

.login-brand,
.login-card {
  box-shadow: 0 18px 48px rgba(25, 36, 79, 0.08);
  border: 1px solid rgba(79, 124, 255, 0.12);
}

.login-brand {
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  background: linear-gradient(135deg, rgba(79, 124, 255, 0.08), rgba(124, 92, 214, 0.06));
}

.brand-badge {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  background: rgba(79, 124, 255, 0.12);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.brand-tagline {
  font-size: 11.5px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.login-brand h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.15;
  max-width: 560px;
}

.brand-description {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
  line-height: 1.65;
  max-width: 560px;
}

.brand-highlights {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-top: 6px;
}

.brand-highlight {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.65);
  color: var(--color-text);
  font-size: 13px;
}

.brand-highlight :deep(svg) {
  color: var(--color-primary);
  flex-shrink: 0;
}

.login-card {
  padding: 26px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(8px);
}

.login-card-header {
  margin-bottom: 4px;
}

.login-logo-inline {
  display: flex;
  align-items: center;
  gap: 10px;
}

.login-logo-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.login-logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.login-logo-title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.login-logo-subtitle {
  font-size: 11.5px;
  color: var(--color-text-muted);
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12.5px;
}

.login-field span {
  color: var(--color-text-muted);
  font-weight: 600;
}

.login-field input {
  padding: 11px 12px;
  border: 1px solid var(--color-border, #d8dbe3);
  border-radius: 10px;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.96);
  transition: border-color 0.14s ease, box-shadow 0.14s ease, background 0.14s ease;
}

.login-field input:focus {
  outline: none;
  border-color: rgba(79, 124, 255, 0.55);
  box-shadow: 0 0 0 4px rgba(79, 124, 255, 0.12);
  background: #fff;
}

.login-submit {
  margin-top: 4px;
  min-height: 42px;
  font-weight: 600;
}

.login-error {
  color: var(--color-danger, #d64545);
  font-size: 12.5px;
  margin: 0;
  line-height: 1.45;
}

.login-error--network {
  color: var(--color-warning, #b8860b);
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-brand {
    order: 2;
  }

  .login-card {
    order: 1;
  }
}

@media (max-width: 560px) {
  .login-screen {
    padding: 16px;
  }

  .login-brand,
  .login-card {
    padding: 20px;
  }

  .login-brand h1 {
    font-size: 24px;
  }

  .brand-highlights {
    grid-template-columns: 1fr;
  }
}
</style>
