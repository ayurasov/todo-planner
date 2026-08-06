<script setup>
import { ref, computed } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import { useListsStore } from '../stores/listsStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import ListSettingsModal from '../components/common/ListSettingsModal.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'

const props = defineProps({ id: { type: String, required: true } })
const tasksStore = useTasksStore()
const listsStore = useListsStore()
const showSettings = ref(false)

const list = computed(() => listsStore.byId(props.id))
const rankedRoots = computed(() => tasksStore.rankedTasksForList(props.id).filter((t) => !t.parentTaskId))
</script>

<template>
  <div class="view-header">
    <div class="view-title">
      <span class="list-icon">{{ list?.settings?.icon || '📋' }}</span>
      <h2>{{ list?.title }}</h2>
    </div>
    <button class="btn btn-sm" @click="showSettings = true">⚙️ Настроить список</button>
  </div>
  <p v-if="list?.description" class="list-description">{{ list.description }}</p>
  <QuickFiltersBar />
  <QuickAddTaskRow :list-id="id" />
  <TaskListPanel :tasks="rankedRoots" empty-text="В этом списке пока нет задач" />
  <ListSettingsModal v-if="showSettings && list" :list="list" @close="showSettings = false" />
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.view-title { display: flex; align-items: center; gap: 8px; }
.view-title h2 { margin: 0; font-size: 19px; }
.list-icon { font-size: 18px; }
.list-description { color: var(--color-text-muted); font-size: 13px; margin-bottom: 14px; }
</style>
