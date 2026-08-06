<script setup>
import { computed } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'
import WorkloadChart from '../components/charts/WorkloadChart.vue'

const tasksStore = useTasksStore()

const filteredTasks = computed(() => tasksStore.teamTasksRanked)
</script>

<template>
  <div class="view-header">
    <h2>Задачи команды</h2>
  </div>
  <QuickFiltersBar />
  <WorkloadChart />
  <TaskListPanel :tasks="filteredTasks" empty-text="Нет задач у команды по текущим фильтрам" />
</template>

<style scoped>
.view-header { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
.view-header h2 { margin: 0; font-size: 19px; }
</style>
