<script setup>
import { ref, computed } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import WorkloadChart from '../components/charts/WorkloadChart.vue'

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const filterAssignee = ref(null)

const filteredTasks = computed(() => {
  let tasks = tasksStore.teamTasksRanked
  if (filterAssignee.value) tasks = tasks.filter((t) => t.assigneeId === filterAssignee.value)
  return tasks
})
</script>

<template>
  <div class="view-header">
    <h2>Задачи команды</h2>
    <select v-model="filterAssignee" class="assignee-filter">
      <option :value="null">Все исполнители</option>
      <option v-for="u in usersStore.users" :key="u.id" :value="u.id">{{ u.name }}</option>
    </select>
  </div>
  <WorkloadChart />
  <TaskListPanel :tasks="filteredTasks" empty-text="Нет задач у команды по текущему фильтру" />
</template>

<style scoped>
.view-header { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
.view-header h2 { margin: 0; font-size: 19px; }
.assignee-filter { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 10px; }
</style>
