<script setup>
import { computed, onMounted } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import { useMeetingsStore } from '../stores/meetingsStore'
import { usePreferencesStore } from '../stores/preferencesStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'

const tasksStore = useTasksStore()
const meetingsStore = useMeetingsStore()
const prefs = usePreferencesStore()
const myTasks = computed(() => tasksStore.myTasksRanked)

onMounted(async () => {
  if (!meetingsStore.loaded) await meetingsStore.load()
})
</script>

<template>
  <div class="view-header">
    <h2>Мои задачи</h2>
    <span class="view-subtitle">Сортировка по актуальности: срочность, срок, недавняя активность</span>
  </div>
  <QuickFiltersBar :task-count="myTasks.length" />
  <!-- Список не подставляется автоматически — задача без списка допустима.
       Автоподстановка listId происходит только внутри конкретного списка (ListView). -->
  <QuickAddTaskRow placeholder="Добавить задачу без привязки к списку..." />
  <label class="meeting-split-toggle">
    <input type="checkbox" :checked="prefs.myTasksGroupByMeeting" @change="prefs.toggle('myTasksGroupByMeeting')" />
    Делить на встречи и подвстречи
  </label>
  <TaskListPanel
    :tasks="myTasks"
    :group-by-meeting="prefs.myTasksGroupByMeeting"
    empty-text="Нет задач, соответствующих текущим фильтрам"
  />
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0 0 2px; font-size: 19px; }
.view-subtitle { font-size: 12.5px; color: var(--color-text-muted); }
.meeting-split-toggle {
  display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px;
  color: var(--color-text-muted); margin: 4px 2px 10px; cursor: pointer; user-select: none;
}
.meeting-split-toggle input { cursor: pointer; }
</style>
