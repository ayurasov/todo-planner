<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import TaskRow from './TaskRow.vue'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { useUiStore } from '../../stores/uiStore'
import { useUsersStore } from '../../stores/usersStore'
import { useListsStore } from '../../stores/listsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { useFiltersStore } from '../../stores/filtersStore'
import { PRIORITY_LABEL } from '../../domain/entities/enums'
import { splitIntoBubbles } from '../../domain/ranking/bubbleSort'
import { formatDateTime } from '../../utils/formatters'

const props = defineProps({
  tasks: { type: Array, required: true },
  emptyText: { type: String, default: 'Нет задач, соответствующих текущему фильтру' },
  showToolbar: { type: Boolean, default: true },
  groupByMeeting: { type: Boolean, default: false },
  // Экран встречи требует отдельной UX-настройки: в обычном режиме
  // («Группировка») показываем только сортировку «Обновлено».
  meetingMode: { type: Boolean, default: false },
})

const prefs = usePreferencesStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const meetingsStore = useMeetingsStore()
const filtersStore = useFiltersStore()
const uiStore = useUiStore()
const router = useRouter()

function openTask(task) { uiStore.openTask(task.id) }
function goToMeeting(meetingId) { router.push(`/meetings/${meetingId}`) }

const visibleTasks = computed(() => {
  let list = filtersStore.apply(props.tasks)
  const usingBubble = prefs.groupBy === 'bubble'
  if (!prefs.showCompleted && !usingBubble) {
    list = list.filter((t) => t.status !== 'done' && t.status !== 'cancelled')
  }
  return list
})

const PRIORITY_ORDER = { urgent: 0, high: 1, medium: 2, low: 3 }

function sortTasks(tasks) {
  const dir = prefs.sortDir === 'asc' ? 1 : -1
  return [...tasks].sort((a, b) => {
    if (!!a.pinned !== !!b.pinned) return a.pinned ? -1 : 1
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

function buildBubbleBlocks(tasks) {
  const { notDone, done } = splitIntoBubbles(tasks)
  const blocks = []
  if (filtersStore.status !== 'done' && notDone.length) {
    blocks.push({ key: 'not_done', label: `Не выполнено (${notDone.length})`, tasks: notDone, bubble: true })
  }
  if (filtersStore.status !== 'not_done' && done.length) {
    blocks.push({ key: 'done', label: `Выполнено (${done.length})`, tasks: done, bubble: true })
  }
  return blocks
}

const GROUP_KEY_LABEL = {
  status: { open: 'Не начато', in_progress: 'В работе', done: 'Выполнено', cancelled: 'Отменено' },
}

function buildExplicitGroups(tasks) {
  const sorted = sortTasks(tasks)
  const buckets = {}
  const order = []
  for (const task of sorted) {
    let key, label
    switch (prefs.groupBy) {
      case 'status':
        key = task.status; label = GROUP_KEY_LABEL.status[task.status]
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
}

function buildSubgroups(tasks) {
  if (prefs.groupBy === 'bubble') return buildBubbleBlocks(tasks)
  if (prefs.groupBy && prefs.groupBy !== 'none') return buildExplicitGroups(tasks)
  return null
}

const meetingTopGroups = computed(() => {
  const byMeeting = {}
  const noMeeting = []
  for (const task of visibleTasks.value) {
    if (task.meetingId) {
      if (!byMeeting[task.meetingId]) byMeeting[task.meetingId] = []
      byMeeting[task.meetingId].push(task)
    } else {
      noMeeting.push(task)
    }
  }

  const meetingEntries = Object.entries(byMeeting)
    .map(([meetingId, tasks]) => ({ meetingId, meeting: meetingsStore.meetingById(meetingId), tasks }))
    .sort((a, b) => {
      if (!a.meeting) return 1
      if (!b.meeting) return -1
      return new Date(a.meeting.date) - new Date(b.meeting.date)
    })

  const result = meetingEntries.map(({ meetingId, meeting, tasks }) => {
    const subgroups = buildSubgroups(tasks)
    return {
      key: `meeting_${meetingId}`,
      label: meeting ? `Встреча: ${meeting.title}, ${formatDateTime(meeting.date)}` : `Встреча (${meetingId})`,
      meetingId,
      tasks: subgroups ? null : sortTasks(tasks),
      subgroups,
      bubble: false,
      isMeetingGroup: true,
    }
  })

  if (noMeeting.length) {
    const subgroups = buildSubgroups(noMeeting)
    result.push({
      key: 'no_meeting',
      label: 'Без встречи',
      tasks: subgroups ? null : sortTasks(noMeeting),
      subgroups,
      bubble: false,
      isMeetingGroup: true,
    })
  }

  return result
})

const groups = computed(() => {
  if (props.groupByMeeting) return meetingTopGroups.value
  const subgroups = buildSubgroups(visibleTasks.value)
  if (subgroups) return subgroups
  return [{ key: null, label: null, tasks: sortTasks(visibleTasks.value) }]
})
</script>

<template>
  <div v-for="group in groups" :key="group.key || 'all'" class="group-block" :class="{ 'bubble-block': group.bubble, 'bubble-block-done': group.key === 'done' }">
    <div v-if="group.label" class="group-header" :class="{ 'bubble-header': group.bubble, 'meeting-group-header': group.isMeetingGroup }">
      <span class="group-header-text">{{ group.label }}</span>
      <span v-if="!group.bubble" class="group-count">{{ (group.tasks || group.subgroups.flatMap(s => s.tasks)).length }}</span>
      <button v-if="group.isMeetingGroup && group.meetingId" class="btn btn-ghost btn-sm meeting-link-btn" @click="goToMeeting(group.meetingId)">Перейти к встрече →</button>
    </div>

    <template v-if="group.subgroups">
      <div v-for="sub in group.subgroups" :key="sub.key" class="subgroup-block" :class="{ 'bubble-block': sub.bubble, 'bubble-block-done': sub.key === 'done' }">
        <div v-if="sub.label" class="group-header subgroup-header" :class="{ 'bubble-header': sub.bubble }">
          <span class="group-header-text">{{ sub.label }}</span>
          <span v-if="!sub.bubble" class="group-count">{{ sub.tasks.length }}</span>
        </div>
        <div class="task-list-panel card" :class="`density-${prefs.density}`">
          <div v-if="!sub.tasks.length" class="empty-state">{{ emptyText }}</div>
          <TransitionGroup v-else name="fade" tag="div" class="task-list-body">
            <TaskRow v-for="task in sub.tasks" :key="task.id" :task="task" :bubble-mode="sub.bubble" class="fade-move" @open="openTask" />
          </TransitionGroup>
        </div>
      </div>
    </template>
    <div v-else class="task-list-panel card" :class="`density-${prefs.density}`">
      <div v-if="!group.tasks.length" class="empty-state">{{ emptyText }}</div>
      <TransitionGroup v-else name="fade" tag="div" class="task-list-body">
        <TaskRow v-for="task in group.tasks" :key="task.id" :task="task" :bubble-mode="group.bubble" class="fade-move" @open="openTask" />
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.group-block { margin-bottom: 16px; }
.group-header { font-size: 12.5px; font-weight: 600; color: var(--color-text-muted); padding: 4px 2px 8px; display: flex; align-items: center; gap: 6px; }
.group-count { background: #eef1f7; border-radius: 10px; padding: 1px 7px; font-size: 11px; font-weight: 600; }
.task-list-panel { overflow: hidden; }
.empty-state { padding: 40px 20px; text-align: center; color: var(--color-text-muted); font-size: 13.5px; }
.bubble-header { font-size: 13.5px; text-transform: uppercase; letter-spacing: 0.03em; padding: 6px 2px 10px; }
.bubble-block-done .bubble-header { color: var(--color-text-muted); opacity: 0.8; }
.bubble-block:not(.bubble-block-done) .bubble-header { color: var(--color-danger); }
.meeting-group-header { color: var(--color-text) !important; justify-content: space-between; text-transform: none; letter-spacing: normal; font-size: 13px; background: #eef1f7; border-radius: 8px; padding: 8px 10px; }
.group-header-text { display: flex; align-items: center; gap: 6px; }
.meeting-link-btn { flex-shrink: 0; white-space: nowrap; }
.subgroup-block { margin-left: 6px; margin-bottom: 10px; }
.subgroup-header { padding: 4px 2px 6px 10px; }
</style>
