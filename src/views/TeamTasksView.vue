<script setup>
import { computed } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import { useFiltersStore } from '../stores/filtersStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'
import WorkloadChart from '../components/charts/WorkloadChart.vue'

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const filtersStore = useFiltersStore()

const filteredTasks = computed(() => tasksStore.teamTasksRanked)
const visibleTasks = computed(() => filtersStore.apply(filteredTasks.value))
const visibleAssigneeUsers = computed(() => {
  const ids = new Set(visibleTasks.value.map((task) => task.assigneeId).filter(Boolean))
  return usersStore.users.filter((user) => ids.has(user.id))
})
</script>

<template>
  <div class="view-header">
    <h2>Задачи команды</h2>
  </div>
  <QuickFiltersBar
    :task-count="visibleTasks.length"
    :show-search="true"
    :show-recent-done-filters="true"
    :assignee-users="visibleAssigneeUsers"
  />
  <WorkloadChart />
  <TaskListPanel :tasks="filteredTasks" empty-text="Нет задач у команды по текущим фильтрам" />
</template>

<style scoped>
.view-header { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
.view-header h2 { margin: 0; font-size: 19px; }
</style>
