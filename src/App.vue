<script setup>
import { onMounted, computed } from 'vue'
import { useUsersStore } from './stores/usersStore'
import { useListsStore } from './stores/listsStore'
import { useTasksStore } from './stores/tasksStore'
import { useRecurrenceStore } from './stores/recurrenceStore'
import { useUiStore } from './stores/uiStore'
import { useNotificationsStore } from './stores/notificationsStore'
import AppSidebar from './components/common/AppSidebar.vue'
import AppTopBar from './components/common/AppTopBar.vue'
import TaskDetailPanel from './components/task/TaskDetailPanel.vue'

const usersStore = useUsersStore()
const listsStore = useListsStore()
const tasksStore = useTasksStore()
const recurrenceStore = useRecurrenceStore()
const uiStore = useUiStore()
const notificationsStore = useNotificationsStore()

const openTask = computed(() => uiStore.openTaskId ? tasksStore.byId(uiStore.openTaskId) : null)

onMounted(async () => {
  await usersStore.load()
  await listsStore.load()
  await notificationsStore.load()
  await tasksStore.load()
  await recurrenceStore.load()
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
