<script setup>
// Компактная нередактируемая строка задачи для блока "Все задачи подвстречи"
// внутри модалки подвстречи (MeetingDetailView). В отличие от TaskRow, клик по
// названию НЕ открывает TaskDetailPanel — открыть детали задачи здесь нельзя,
// доступны только быстрые кнопки: чекбокс выполнения, срок и приоритет.
import { computed } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { relativeDay, isOverdue } from '../../utils/formatters'
import { useTaskPermissions } from '../../composables/usePermissions'
import { getInitials, getAvatarColor } from '../../utils/avatar'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({ task: { type: Object, required: true } })

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const { canToggleStatus, canEditThisTask } = useTaskPermissions(() => props.task)

const assignee = computed(() => usersStore.byId(props.task.assigneeId))
const isDone = computed(() => props.task.status === 'done')
const overdue = computed(() => isOverdue(props.task.dueDate, props.task.status))

const PRIORITY_COLOR = { low: '#9aa3b2', medium: '#4f7cff', high: '#e8a13a', urgent: '#e5484d' }
const PRIORITY_LABEL = { low: 'Низкий', medium: 'Средний', high: 'Высокий', urgent: 'Срочный' }
const PRIORITIES = ['low', 'medium', 'high', 'urgent']

function toggleComplete() {
  if (!canToggleStatus.value) return
  if (isDone.value) tasksStore.reopenTask(props.task.id)
  else tasksStore.completeTask(props.task.id)
}

function cyclePriority() {
  if (!canEditThisTask.value) return
  const idx = PRIORITIES.indexOf(props.task.priority)
  const next = PRIORITIES[(idx + 1) % PRIORITIES.length]
  tasksStore.updateTaskField(props.task.id, 'priority', next)
}

function snooze() {
  if (!canEditThisTask.value) return
  const d = new Date(props.task.dueDate || new Date())
  d.setDate(d.getDate() + 1)
  tasksStore.rescheduleTask(props.task.id, d.toISOString())
}
</script>

<template>
  <div class="occ-glance-row" :class="{ done: isDone }" :style="{ borderLeftColor: PRIORITY_COLOR[task.priority], borderLeftWidth: '9px' }">
    <input
      type="checkbox" :checked="isDone" class="occ-glance-checkbox"
      :disabled="!canToggleStatus"
      :title="canToggleStatus ? '' : 'Недостаточно прав для изменения статуса'"
      @change="toggleComplete"
    />
    <span class="occ-glance-title" :title="'Открыть детали задачи можно только из общего списка задач'">{{ task.title }}</span>
    <span v-if="task.dueDate" class="occ-glance-date" :class="{ overdue }"><AppIcon name="calendar" :size="11" /> {{ relativeDay(task.dueDate) }}</span>
    <button
      class="occ-glance-priority" :style="{ background: PRIORITY_COLOR[task.priority] }"
      :disabled="!canEditThisTask" title="Быстро изменить приоритет (без открытия деталей)"
      @click.stop="cyclePriority"
    >{{ PRIORITY_LABEL[task.priority] }}</button>
    <button v-if="canEditThisTask && !isDone" class="btn btn-ghost btn-sm occ-glance-snooze" title="Отложить на день" @click.stop="snooze"><AppIcon name="alarm" :size="12" /></button>
    <span v-if="assignee" class="occ-glance-avatar" :style="{ background: getAvatarColor(assignee.name) }" :title="assignee.name">{{ getInitials(assignee.name) }}</span>
  </div>
</template>

<style scoped>
.occ-glance-row {
  display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  border-bottom: 1px solid var(--color-border); border-left: 0 solid transparent;
  background: var(--color-surface); font-size: 12.5px;
}
.occ-glance-row:last-child { border-bottom: none; }
.occ-glance-row.done { opacity: 0.65; }
.occ-glance-row.done .occ-glance-title { text-decoration: line-through; color: var(--color-text-muted); }
.occ-glance-checkbox { accent-color: var(--color-primary); cursor: pointer; flex-shrink: 0; }
.occ-glance-checkbox:disabled { cursor: not-allowed; opacity: 0.45; }
.occ-glance-title { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: default; }
.occ-glance-date { font-size: 11px; color: var(--color-text-muted); display: inline-flex; align-items: center; gap: 3px; white-space: nowrap; }
.occ-glance-date.overdue { color: var(--color-danger); font-weight: 600; }
.occ-glance-priority {
  border: none; border-radius: 999px; color: #fff; font-size: 10.5px; font-weight: 600;
  padding: 2px 8px; cursor: pointer; flex-shrink: 0;
}
.occ-glance-priority:disabled { cursor: default; opacity: 0.85; }
.occ-glance-snooze { flex-shrink: 0; }
.occ-glance-avatar {
  width: 20px; height: 20px; border-radius: 50%; color: #fff; font-size: 9px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
</style>
