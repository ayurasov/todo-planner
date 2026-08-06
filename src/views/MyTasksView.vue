<script setup>
import { computed } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import { useListsStore } from '../stores/listsStore'
import { useFiltersStore } from '../stores/filtersStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'

const tasksStore = useTasksStore()
const listsStore = useListsStore()
const filtersStore = useFiltersStore()
const myTasks = computed(() => filtersStore.apply(tasksStore.myTasksRanked))
const defaultListId = computed(() => listsStore.lists[0]?.id)
</script>

<template>
  <div class="view-header">
    <h2>Мои задачи</h2>
    <span class="view-subtitle">Сортировка по актуальности: срочность, срок, недавняя активность</span>
  </div>
  <QuickFiltersBar />
  <QuickAddTaskRow v-if="defaultListId" :list-id="defaultListId" placeholder="Добавить задачу в первый доступный список..." />
  <TaskListPanel :tasks="myTasks" empty-text="Нет задач, соответствующих текущим фильтрам" />
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0 0 2px; font-size: 19px; }
.view-subtitle { font-size: 12.5px; color: var(--color-text-muted); }
</style>
