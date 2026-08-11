<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useUsersStore } from './stores/usersStore'
import { useListsStore } from './stores/listsStore'
import { useTasksStore } from './stores/tasksStore'
import { useUiStore } from './stores/uiStore'
import { useNotificationsStore } from './stores/notificationsStore'
import { useAuthStore } from './stores/authStore'
import { apiMode } from './repositories'
import { AuthRequiredError } from './repositories/http/apiClient'
import AppSidebar from './components/common/AppSidebar.vue'
import AppTopBar from './components/common/AppTopBar.vue'
import TaskDetailPanel from './components/task/TaskDetailPanel.vue'

const route = useRoute()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const tasksStore = useTasksStore()
const uiStore = useUiStore()
const notificationsStore = useNotificationsStore()
const authStore = useAuthStore()

const openTask = computed(() => uiStore.openTaskId ? tasksStore.byId(uiStore.openTaskId) : null)
// /login -- публичный экран, без sidebar/topbar authenticated-оболочки.
const isPublicScreen = computed(() => route.meta?.public === true)

// Промпт 24: сетевая недоступность backend (fetch reject / TypeError, не 401/403) --
// показываем понятный полноэкранный экран вместо белого экрана/бесконечного спиннера.
const loadFailed = ref(false)

async function retryLoad() {
  loadFailed.value = false
  await loadAuthenticatedData()
}

async function loadAuthenticatedData() {
  try {
    await usersStore.load()
    await listsStore.load()
    await notificationsStore.load()
    await tasksStore.load()
  } catch (err) {
    // AuthRequiredError уже обрабатывается через withPermissionHandling/router в stores,
    // сюда долетают только сетевые сбои (fetch reject, 5xx, backend недоступен).
    if (err instanceof AuthRequiredError) return
    loadFailed.value = true
  }
}

/**
 * в http-режиме authStore.bootstrap() уже вызывался в main.js до mount. Если сессия
 * невалидна (401), router уже перекинул на /login -- в этом случае не нужно тянуть
 * authenticated-только данные (tasks/lists/notifications), иначе получим лишние 401 в консоли.
 * В mock-режиме authenticated всегда true, поведение не меняется.
 */
onMounted(async () => {
  if (apiMode === 'http' && !authStore.authenticated) return
  await loadAuthenticatedData()
})
</script>

<template>
  <router-view v-if="isPublicScreen" />
  <div v-else-if="loadFailed" class="load-error-screen">
    <div class="card load-error-card">
      <h2>Не удаётся связаться с сервером</h2>
      <p>Backend недоступен или произошла сетевая ошибка. Проверьте подключение и повторите попытку.</p>
      <button class="btn btn-sm" type="button" @click="retryLoad">Повторить</button>
    </div>
  </div>
  <template v-else>
    <div class="app-shell">
      <AppSidebar />
      <div class="app-main">
        <AppTopBar />
        <div class="app-content">
          <router-view />
        </div>
      </div>
    </div>
    <TaskDetailPanel v-if="openTask" :task="openTask" @close="uiStore.closeTask()" />
  </template>
</template>

<style scoped>
.load-error-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--color-bg, #f4f5f8); }
.load-error-card { width: 360px; padding: 24px; display: flex; flex-direction: column; gap: 12px; text-align: center; }
.load-error-card h2 { margin: 0; font-size: 17px; }
.load-error-card p { margin: 0; font-size: 13px; color: var(--color-text-secondary, #626a7a); }
</style>
