<script setup>
import { onMounted, computed } from 'vue'
import { useHistoryStore } from '../stores/historyStore'
import { useTasksStore } from '../stores/tasksStore'
import { formatDateTime } from '../utils/formatters'
import ActivityChart from '../components/charts/ActivityChart.vue'

const historyStore = useHistoryStore()
const tasksStore = useTasksStore()

onMounted(async () => {
  const taskIds = tasksStore.tasks.map((t) => t.id)
  await historyStore.loadGlobalLog(taskIds)
})

const taskTitle = (taskId) => tasksStore.byId(taskId)?.title || taskId

const HISTORY_LABEL = {
  created: 'создал(а) задачу', field_changed: 'изменил(а) поле', commented: 'оставил(а) комментарий',
  assignee_changed: 'сменил(а) исполнителя', rescheduled: 'перенёс(ла) срок', completed: 'выполнил(а) задачу', reopened: 'вернул(а) в работу',
}
</script>

<template>
  <div class="view-header"><h2>История и активность</h2></div>
  <ActivityChart />
  <div class="card global-log scroll-thin">
    <div v-for="entry in historyStore.globalLog" :key="entry.id" class="log-row">
      <span class="actor">{{ historyStore.actorName(entry.actorId) }}</span>
      <span class="action">{{ HISTORY_LABEL[entry.type] || entry.type }}</span>
      <span class="task-link">«{{ taskTitle(entry.taskId) }}»</span>
      <span class="log-time">{{ formatDateTime(entry.timestamp) }}</span>
    </div>
    <div v-if="!historyStore.globalLog.length" class="empty-state">Пока нет активности</div>
  </div>
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.global-log { margin-top: 14px; max-height: 460px; overflow-y: auto; }
.log-row { display: flex; gap: 8px; padding: 10px 14px; border-bottom: 1px solid var(--color-border); font-size: 13px; align-items: baseline; flex-wrap: wrap; }
.actor { font-weight: 600; }
.log-time { margin-left: auto; color: var(--color-text-muted); font-size: 11.5px; }
.empty-state { padding: 30px; text-align: center; color: var(--color-text-muted); }
</style>
