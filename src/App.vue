<script setup>
import { onMounted } from 'vue'
import { useUsersStore } from './stores/usersStore'
import { useListsStore } from './stores/listsStore'
import { useTasksStore } from './stores/tasksStore'
import { useRecurrenceStore } from './stores/recurrenceStore'
import AppSidebar from './components/common/AppSidebar.vue'
import AppTopBar from './components/common/AppTopBar.vue'

const usersStore = useUsersStore()
const listsStore = useListsStore()
const tasksStore = useTasksStore()
const recurrenceStore = useRecurrenceStore()

onMounted(async () => {
  await usersStore.load()
  await listsStore.load()
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
</template>
