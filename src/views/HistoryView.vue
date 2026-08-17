<script setup>
import { onMounted, computed, ref } from 'vue'
import { useHistoryStore } from '../stores/historyStore'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import { useUiStore } from '../stores/uiStore'
import { formatDateTime, stripHtml, truncateText } from '../utils/formatters'
import { PRIORITY_LABEL } from '../domain/entities/enums'
import ActivityChart from '../components/charts/ActivityChart.vue'
import AppIcon from '../components/common/AppIcon.vue'

const historyStore = useHistoryStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const uiStore = useUiStore()

onMounted(async () => {
  if (!usersStore.loaded) await usersStore.load()
  const taskIds = tasksStore.tasks.map((t) => t.id)
  await historyStore.loadGlobalLog(taskIds)
})

const filterActor = ref('')
const filterType = ref('')

const taskTitle = (taskId) => tasksStore.byId(taskId)?.title || taskId

// Задачи в приложении открываются глобальной модалкой (App.vue слушает
// uiStore.openTaskId), а не отдельным маршрутом. Ссылка на "/lists/<listId>"
// вела в неправильное место, а для задач без listId (например, привязанных
// только к встрече) превращалась в /lists/undefined и переход не срабатывал
// вовсе. Открываем задачу так же, как это делает TaskListPanel/TaskRow.
function openTaskDetail(taskId) {
  if (!tasksStore.byId(taskId)) return
  uiStore.openTask(taskId)
}

const HISTORY_LABEL = {
  created: 'создал(а) задачу', field_changed: 'изменил(а)', commented: 'оставил(а) комментарий',
  assignee_changed: 'сменил(а) исполнителя', rescheduled: 'перенёс(ла) срок', completed: 'выполнил(а) задачу', reopened: 'вернул(а) в работу',
}

const FIELD_LABEL = {
  title: 'название', description: 'описание', status: 'статус', priority: 'приоритет',
  dueDate: 'срок', startDate: 'дату начала', tags: 'теги', pinned: 'закрепление',
}

function userName(id) {
  return usersStore.byId(id)?.name || historyStore.actorName(id)
}

// Поля, хранящие rich-text (HTML из редактора) — в истории их нужно
// показывать как обычный текст без тегов, иначе в диффе видны <div>, <br>
// и прочая разметка редактора.
const RICH_TEXT_FIELDS = new Set(['description'])

function formatValue(field, value) {
  if (RICH_TEXT_FIELDS.has(field)) {
    const plain = stripHtml(value)
    return plain ? truncateText(plain, 80) : '—'
  }
  if (value === null || value === undefined || value === '') return '—'
  if (field === 'dueDate' || field === 'startDate') return formatDateTime(value)
  if (field === 'priority') return PRIORITY_LABEL[value] || value
  if (field === 'assigneeId') return userName(value)
  if (Array.isArray(value)) return value.length ? value.join(', ') : '—'
  if (typeof value === 'boolean') return value ? 'да' : 'нет'
  return String(value)
}

const filteredLog = computed(() => historyStore.globalLog.filter((e) => {
  if (filterActor.value && e.actorId !== filterActor.value) return false
  if (filterType.value && e.type !== filterType.value) return false
  return true
}))

const actorOptions = computed(() => {
  const ids = new Set(historyStore.globalLog.map((e) => e.actorId))
  return usersStore.users.filter((u) => ids.has(u.id))
})
</script>

<template>
  <div class="view-header">
    <h2>История и активность</h2>
    <router-link to="/analytics" class="analytics-link"><AppIcon name="chart" :size="14" /> Полная аналитика</router-link>
  </div>
  <ActivityChart />

  <div class="log-filters">
    <select v-model="filterActor">
      <option value="">Все авторы</option>
      <option v-for="u in actorOptions" :key="u.id" :value="u.id">{{ u.name }}</option>
    </select>
    <select v-model="filterType">
      <option value="">Все события</option>
      <option v-for="(label, type) in HISTORY_LABEL" :key="type" :value="type">{{ label }}</option>
    </select>
  </div>

  <div class="card global-log scroll-thin">
    <div v-for="entry in filteredLog" :key="entry.id" class="log-row">
      <div class="log-main">
        <span class="actor">{{ userName(entry.actorId) }}</span>
        <span class="action">
          {{ HISTORY_LABEL[entry.type] || entry.type }}
          <template v-if="entry.type === 'field_changed'">{{ FIELD_LABEL[entry.field] || entry.field }}</template>
        </span>
        <button type="button" class="task-link" @click="openTaskDetail(entry.taskId)">«{{ taskTitle(entry.taskId) }}»</button>
        <span class="log-time">{{ formatDateTime(entry.timestamp) }}</span>
      </div>
      <div v-if="entry.type === 'field_changed' || entry.type === 'assignee_changed' || entry.type === 'rescheduled'" class="log-diff">
        <span class="diff-old">{{ formatValue(entry.type === 'assignee_changed' ? 'assigneeId' : entry.field, entry.oldValue) }}</span>
        <AppIcon name="chevronRight" :size="11" />
        <span class="diff-new">{{ formatValue(entry.type === 'assignee_changed' ? 'assigneeId' : entry.field, entry.newValue) }}</span>
      </div>
      <div v-if="entry.type === 'commented' && entry.comment" class="log-comment">«{{ entry.comment }}»</div>
    </div>
    <div v-if="!filteredLog.length" class="empty-state">Пока нет активности</div>
  </div>
</template>

<style scoped>
.view-header { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
.view-header h2 { margin: 0; font-size: 19px; }
.analytics-link { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--color-primary-dark); text-decoration: none; font-weight: 600; }
.analytics-link:hover { text-decoration: underline; }
.log-filters { display: flex; gap: 8px; margin: 12px 0; }
.log-filters select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 8px; font-size: 12.5px; background: var(--color-surface); }
.global-log { max-height: 520px; overflow-y: auto; }
.log-row { padding: 10px 14px; border-bottom: 1px solid var(--color-border); font-size: 13px; }
.log-main { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }
.actor { font-weight: 600; }
.task-link {
  color: var(--color-primary-dark); text-decoration: none; background: none; border: none;
  padding: 0; font: inherit; cursor: pointer;
}
.task-link:hover { text-decoration: underline; }
.log-time { margin-left: auto; color: var(--color-text-muted); font-size: 11.5px; }
.log-diff { display: flex; align-items: center; gap: 6px; margin-top: 4px; font-size: 12px; color: var(--color-text-muted); padding-left: 2px; }
.diff-old { text-decoration: line-through; opacity: 0.75; }
.diff-new { font-weight: 600; color: var(--color-text); }
.log-comment { margin-top: 4px; font-size: 12.5px; color: var(--color-text-muted); padding-left: 2px; }
.empty-state { padding: 30px; text-align: center; color: var(--color-text-muted); }
</style>
