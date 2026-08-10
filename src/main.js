import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import { useAuthStore } from './stores/authStore'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

/**
 * В http-режиме до mount нужно успеть сходить за CSRF-токеном и текущим пользователем,
 * иначе router.beforeEach и App.vue увидят необработанное состояние authStore и возможна
 * гонка между authenticated-shell и /login. В mock-режиме bootstrap() -- no-op
 * (authenticated сразу true), поведение не меняется.
 */
const authStore = useAuthStore()
authStore.bootstrap().finally(() => {
  app.mount('#app')
})
