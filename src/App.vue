<script setup>
import { onMounted, computed } from 'vue'
import { useUsersStore } from './stores/usersStore'
import { useListsStore } from './stores/listsStore'
import { useTasksStore } from './stores/tasksStore'
import { useUiStore } from './stores/uiStore'
import { useNotificationsStore } from './stores/notificationsStore'
import { useAuthStore } from './stores/authStore'
import { apiMode } from './repositories'
import AppSidebar from './components/common/AppSidebar.vue'
import AppTopBar from './components/common/AppTopBar.vue'
import TaskDetailPanel from './components/task/TaskDetailPanel.vue'

const usersStore = useUsersStore()
const listsStore = useListsStore()
const tasksStore = useTasksStore()
const uiStore = useUiStore()
const notificationsStore = useNotificationsStore()
const authStore = useAuthStore()

const openTask = computed(() => uiStore.openTaskId ? tasksStore.byId(uiStore.openTaskId) : null)

/**
 * в http-режиме authStore.bootstrap() уже вызывался в main.js до mount. Если сессия
 * невалидна (401), router уже перекинул на /login -- в этом случае не нужно тянуть
 * authenticated-только данные (tasks/lists/notifications), иначе получим лишние 401 в консоли.
 * В mock-режиме authenticated всегда true, поведение не меняется.
 */
onMounted(async () => {
  if (apiMode === 'http' && !authStore.authenticated) return
  await usersStore.load()
  await listsStore.load()
  await notificationsStore.load()
  await tasksStore.load()
})
</script>

<template>
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
