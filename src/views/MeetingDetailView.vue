<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingsStore } from '../stores/meetingsStore'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import { useListsStore } from '../stores/listsStore'
import { usePreferencesStore } from '../stores/preferencesStore'
import { useFiltersStore } from '../stores/filtersStore'
import { useIsAdmin } from '../composables/usePermissions'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'
import AppIcon from '../components/common/AppIcon.vue'
import RichTextEditor from '../components/common/RichTextEditor.vue'
import ConfirmModal from '../components/common/ConfirmModal.vue'
import UserMultiSelect from '../components/common/UserMultiSelect.vue'
import { formatDateTime, formatTime, formatMeetingRecurrence } from '../utils/formatters'
import { meetingSummaryParser, MATCHED_PATTERN_LABEL } from '../services/MeetingSummaryParser'
import { meetingOccurrenceService } from '../services/MeetingOccurrenceService'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const meetingsStore = useMeetingsStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const prefs = usePreferencesStore()
const filtersStore = useFiltersStore()
const isAdmin = useIsAdmin()

const editing = ref(false)
const editDraft = ref({
  title: '', date: '', time: '', description: '', link: '', attendeeIds: [], editorIds: [], color: '#4f7cff',
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})



const showSummaryParser = ref(false)
const summaryText = ref('')
const parsedCandidates = ref([])
const parseAttempted = ref(false)
const selectedSummaryOccurrenceId = ref('all')

const activeOccurrence = ref(null)
const occurrenceDraft = ref({ description: '', link: '' })
const occurrenceEditing = ref(false)
const expandedOccurrenceIds = ref([])

const addingOccurrence = ref(false)
const newOccurrenceDraft = ref({ date: '', time: '', description: '', link: '' })

// Все подтверждения удаления на странице встречи теперь через единый ConfirmModal.
const occurrencePendingRemoval = ref(null)
const meetingPendingRemoval = ref(false)

const WEEKDAY_OPTIONS = [
  { value: 1, label: 'Пн' },
  { value: 2, label: 'Вт' },
  { value: 3, label: 'Ср' },
  { value: 4, label: 'Чт' },
  { value: 5, label: 'Пт' },
  { value: 6, label: 'Сб' },
  { value: 0, label: 'Вс' },
]

onMounted(async () => {
  if (!meetingsStore.loaded) await meetingsStore.load()
  if (!tasksStore.loaded) await tasksStore.load()
  if (!listsStore.loaded) await listsStore.load()
  if (!usersStore.loaded) await usersStore.load()
  // Группировка по исполнителю внутри подвстреч больше не форсируется —
  // задачи каждой подвстречи показываются простым списком без лишней
  // иерархии; пользователь может сам включить нужную группировку в
  // QuickFiltersBar/QuickToolbar, если это понадобится.
  if (isRecurring.value) {
    filtersStore.setStatus('all')
  }
})

const meeting = computed(() => meetingsStore.meetingById(props.id))
const author = computed(() => (meeting.value ? usersStore.byId(meeting.value.createdBy) : null))
const isRecurring = computed(() => !!meeting.value?.recurrence?.freq)
const meetingTypeIcon = computed(() => (isRecurring.value ? 'repeat' : 'calendar'))
const meetingTypeTitle = computed(() => (isRecurring.value ? 'Регулярная встреча' : 'Разовая встреча'))
const meetingTasks = computed(() => tasksStore.tasks.filter((t) => t.meetingId === props.id && !t.parentTaskId))
const attendees = computed(() => (meeting.value?.attendeeIds || []).map((id) => usersStore.byId(id)).filter(Boolean))
const recurrenceLabel = computed(() => formatMeetingRecurrence(meeting.value?.recurrence))
const occurrences = computed(() => meetingsStore.occurrencesOf(props.id))

function occurrenceTitle(occ) {
  return `${meeting.value?.title || ''} · ${formatDateTime(occ.date)}`
}

function isOccurrenceExpanded(occId) {
  return expandedOccurrenceIds.value.includes(occId)
}

function toggleOccurrenceExpanded(occId) {
  if (isOccurrenceExpanded(occId)) {
    expandedOccurrenceIds.value = expandedOccurrenceIds.value.filter((id) => id !== occId)
  } else {
    expandedOccurrenceIds.value = [...expandedOccurrenceIds.value, occId]
  }
}

const seriesTasksWithoutOccurrence = computed(() => {
  if (!isRecurring.value) return []
  return recurringVisibleTasks.value.filter((t) => !t.occurrenceId)
})

/**
 * Задачи, вообще не привязанные ни к какой встрече (t.meetingId пусто), но
 * находящиеся в тех же списках, где есть задачи этой серии встреч. Требование:
 * бейдж "НЕ ВЫПОЛНЕНО В СЕРИИ ВСТРЕЧ" должен также учитывать такие задачи —
 * то есть незавершённые задачи без привязки к встрече в списках, связанных с
 * этой серией, а не только задачи с meetingId === props.id.
 */
const relatedListIds = computed(() => new Set(meetingTasks.value.map((t) => t.listId).filter(Boolean)))

const standaloneUnfinishedTasks = computed(() => {
  if (!isRecurring.value) return []
  if (!relatedListIds.value.size) return []
  return tasksStore.tasks.filter((t) => (
    !t.parentTaskId
    && !t.meetingId
    && relatedListIds.value.has(t.listId)
    && t.status !== 'done' && t.status !== 'cancelled'
  )).sort((a, b) => new Date(a.updatedAt || a.createdAt || 0) - new Date(b.updatedAt || b.createdAt || 0))
})

const unfinishedGroupsByOccurrence = computed(() => {
  if (!isRecurring.value) return []
  const orderMap = new Map(occurrences.value.map((o, index) => [o.id, index]))
  return occurrences.value
    .map((occ) => {
      const tasks = meetingTasks.value
        .filter((t) => t.occurrenceId === occ.id && t.status !== 'done' && t.status !== 'cancelled')
        .sort((a, b) => new Date(a.updatedAt || a.createdAt || 0) - new Date(b.updatedAt || b.createdAt || 0))
      return { occurrence: occ, tasks, count: tasks.length, order: orderMap.get(occ.id) ?? 0 }
    })
    .filter((g) => g.count)
    .sort((a, b) => a.order - b.order)
})

const unfinishedTotalCount = computed(() => (
  unfinishedGroupsByOccurrence.value.reduce((sum, g) => sum + g.count, 0) + standaloneUnfinishedTasks.value.length
))

const filteredMeetingTasks = computed(() => filtersStore.apply(meetingTasks.value))
const recurringVisibleTasks = computed(() => {
  if (!isRecurring.value) return []
  let list = filteredMeetingTasks.value
  const usingBubble = prefs.groupBy === 'bubble'
  if (!prefs.showCompleted && !usingBubble) {
    list = list.filter((t) => t.status !== 'done' && t.status !== 'cancelled')
  }
  return list
})

const occurrenceGroups = computed(() => {
  if (!isRecurring.value) return []
  const orderMap = new Map(occurrences.value.map((o, index) => [o.id, index]))
  return occurrences.value
    .map((occ) => ({
      occurrence: occ,
      tasks: recurringVisibleTasks.value.filter((t) => t.occurrenceId === occ.id),
      order: orderMap.get(occ.id) ?? 0,
    }))
    .sort((a, b) => a.order - b.order)
})

const canManageMeeting = computed(() => {
  if (!meeting.value) return false
  if (isAdmin.value) return true
  if (meeting.value.createdBy === usersStore.currentUser?.id) return true
  const listIdsOfMeetingTasks = new Set(meetingTasks.value.map((t) => t.listId).filter(Boolean))
  for (const listId of listIdsOfMeetingTasks) {
    const role = listsStore.memberships[listId]?.find((m) => m.userId === usersStore.currentUser?.id)?.role
    if (role === 'owner' || role === 'editor') return true
  }
  return false
})

const summaryOccurrenceOptions = computed(() => occurrences.value.map((o) => ({ id: o.id, label: occurrenceTitle(o) })))

function openOccurrence(occ) {
  activeOccurrence.value = occ
  occurrenceDraft.value = { description: occ.description || '', link: occ.link || '' }
  occurrenceEditing.value = false
}

function closeOccurrence() {
  activeOccurrence.value = null
  occurrenceEditing.value = false
}

function startEditOccurrence() {
  occurrenceEditing.value = true
}

function openAddOccurrenceForm() {
  const suggested = meetingOccurrenceService.computeNextSuggestedDate(meeting.value)
  const d = suggested ? new Date(suggested) : new Date()
  newOccurrenceDraft.value = {
    date: d.toISOString().slice(0, 10),
    time: d.toTimeString().slice(0, 5),
    description: '',
    link: '',
  }
  addingOccurrence.value = true
}

function closeAddOccurrenceForm() {
  addingOccurrence.value = false
}

async function submitAddOccurrence() {
  if (!newOccurrenceDraft.value.date) return
  const isoDate = new Date(`${newOccurrenceDraft.value.date}T${newOccurrenceDraft.value.time || '00:00'}`).toISOString()
  await meetingsStore.addOccurrence(props.id, {
    date: isoDate,
    description: newOccurrenceDraft.value.description,
    link: newOccurrenceDraft.value.link.trim(),
  })
  addingOccurrence.value = false
}

function requestRemoveOccurrence(occ) {
  occurrencePendingRemoval.value = occ
}

function cancelRemoveOccurrence() {
  occurrencePendingRemoval.value = null
}

async function confirmRemoveOccurrence() {
  const occ = occurrencePendingRemoval.value
  if (!occ) return
  await meetingsStore.removeOccurrence(props.id, occ.id, { tasksStore })
  if (activeOccurrence.value?.id === occ.id) closeOccurrence()
  expandedOccurrenceIds.value = expandedOccurrenceIds.value.filter((id) => id !== occ.id)
  occurrencePendingRemoval.value = null
}

async function saveOccurrence() {
  await meetingsStore.updateOccurrence(props.id, activeOccurrence.value.id, {
    description: occurrenceDraft.value.description,
    link: occurrenceDraft.value.link.trim(),
  })
  activeOccurrence.value = occurrences.value.find((o) => o.id === activeOccurrence.value.id) || null
  occurrenceEditing.value = false
}

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

function openSummaryParser(occurrence = null) {
  selectedSummaryOccurrenceId.value = occurrence?.id || 'all'
  summaryText.value = occurrence ? (occurrence.description || '') : (meeting.value?.description || '')
  parsedCandidates.value = []
  parseAttempted.value = false
  showSummaryParser.value = true
}

function runParse() {
  parsedCandidates.value = meetingSummaryParser.parse(stripHtml(summaryText.value), { knownUsers: usersStore.users })
  parseAttempted.value = true
}

function removeCandidate(idx) {
  parsedCandidates.value.splice(idx, 1)
}

async function confirmCreateTasks() {
  const toCreate = parsedCandidates.value.filter((c) => c.accepted && c.title.trim())
  for (const c of toCreate) {
    await tasksStore.createTask({
      meetingId: props.id,
      occurrenceId: selectedSummaryOccurrenceId.value !== 'all' ? selectedSummaryOccurrenceId.value : null,
      title: c.title.trim(),
      assigneeId: c.assigneeGuess || null,
    })
  }
  showSummaryParser.value = false
}

function startEdit() {
  if (!meeting.value) return
  const d = new Date(meeting.value.date)
  editDraft.value = {
    title: meeting.value.title,
    date: d.toISOString().slice(0, 10),
    time: d.toTimeString().slice(0, 5),
    description: meeting.value.description || '',
    link: meeting.value.link || '',
    attendeeIds: [...(meeting.value.attendeeIds || [])],
    editorIds: [...(meeting.value.editorIds || [])],
    color: meeting.value.color || '#4f7cff',
    recurrenceEnabled: !!meeting.value.recurrence?.freq,
    recurrenceFreq: meeting.value.recurrence?.freq || 'weekly',
    recurrenceWeekdays: [...(meeting.value.recurrence?.weekdays || [])],
  }
  editing.value = true
}

function withTimeOfDay(baseDate, timeStr) {
  const [h, m] = (timeStr || '00:00').split(':').map(Number)
  const d = new Date(baseDate)
  d.setHours(h || 0, m || 0, 0, 0)
  return d.toISOString()
}

function toggleWeekday(day) {
  const idx = editDraft.value.recurrenceWeekdays.indexOf(day)
  if (idx === -1) editDraft.value.recurrenceWeekdays.push(day)
  else editDraft.value.recurrenceWeekdays.splice(idx, 1)
}

async function saveEdit() {
  if (!editDraft.value.title.trim()) return
  if (!isRecurring.value && !editDraft.value.date) return
  // Для регулярной встречи дата серии (meeting.date) не редактируется — это дата
  // создания встречи, меняется только время суток по умолчанию для серии.
  const isoDate = isRecurring.value
    ? withTimeOfDay(meeting.value.date, editDraft.value.time || '00:00')
    : new Date(`${editDraft.value.date}T${editDraft.value.time || '00:00'}`).toISOString()
  const recurrence = editDraft.value.recurrenceEnabled
    ? {
        freq: editDraft.value.recurrenceFreq,
        weekdays: ['weekly', 'biweekly'].includes(editDraft.value.recurrenceFreq)
          ? [...editDraft.value.recurrenceWeekdays].sort((a, b) => a - b)
          : [],
      }
    : null
  await meetingsStore.updateMeetingSeries(props.id, {
    title: editDraft.value.title.trim(),
    date: isoDate,
    description: editDraft.value.description,
    link: editDraft.value.link.trim(),
    attendeeIds: [...editDraft.value.attendeeIds],
    editorIds: [...editDraft.value.editorIds],
    color: editDraft.value.color,
    recurrence,
  })
  editing.value = false
}

function requestRemoveMeeting() {
  meetingPendingRemoval.value = true
}

function cancelRemoveMeeting() {
  meetingPendingRemoval.value = false
}

async function confirmRemoveMeeting() {
  for (const t of tasksStore.tasks.filter((x) => x.meetingId === props.id)) {
    await tasksStore.updateTaskField(t.id, 'meetingId', null)
  }
  await meetingsStore.removeMeeting(props.id)
  meetingPendingRemoval.value = false
  router.push('/meetings')
}

function toggleArchived() {
  if (!meeting.value) return
  if (meeting.value.archived) meetingsStore.unarchiveMeeting(meeting.value.id)
  else meetingsStore.archiveMeeting(meeting.value.id)
}
</script>

<template>
  <div v-if="!meeting" class="empty-state">Встреча не найдена или была удалена.</div>

  <template v-else>
    <div class="view-header">
      <div class="view-title">
        <button class="btn btn-ghost btn-sm back-btn" @click="router.push('/meetings')"><AppIcon name="chevronLeft" :size="13" /> Встречи</button>
      </div>
      <div v-if="canManageMeeting" class="header-actions">
        <button class="btn btn-ghost btn-icon btn-sm" title="Разбор резюме в задачи" @click="openSummaryParser()"><AppIcon name="layers" :size="14" /></button>
        <button class="btn btn-ghost btn-icon btn-sm" title="Редактировать встречу" @click="startEdit"><AppIcon name="edit" :size="14" /></button>
        <button
          class="btn btn-ghost btn-icon btn-sm" :title="meeting.archived ? 'Вернуть из архива' : 'Архивировать'"
          @click="toggleArchived"
        ><AppIcon :name="meeting.archived ? 'undo' : 'copy'" :size="14" /></button>
        <button class="btn btn-ghost btn-icon btn-sm btn-danger-ghost" title="Удалить встречу" @click="requestRemoveMeeting"><AppIcon name="trash" :size="14" /></button>
      </div>
    </div>

    <div class="meeting-header card">
      <h2 class="meeting-title">
        <span class="meeting-color-dot" :style="{ background: meeting.color || '#4f7cff' }" />
        <AppIcon :name="meetingTypeIcon" :size="17" /> {{ meeting.title }}
        <span v-if="meeting.archived" class="tag archived-tag">В архиве</span>
      </h2>
      <div class="meeting-meta meeting-meta-wrap">
        <span class="meta-item"><AppIcon name="alarm" :size="12" /> {{ isRecurring ? formatTime(meeting.date) : formatDateTime(meeting.date) }}</span>
        <span class="meeting-recurrence meta-item"><AppIcon :name="meetingTypeIcon" :size="12" /> {{ recurrenceLabel }}</span>
        <a v-if="meeting.link" :href="meeting.link" target="_blank" rel="noopener" class="meta-item meeting-link"><AppIcon name="link" :size="12" /> Присоединиться к звонку</a>
        <span v-if="author">· Автор: {{ author.name }}</span>
      </div>
      <div v-if="meeting.description" class="meeting-description rte-render" v-html="meeting.description" />
      <div v-if="attendees.length" class="meeting-attendees">
        <span class="attendees-label">Участники:</span>
        <span v-for="u in attendees" :key="u.id" class="tag attendee-tag">{{ u.name }}</span>
      </div>
    </div>

    <template v-if="isRecurring">
      <div v-if="unfinishedTotalCount" class="series-alert-bubble">НЕ ВЫПОЛНЕНО В СЕРИИ ВСТРЕЧ ({{ unfinishedTotalCount }})</div>
      <div v-else class="series-alert-subtitle">По серии нет невыполненных задач</div>

      <div v-if="unfinishedGroupsByOccurrence.length || standaloneUnfinishedTasks.length" class="series-occ-list">
        <div v-for="group in unfinishedGroupsByOccurrence" :key="group.occurrence.id" class="series-occ-row card">
          <div class="series-occ-marker">
            <span class="series-occ-date">{{ formatDateTime(group.occurrence.date) }}</span>
            <span class="series-occ-count">({{ group.count }})</span>
          </div>
          <div class="series-occ-tasks">
            <TaskListPanel :tasks="group.tasks" :show-toolbar="false" :meeting-mode="true" :flat="true" />
          </div>
        </div>
        <div v-if="standaloneUnfinishedTasks.length" class="series-occ-row card">
          <div class="series-occ-marker">
            <span class="series-occ-date">Без встречи</span>
            <span class="series-occ-count">({{ standaloneUnfinishedTasks.length }})</span>
          </div>
          <div class="series-occ-tasks">
            <TaskListPanel :tasks="standaloneUnfinishedTasks" :show-toolbar="false" :meeting-mode="true" :flat="true" />
          </div>
        </div>
      </div>

      <div class="occurrences-header-row">
        <h3 class="tasks-title occurrences-title">Подвстречи серии (все подвстречи и все их задачи)</h3>
        <button v-if="canManageMeeting" class="btn btn-primary btn-sm" @click="openAddOccurrenceForm">
          <AppIcon name="plus" :size="13" /> Добавить подвстречу серии
        </button>
      </div>
      <QuickFiltersBar :task-count="recurringVisibleTasks.length" :meeting-mode="false" />

      <div v-if="seriesTasksWithoutOccurrence.length" class="occurrence-card card standalone-series-card">
        <div class="occurrence-header-wrap occurrence-header-wrap--static">
          <div class="occurrence-header occurrence-header--static">
            <span class="occurrence-date"><AppIcon name="layers" :size="13" /> Общие задачи серии (без привязки к подвстрече)</span>
            <span class="occurrence-has-desc">{{ seriesTasksWithoutOccurrence.length }} задач</span>
          </div>
        </div>
        <TaskListPanel :tasks="seriesTasksWithoutOccurrence" :show-toolbar="false" :meeting-mode="true" />
        <QuickAddTaskRow
          :meeting-id="props.id"
          placeholder="Добавить общую задачу серии..."
        />
      </div>

      <div v-if="!occurrenceGroups.length && !seriesTasksWithoutOccurrence.length" class="empty-state-inline">
        Подвстреч пока нет — добавьте первую кнопкой «Добавить подвстречу серии».
      </div>
      <div class="occurrence-list">
        <div v-for="group in occurrenceGroups" :key="group.occurrence.id" class="occurrence-card card">
          <div class="occurrence-header-wrap">
            <button class="occurrence-header" @click="openOccurrence(group.occurrence)">
              <span class="occurrence-date"><AppIcon name="calendar" :size="13" /> {{ occurrenceTitle(group.occurrence) }}</span>
              <span v-if="group.occurrence.description" class="occurrence-has-desc"><AppIcon name="edit" :size="11" /> описание заполнено</span>
              <span class="occurrence-open-hint">{{ group.occurrence.description ? 'Открыть подробно' : 'Заполнить описание' }} →</span>
            </button>
            <button
              v-if="group.occurrence.description"
              class="btn btn-ghost btn-sm occurrence-inline-toggle"
              @click="toggleOccurrenceExpanded(group.occurrence.id)"
            >
              <AppIcon :name="isOccurrenceExpanded(group.occurrence.id) ? 'chevronUp' : 'chevronDown'" :size="13" />
              {{ isOccurrenceExpanded(group.occurrence.id) ? 'Свернуть описание' : 'Развернуть описание' }}
            </button>
            <button v-if="canManageMeeting" class="btn btn-ghost btn-sm" @click="openSummaryParser(group.occurrence)">
              <AppIcon name="layers" :size="13" /> Разбор резюме встречи в задачи
            </button>
            <button v-if="canManageMeeting" class="btn btn-ghost btn-icon btn-sm btn-danger-ghost" title="Удалить подвстречу" @click="requestRemoveOccurrence(group.occurrence)">
              <AppIcon name="trash" :size="13" />
            </button>
          </div>

          <Transition name="fade-tab">
            <div v-if="isOccurrenceExpanded(group.occurrence.id) && group.occurrence.description" class="occurrence-inline-description rte-render">
              <div v-html="group.occurrence.description" />
              <a v-if="group.occurrence.link" :href="group.occurrence.link" target="_blank" rel="noopener" class="meta-item meeting-link occurrence-inline-link"><AppIcon name="link" :size="12" /> Дополнительные материалы</a>
            </div>
          </Transition>

          <div v-if="!group.tasks.length" class="empty-state-inline">Задач на встрече нет</div>
          <TaskListPanel v-else :tasks="group.tasks" :show-toolbar="false" :meeting-mode="true" />

          <QuickAddTaskRow
            :meeting-id="props.id"
            :occurrence-id="group.occurrence.id"
            placeholder="Добавить задачу для этой подвстречи..."
          />
        </div>
      </div>
    </template>

    <template v-else>
      <h3 class="tasks-title">Задачи встречи</h3>
      <QuickFiltersBar :task-count="meetingTasks.length" :meeting-mode="true" />
      <QuickAddTaskRow
        :meeting-id="props.id"
        placeholder="Добавить задачу по итогам встречи..."
      />
      <TaskListPanel :tasks="meetingTasks" :meeting-mode="true" empty-text="К этой встрече пока не привязано ни одной задачи" />
    </template>

    <div v-if="addingOccurrence" class="modal-overlay">
      <div class="modal card scroll-thin">
        <div class="modal-header">
          <h3>Добавить подвстречу серии</h3>
          <button class="btn btn-ghost btn-sm" @click="closeAddOccurrenceForm"><AppIcon name="close" :size="13" /></button>
        </div>
        <div class="modal-body">
          <p class="hint-text">
            Дата/время предзаполнены ближайшим слотом по регламенту серии — при
            необходимости поправьте перед сохранением.
          </p>
          <div class="field-row">
            <div class="field-group">
              <label>Дата</label>
              <input v-model="newOccurrenceDraft.date" type="date" />
            </div>
            <div class="field-group">
              <label>Время</label>
              <input v-model="newOccurrenceDraft.time" type="time" step="300" />
            </div>
          </div>
          <div class="field-group">
            <label>Ссылка на материалы (опционально)</label>
            <input v-model="newOccurrenceDraft.link" placeholder="https://..." />
          </div>
          <div class="field-group">
            <label>Описание (опционально)</label>
            <RichTextEditor v-model="newOccurrenceDraft.description" placeholder="Что обсуждалось / повестка..." />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="closeAddOccurrenceForm">Отмена</button>
          <button class="btn btn-primary" @click="submitAddOccurrence">Добавить</button>
        </div>
      </div>
    </div>

    <div v-if="activeOccurrence" class="modal-overlay">
      <div class="modal modal-occurrence card scroll-thin">
        <div class="modal-header">
          <h3>{{ occurrenceTitle(activeOccurrence) }}</h3>
          <button class="btn btn-ghost btn-sm" @click="closeOccurrence"><AppIcon name="close" :size="13" /></button>
        </div>
        <div class="modal-body">
          <template v-if="occurrenceEditing">
            <div class="field-group">
              <label>Что обсуждалось</label>
              <RichTextEditor v-model="occurrenceDraft.description" placeholder="Заметки по этой встрече из серии..." />
            </div>
            <div class="field-group">
              <label>Ссылка на доп. материалы</label>
              <input v-model="occurrenceDraft.link" placeholder="https://..." />
            </div>
          </template>
          <template v-else>
            <div v-if="activeOccurrence.description" class="occurrence-description-text rte-render" v-html="activeOccurrence.description" />
            <p v-else class="empty-state-inline">Описание пока не заполнено</p>
            <a v-if="activeOccurrence.link" :href="activeOccurrence.link" target="_blank" rel="noopener" class="meta-item meeting-link"><AppIcon name="link" :size="12" /> Дополнительные материалы</a>
          </template>
        </div>
        <div class="modal-actions">
          <template v-if="occurrenceEditing">
            <button class="btn btn-ghost" @click="occurrenceEditing = false">Отмена</button>
            <button class="btn btn-primary" @click="saveOccurrence">Сохранить</button>
          </template>
          <template v-else>
            <button class="btn btn-ghost" @click="closeOccurrence">Закрыть</button>
            <button v-if="canManageMeeting" class="btn btn-primary" @click="startEditOccurrence">{{ activeOccurrence.description ? 'Изменить' : 'Заполнить' }}</button>
          </template>
        </div>
      </div>
    </div>

    <div v-if="showSummaryParser" class="modal-overlay">
      <div class="modal modal-wide card scroll-thin">
        <div class="modal-header">
          <h3>Разбор резюме встречи в задачи</h3>
          <button class="btn btn-ghost btn-sm" @click="showSummaryParser = false"><AppIcon name="close" :size="13" /></button>
        </div>
        <div class="modal-body">
          <p class="hint-text">
            Вставьте текстовое резюме встречи. Кандидатами в задачи считаются строки,
            начинающиеся с "-", "•", номера пункта, либо в формате "Имя: сделать...".
            Ничего не создаётся без вашего подтверждения.
          </p>
          <div v-if="isRecurring" class="field-group">
            <label>Подвстреча для создаваемых задач</label>
            <select v-model="selectedSummaryOccurrenceId">
              <option value="all">Без привязки к подвстрече (общие задачи серии)</option>
              <option v-for="opt in summaryOccurrenceOptions" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
            </select>
          </div>
          <div class="field-group">
            <label>Текст резюме</label>
            <RichTextEditor v-model="summaryText" placeholder="Вставьте резюме встречи сюда..." />
          </div>
          <button class="btn btn-primary btn-sm" @click="runParse">Разобрать на задачи</button>

          <div v-if="parseAttempted" class="parse-results">
            <div v-if="!parsedCandidates.length" class="empty-state-inline">
              Не найдено ни одной строки, соответствующей эвристикам разбора.
            </div>
            <template v-else>
              <div class="section-title">Найдено кандидатов: {{ parsedCandidates.length }} — подтвердите перед сохранением</div>
              <div v-for="(c, idx) in parsedCandidates" :key="idx" class="candidate-row">
                <input type="checkbox" v-model="c.accepted" />
                <div class="candidate-main">
                  <input v-model="c.title" class="candidate-title-input" />
                  <div class="candidate-meta">
                    <span class="tag">{{ MATCHED_PATTERN_LABEL[c.matchedPattern] }}</span>
                    <span v-if="c.assigneeNameRaw" class="tag">
                      Имя в тексте: "{{ c.assigneeNameRaw }}"
                      <template v-if="c.assigneeGuess">→ сопоставлено: {{ usersStore.byId(c.assigneeGuess)?.name }}</template>
                      <template v-else>→ исполнитель не найден</template>
                    </span>
                  </div>
                </div>
                <button class="btn btn-ghost btn-sm" @click="removeCandidate(idx)"><AppIcon name="close" :size="11" /></button>
              </div>
            </template>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showSummaryParser = false">Отмена</button>
          <button
            class="btn btn-primary"
            :disabled="!parsedCandidates.some((c) => c.accepted && c.title.trim())"
            @click="confirmCreateTasks"
          >Создать задачи ({{ parsedCandidates.filter((c) => c.accepted && c.title.trim()).length }})</button>
        </div>
      </div>
    </div>

    <div v-if="editing" class="modal-overlay">
      <div class="modal card scroll-thin">
        <div class="modal-header">
          <h3>Редактировать встречу</h3>
          <button class="btn btn-ghost btn-sm" @click="editing = false"><AppIcon name="close" :size="13" /></button>
        </div>
        <div class="modal-body">
          <div class="field-group">
            <label>Название</label>
            <input v-model="editDraft.title" />
          </div>
          <div class="field-row">
            <div v-if="!isRecurring" class="field-group">
              <label>Дата</label>
              <input v-model="editDraft.date" type="date" />
            </div>
            <div class="field-group">
              <label>{{ isRecurring ? 'Время серии' : 'Время' }}</label>
              <input v-model="editDraft.time" type="time" step="300" />
            </div>
            <div class="field-group color-field">
              <label>Цвет</label>
              <input v-model="editDraft.color" type="color" />
            </div>
          </div>
          <p v-if="isRecurring" class="hint-text">Дата серии — дата создания встречи, её нельзя изменить. Дату каждой подвстречи задаёте отдельно.</p>
          <div class="field-group">
            <label>Ссылка на звонок</label>
            <input v-model="editDraft.link" placeholder="https://meet.example.com/..." />
          </div>
          <div class="field-group recurrence-section">
            <label>тип встречи</label>
            <div class="segmented-row">
              <button class="segmented-btn" :class="{ active: !editDraft.recurrenceEnabled }" @click="editDraft.recurrenceEnabled = false">Разовая</button>
              <button class="segmented-btn" :class="{ active: editDraft.recurrenceEnabled }" @click="editDraft.recurrenceEnabled = true">Регулярная</button>
            </div>
          </div>
          <div v-if="editDraft.recurrenceEnabled" class="field-group recurrence-box">
            <label>Периодичность</label>
            <div class="segmented-row recurrence-type-row">
              <button class="segmented-btn" :class="{ active: editDraft.recurrenceFreq === 'daily' }" @click="editDraft.recurrenceFreq = 'daily'">Каждый день</button>
              <button class="segmented-btn" :class="{ active: editDraft.recurrenceFreq === 'weekly' }" @click="editDraft.recurrenceFreq = 'weekly'">Раз в неделю</button>
              <button class="segmented-btn" :class="{ active: editDraft.recurrenceFreq === 'biweekly' }" @click="editDraft.recurrenceFreq = 'biweekly'">раз в 2 недели</button>
            </div>
            <div v-if="editDraft.recurrenceFreq !== 'daily'" class="weekday-picker">
              <button
                v-for="day in WEEKDAY_OPTIONS" :key="day.value"
                class="weekday-btn" :class="{ active: editDraft.recurrenceWeekdays.includes(day.value) }"
                @click="toggleWeekday(day.value)"
              >{{ day.label }}</button>
            </div>
            <p class="hint-text">Первая подвстреча серии — дата и время, указанные выше. Следующие подвстречи появятся автоматически за день до начала.</p>
          </div>
          <div class="field-group">
            <label>Описание</label>
            <RichTextEditor v-model="editDraft.description" placeholder="Тема, контекст..." />
          </div>
          <div class="field-group">
            <label>Участники (опционально — если не выбрано никого, ассайн задач встречи доступен на всех)</label>
            <UserMultiSelect
              v-model="editDraft.attendeeIds"
              :users="usersStore.users"
              placeholder="Добавить участника"
              empty-hint="Никого не выбрано — доступно всем"
              chip-class="attendee-chip"
            />
          </div>

          <div class="field-group">
            <label>Редакторы</label>
            <UserMultiSelect
              v-model="editDraft.editorIds"
              :users="usersStore.users"
              placeholder="Добавить редактора"
              empty-hint="Редакторы не назначены"
              chip-class="editor-chip"
              avatar-class="mini-avatar-editor"
            />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="editing = false">Отмена</button>
          <button class="btn btn-primary" :disabled="!editDraft.title.trim() || !editDraft.date" @click="saveEdit">Сохранить</button>
        </div>
      </div>
    </div>

    <ConfirmModal
      v-if="occurrencePendingRemoval"
      title="Удалить подвстречу?"
      message="Задачи, привязанные к ней, останутся, но потеряют привязку к подвстрече."
      confirm-text="Удалить"
      @confirm="confirmRemoveOccurrence"
      @cancel="cancelRemoveOccurrence"
    />

    <ConfirmModal
      v-if="meetingPendingRemoval"
      title="Удалить встречу?"
      message="Задачи останутся, но потеряют привязку к встрече."
      confirm-text="Удалить"
      @confirm="confirmRemoveMeeting"
      @cancel="cancelRemoveMeeting"
    />
  </template>
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.back-btn { padding-left: 4px; display: inline-flex; align-items: center; gap: 4px; }
.header-actions { display: flex; gap: 8px; align-items: center; }

.meeting-header { padding: 16px 18px; margin-bottom: 18px; }
.meeting-title { margin: 0 0 6px; font-size: 18px; display: flex; align-items: center; gap: 8px; }
.meeting-color-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.archived-tag { background: #eef1f7; color: var(--color-text-muted); font-weight: 500; }
.meeting-meta { display: flex; gap: 10px; font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 8px; }
.meeting-meta-wrap { flex-wrap: wrap; }
.meta-item { display: inline-flex; align-items: center; gap: 5px; }
.meeting-recurrence { color: var(--color-text); font-weight: 500; }
.meeting-link { color: var(--color-primary); font-weight: 600; text-decoration: none; }
.meeting-link:hover { text-decoration: underline; }
.meeting-description { margin: 0 0 8px; font-size: 13px; color: var(--color-text); line-height: 1.5; }
.rte-render :deep(ul), .rte-render :deep(ol) { padding-left: 20px; margin: 4px 0; }
.meeting-attendees { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.attendees-label { font-size: 11.5px; color: var(--color-text-muted); }
.attendee-tag { background: #f4f0ff; color: #7c5cd6; }
.btn-danger-ghost { color: var(--color-danger); }
.btn-danger-ghost:hover { background: #fdeceb; }

.tasks-title { font-size: 13px; font-weight: 600; margin: 0 0 8px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.03em; }
.occurrences-header-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 20px; }
.occurrences-header-row .occurrences-title { margin-top: 0; }
.occurrences-title { margin-top: 20px; }
.empty-state { color: var(--color-text-muted); font-size: 13px; text-align: center; padding: 40px 0; }
.empty-state-inline { font-size: 12.5px; color: var(--color-text-muted); padding: 10px; text-align: center; }

/* По скриншоту верхний заголовок должен выглядеть так же, как bubble "НЕ ВЫПОЛНЕНО",
   только с полным названием серии встреч. Отдельная строка "Открытых задач: x" убрана —
   она дублировала число, которое уже есть в заголовке. */
.series-alert-bubble {
  display: inline-flex; align-items: center; gap: 6px; margin-bottom: 12px;
  color: var(--color-danger); font-size: 13.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
}
.series-alert-subtitle { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 12px; }
.series-occ-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 4px; }
.series-occ-row { display: grid; grid-template-columns: 118px minmax(0, 1fr); gap: 10px; align-items: start; padding: 12px 14px; }
.series-occ-marker { display: flex; flex-direction: column; align-items: center; gap: 3px; padding-top: 6px; text-align: center; }
/* Дата подсерии — жирная и синяя. Счётчик рядом теперь оформлен так же ярко,
   как в bubble "НЕ ВЫПОЛНЕНО": жирный, красный, крупнее прежнего. */
.series-occ-date { font-size: 13px; font-weight: 700; color: #2f6fed; line-height: 1.3; }
.series-occ-count { font-size: 15px; font-weight: 700; color: var(--color-danger); }
.series-occ-tasks { min-width: 0; }

.occurrence-list { display: flex; flex-direction: column; gap: 12px; }
.occurrence-card { padding: 12px 14px; }
.standalone-series-card { margin-bottom: 12px; }
.occurrence-header-wrap { display: flex; align-items: center; gap: 10px; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; }
.occurrence-header-wrap--static { margin-bottom: 10px; }
.occurrence-header {
  display: flex; align-items: center; gap: 10px; flex: 1; border: none; background: none; cursor: pointer;
  padding: 4px 2px 2px; text-align: left;
}
.occurrence-header--static { cursor: default; padding: 0; }
.occurrence-date { font-size: 13.5px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.occurrence-has-desc { font-size: 11.5px; color: var(--color-text-muted); display: inline-flex; align-items: center; gap: 4px; }
.occurrence-open-hint { margin-left: auto; font-size: 12px; color: var(--color-primary); font-weight: 600; }
.occurrence-inline-toggle { display: inline-flex; align-items: center; gap: 6px; }
.occurrence-inline-description {
  margin: 0 0 12px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: #fafbfe;
  font-size: 13px;
  line-height: 1.55;
}
.occurrence-inline-link { margin-top: 10px; }
.occurrence-description-text { font-size: 13px; line-height: 1.55; margin: 0 0 10px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { width: 620px; max-height: 85vh; padding: 0; display: flex; flex-direction: column; }

.modal-occurrence { width: 860px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 10px; }
.modal-header h3 { margin: 0; font-size: 15px; }
.modal-body { padding: 4px 18px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.field-group { display: flex; flex-direction: column; gap: 4px; }
.field-group label { font-size: 11.5px; color: var(--color-text-muted); }
.field-group input, .field-group textarea, .field-group select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 8px; }
.field-row { display: flex; gap: 12px; }
.field-row .field-group { flex: 1; }
.color-field { flex: 0 0 auto; }
.color-field input[type=color] { padding: 2px; width: 40px; height: 32px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--color-border); }

.segmented-row { display: flex; gap: 6px; flex-wrap: wrap; }
.segmented-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); padding: 6px 10px;
  border-radius: 8px; cursor: pointer; font-size: 12.5px; color: var(--color-text-muted);
}
.segmented-btn.active { background: #eef2ff; border-color: #cfd8ff; color: var(--color-primary-dark); font-weight: 600; }
.recurrence-box { border: 1px solid var(--color-border); border-radius: 10px; padding: 10px; background: #fafbfe; }
.recurrence-type-row { margin-bottom: 6px; }
.weekday-picker { display: flex; gap: 6px; flex-wrap: wrap; }
.weekday-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 20px;
  padding: 5px 10px; cursor: pointer; font-size: 12px; color: var(--color-text-muted);
}
.weekday-btn.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }

.modal-wide { width: 560px; }
.hint-text { font-size: 12px; color: var(--color-text-muted); line-height: 1.5; margin: 0 0 4px; }
.parse-results { margin-top: 8px; display: flex; flex-direction: column; gap: 8px; }
.section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted); border-top: 1px solid var(--color-border); padding-top: 10px; }
.candidate-row { display: flex; align-items: flex-start; gap: 8px; padding: 6px 4px; border-bottom: 1px solid var(--color-border); }
.candidate-main { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.candidate-title-input { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 13px; width: 100%; }
.candidate-meta { display: flex; gap: 6px; flex-wrap: wrap; font-size: 11px; }
.fade-tab-enter-active, .fade-tab-leave-active { transition: opacity 0.12s ease; }
.fade-tab-enter-from, .fade-tab-leave-to { opacity: 0; }
</style>
