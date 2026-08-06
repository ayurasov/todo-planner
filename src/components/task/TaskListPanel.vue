<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import TaskRow from './TaskRow.vue'
import QuickToolbar from '../common/QuickToolbar.vue'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { useUiStore } from '../../stores/uiStore'
import { useUsersStore } from '../../stores/usersStore'
import { useListsStore } from '../../stores/listsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { useFiltersStore } from '../../stores/filtersStore'
import { PRIORITY_LABEL } from '../../domain/entities/enums'
import { splitIntoBubbles, BUBBLE_TIER_LABEL } from '../../domain/ranking/bubbleSort'
import { formatDateTime } from '../../utils/formatters'

const props = defineProps({
  tasks: { type: Array, required: true },
  emptyText: { type: String, default: 'Нет задач, соответствующих текущему фильтру' },
  showToolbar: { type: Boolean, default: true },
  // Авто-группировка по встрече (Промпт 5) — это только дефолтное поведение
  // экрана (My Tasks), которое включается, только если пользователь явно не
  // выбрал свой вариант группировки в QuickToolbar (prefs.groupBy). Раньше этот режим
  // безусловно игнорировал prefs.groupBy — из-за этого выбор группировки в
  // тулбаре на экране «Мои задачи» не имел эффекта (см. groups ниже).
  groupByMeeting: { type: Boolean, default: false },
})

const prefs = usePreferencesStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const meetingsStore = useMeetingsStore()
const filtersStore = useFiltersStore()
const uiStore = useUiStore()
const router = useRouter()

function openTask(task) { uiStore.openTask(task.id) }

function goToMeeting(meetingId) {
  router.push(`/meetings/${meetingId}`)
}

const visibleTasks = computed(() => {
  // Быстрые фильтры (QuickFiltersBar / filtersStore) применяются здесь —
  // централизованно, на уровне TaskListPanel — чтобы работать одинаково
  // во ВСЕХ представлениях и списках (Мои задачи, Команда, конкретный
  // список, встреча), а не только там, где явно вызван filtersStore.apply().
  let list = filtersStore.apply(props.tasks)
  const usingBubble = prefs.groupBy === 'bubble' || (props.groupByMeeting && (!prefs.groupBy || prefs.groupBy === 'none'))
  // В режиме "Пузырьки" (в т.ч. авто-группировка по встречам) блок "Выполнено" —
  // часть основного макета, поэтому выполненные задачи не отфильтровываются
  // флагом showCompleted.
  if (!prefs.showCompleted && !usingBubble) {
    list = list.filter((t) => t.status !== 'done' && t.status !== 'cancelled')
  }
  return list
})

const PRIORITY_ORDER = { urgent: 0, high: 1, medium: 2, low: 3 }

function sortTasks(tasks) {
  const dir = prefs.sortDir === 'asc' ? 1 : -1
  // pinned-задачи всегда идут первыми независимо от выбранного поля
  // сортировки — это отдельный, явный сигнал пользователя (📌), который
  // не должен «тонуть» среди обычных полей.
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

const bubbleBlocks = computed(() => {
  const { notDone, done } = splitIntoBubbles(visibleTasks.value)
  return [
    { key: 'not_done', label: `Не выполнено (${notDone.length})`, tasks: notDone, bubble: true },
    { key: 'done', label: `Выполнено (${done.length})`, tasks: done, bubble: true },
  ]
})

/**
 * Группировка "Мои задачи" по встрече (Промпт 5). Задача принадлежит группе
 * своей встречи (task.meetingId), задачи без meetingId попадают в отдельный
 * блок "Без встречи", который всегда идёт последним. Порядок групп-встреч —
 * по дате встречи (более ранние/близкие — выше). Внутри каждой группы
 * применяется сортировка — та же, что выбрана пользователем в QuickFiltersBar
 * (sortTasks), а не жёсткий пузырьковый порядок.
 */
const meetingGroups = computed(() => {
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

  const groupsResult = meetingEntries.map(({ meetingId, meeting, tasks }) => ({
    key: `meeting_${meetingId}`,
    label: meeting ? `Встреча: ${meeting.title}, ${formatDateTime(meeting.date)}` : `Встреча (${meetingId})`,
    meetingId,
    tasks: sortTasks(tasks),
    bubble: true,
    isMeetingGroup: true,
  }))

  if (noMeeting.length) {
    groupsResult.push({ key: 'no_meeting', label: 'Без встречи', tasks: sortTasks(noMeeting), bubble: true })
  }

  return groupsResult
})

const GROUP_KEY_LABEL = {
  status: { open: 'Открыто', in_progress: 'В работе', done: 'Выполнено', cancelled: 'Отменено' },
}

function explicitGroups(sorted) {
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

const groups = computed(() => {
  // Приоритеты (сверху вниз): 1) явный выбор группировки в QuickToolbar
  // (prefs.groupBy из GroupByMode, кроме 'none'), 2) автоматическая группировка по
  // встречам (только на экранах с groupByMeeting), 3) без группировки.
  if (prefs.groupBy === 'bubble') return bubbleBlocks.value
  if (prefs.groupBy && prefs.groupBy !== 'none') return explicitGroups(sortTasks(visibleTasks.value))
  if (props.groupByMeeting) return meetingGroups.value
  return [{ key: null, label: null, tasks: sortTasks(visibleTasks.value) }]
})
</script>

<template>
  <QuickToolbar v-if="showToolbar" :task-count="visibleTasks.length" />

  <div v-for="group in groups" :key="group.key || 'all'" class="group-block" :class="{ 'bubble-block': group.bubble, 'bubble-block-done': group.key === 'done' }">
    <div v-if="group.label" class="group-header" :class="{ 'bubble-header': group.bubble, 'meeting-group-header': group.isMeetingGroup }">
      <span class="group-header-text">{{ group.label }}</span>
      <span v-if="!group.bubble" class="group-count">{{ group.tasks.length }}</span>
      <button v-if="group.isMeetingGroup" class="btn btn-ghost btn-sm meeting-link-btn" @click="goToMeeting(group.meetingId)">Перейти к встрече →</button>
    </div>
    <div class="task-list-panel card" :class="`density-${prefs.density}`">
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
</style>
