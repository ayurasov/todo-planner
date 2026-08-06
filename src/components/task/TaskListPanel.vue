<script setup>
import { ref, computed } from 'vue'
import TaskRow from './TaskRow.vue'
import TaskDetailPanel from './TaskDetailPanel.vue'
import QuickToolbar from '../common/QuickToolbar.vue'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { useUsersStore } from '../../stores/usersStore'
import { useListsStore } from '../../stores/listsStore'
import { PRIORITY_LABEL } from '../../domain/entities/enums'

const props = defineProps({
  tasks: { type: Array, required: true },
  emptyText: { type: String, default: 'Нет задач, соответствующих текущему фильтру' },
  showToolbar: { type: Boolean, default: true },
})

const prefs = usePreferencesStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const activeTask = ref(null)

function openTask(task) { activeTask.value = task }
function closePanel() { activeTask.value = null }

const visibleTasks = computed(() => {
  let list = props.tasks
  if (!prefs.showCompleted) list = list.filter((t) => t.status !== 'done' && t.status !== 'cancelled')
  return list
})

const PRIORITY_ORDER = { urgent: 0, high: 1, medium: 2, low: 3 }

function sortTasks(tasks) {
  const dir = prefs.sortDir === 'asc' ? 1 : -1
  return [...tasks].sort((a, b) => {
    switch (prefs.sortField) {
      case 'due_date':
        return dir * ((a.dueDate ? new Date(a.dueDate) : Infinity) - (b.dueDate ? new Date(b.dueDate) : Infinity))
      case 'priority':
        return dir * (PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
      case 'created_at':
        return dir * (new Date(a.createdAt) - new Date(b.createdAt))
      case 'updated_at':
        return dir * (new Date(a.updatedAt) - new Date(b.updatedAt))
      case 'title':
        return dir * a.title.localeCompare(b.title)
      default:
        return -dir * ((a.__score ?? 0) - (b.__score ?? 0))
    }
  })
}

const groups = computed(() => {
  const sorted = sortTasks(visibleTasks.value)
  if (prefs.groupBy === 'none') return [{ key: null, label: null, tasks: sorted }]

  const buckets = {}
  const order = []
  for (const task of sorted) {
    let key, label
    switch (prefs.groupBy) {
      case 'status':
        key = task.status; label = { open: 'Открыто', in_progress: 'В работе', done: 'Выполнено', cancelled: 'Отменено' }[task.status]
        break
      case 'priority':
        key = task.priority; label = PRIORITY_LABEL[task.priority]
        break
      case 'assignee':
        key = task.assigneeId || 'none'; label = task.assigneeId ? usersStore.byId(task.assigneeId)?.name : 'Без исполнителя'
        break
      case 'list':
        key = task.listId; label = listsStore.byId(task.listId)?.title || task.listId
        break
      case 'due_date':
        key = task.dueDate ? task.dueDate.slice(0, 10) : 'none'; label = task.dueDate ? new Date(task.dueDate).toLocaleDateString('ru-RU') : 'Без срока'
        break
      case 'tag':
        key = task.tags?.[0] || 'none'; label = task.tags?.[0] || 'Без тега'
        break
      default:
        key = 'all'; label = null
    }
    if (!buckets[key]) { buckets[key] = { key, label, tasks: [] }; order.push(key) }
    buckets[key].tasks.push(task)
  }
  return order.map((k) => buckets[k])
})
</script>

<template>
  <QuickToolbar v-if="showToolbar" :task-count="visibleTasks.length" />

  <div v-for="group in groups" :key="group.key || 'all'" class="group-block">
    <div v-if="group.label" class="group-header">{{ group.label }} <span class="group-count">{{ group.tasks.length }}</span></div>
    <div class="task-list-panel card" :class="`density-${prefs.density}`">
      <div v-if="!group.tasks.length" class="empty-state">{{ emptyText }}</div>
      <TransitionGroup v-else name="fade" tag="div" class="task-list-body">
        <TaskRow v-for="task in group.tasks" :key="task.id" :task="task" class="fade-move" @open="openTask" />
      </TransitionGroup>
    </div>
  </div>

  <TaskDetailPanel v-if="activeTask" :task="activeTask" @close="closePanel" />
</template>

<style scoped>
.group-block { margin-bottom: 16px; }
.group-header { font-size: 12.5px; font-weight: 600; color: var(--color-text-muted); padding: 4px 2px 8px; display: flex; align-items: center; gap: 6px; }
.group-count { background: #eef1f7; border-radius: 10px; padding: 1px 7px; font-size: 11px; font-weight: 600; }
.task-list-panel { overflow: hidden; }
.empty-state { padding: 40px 20px; text-align: center; color: var(--color-text-muted); font-size: 13.5px; }
</style>
