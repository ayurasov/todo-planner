<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingsStore } from '../stores/meetingsStore'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import { useDragReorder } from '../composables/useDragReorder'
import { formatDateTime, formatTime, formatMeetingRecurrence } from '../utils/formatters'
import AppIcon from '../components/common/AppIcon.vue'
import RichTextEditor from '../components/common/RichTextEditor.vue'
import ConfirmModal from '../components/common/ConfirmModal.vue'

const router = useRouter()
const meetingsStore = useMeetingsStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()

const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const showCreateForm = ref(false)
const showArchived = ref(false)
const draft = ref({
  title: '', date: '', time: '', description: '', link: '', attendeeIds: [], editorIds: [], color: '#4f7cff',
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})

const editingMeetingId = ref(null)
const editDraft = ref({
  title: '', date: '', time: '', description: '', link: '', attendeeIds: [], editorIds: [], color: '#4f7cff',
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})

const meetingPendingRemoval = ref(null)

// --- tag-пикер состояние для черновика создания ---
const draftAttendeePickerOpen = ref(false)
const draftEditorPickerOpen = ref(false)

// --- tag-пикер состояние для черновика редактирования ---
const editAttendeePickerOpen = ref(false)
const editEditorPickerOpen = ref(false)

function withTimeOfDay(date, timeStr) {
  const [h, m] = (timeStr || '00:00').split(':').map(Number)
  const d = new Date(date)
  d.setHours(h || 0, m || 0, 0, 0)
  return d
}

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
  if (!usersStore.loaded) await usersStore.load()
})

const taskCountByMeeting = computed(() => {
  const map = {}
  for (const t of tasksStore.tasks) {
    if (t.meetingId) map[t.meetingId] = (map[t.meetingId] || 0) + 1
  }
  return map
})

const baseMeetings = computed(() => (showArchived.value ? meetingsStore.archivedMeetings : meetingsStore.activeMeetings))

const filteredMeetings = computed(() => {
  let list = baseMeetings.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter((m) => m.title.toLowerCase().includes(q))
  }
  if (dateFrom.value) {
    list = list.filter((m) => new Date(m.date) >= new Date(dateFrom.value))
  }
  if (dateTo.value) {
    const end = new Date(dateTo.value)
    end.setHours(23, 59, 59, 999)
    list = list.filter((m) => new Date(m.date) <= end)
  }
  return list
})

const { draggingId, displayItems: displayMeetings, startDrag, dragOver, dragOverEnd, endDrag, cancelDrag } = useDragReorder(
  filteredMeetings,
  (orderedIds) => meetingsStore.reorderMeetings(orderedIds),
)

function resetFilters() {
  searchQuery.value = ''
  dateFrom.value = ''
  dateTo.value = ''
}

function openCreateForm() {
  const now = new Date()
  draft.value = {
    title: '',
    date: now.toISOString().slice(0, 10),
    time: now.toTimeString().slice(0, 5),
    description: '',
    link: '',
    attendeeIds: [],
    editorIds: [],
    color: '#4f7cff',
    recurrenceEnabled: false,
    recurrenceFreq: 'weekly',
    recurrenceWeekdays: [],
  }
  draftAttendeePickerOpen.value = false
  draftEditorPickerOpen.value = false
  showCreateForm.value = true
}

function toggleDraftWeekday(day) {
  const idx = draft.value.recurrenceWeekdays.indexOf(day)
  if (idx === -1) draft.value.recurrenceWeekdays.push(day)
  else draft.value.recurrenceWeekdays.splice(idx, 1)
}

// --- helpers для tag-пикеров ---
function availableAttendeesForDraft() {
  const ids = new Set(draft.value.attendeeIds)
  return usersStore.users.filter((u) => !ids.has(u.id))
}
function availableEditorsForDraft() {
  const ids = new Set(draft.value.editorIds)
  return usersStore.users.filter((u) => !ids.has(u.id))
}
function availableAttendeesForEdit() {
  const ids = new Set(editDraft.value.attendeeIds)
  return usersStore.users.filter((u) => !ids.has(u.id))
}
function availableEditorsForEdit() {
  const ids = new Set(editDraft.value.editorIds)
  return usersStore.users.filter((u) => !ids.has(u.id))
}

function addDraftAttendee(userId) {
  if (!draft.value.attendeeIds.includes(userId)) draft.value.attendeeIds.push(userId)
  draftAttendeePickerOpen.value = false
}
function removeDraftAttendee(userId) {
  draft.value.attendeeIds = draft.value.attendeeIds.filter((id) => id !== userId)
}
function addDraftEditor(userId) {
  if (!draft.value.editorIds.includes(userId)) draft.value.editorIds.push(userId)
  draftEditorPickerOpen.value = false
}
function removeDraftEditor(userId) {
  draft.value.editorIds = draft.value.editorIds.filter((id) => id !== userId)
}

function addEditAttendee(userId) {
  if (!editDraft.value.attendeeIds.includes(userId)) editDraft.value.attendeeIds.push(userId)
  editAttendeePickerOpen.value = false
}
function removeEditAttendee(userId) {
  editDraft.value.attendeeIds = editDraft.value.attendeeIds.filter((id) => id !== userId)
}
function addEditEditor(userId) {
  if (!editDraft.value.editorIds.includes(userId)) editDraft.value.editorIds.push(userId)
  editEditorPickerOpen.value = false
}
function removeEditEditor(userId) {
  editDraft.value.editorIds = editDraft.value.editorIds.filter((id) => id !== userId)
}

async function submitCreate() {
  if (!draft.value.title.trim()) return
  if (!draft.value.recurrenceEnabled && !draft.value.date) return
  const isoDate = draft.value.recurrenceEnabled
    ? withTimeOfDay(new Date(), draft.value.time || '00:00').toISOString()
    : new Date(`${draft.value.date}T${draft.value.time || '00:00'}`).toISOString()
  const recurrence = draft.value.recurrenceEnabled
    ? {
        freq: draft.value.recurrenceFreq,
        weekdays: ['weekly', 'biweekly'].includes(draft.value.recurrenceFreq)
          ? [...draft.value.recurrenceWeekdays].sort((a, b) => a - b)
          : [],
      }
    : null
  const meeting = await meetingsStore.createMeeting({
    title: draft.value.title.trim(),
    date: isoDate,
    description: draft.value.description,
    link: draft.value.link.trim(),
    attendeeIds: [...draft.value.attendeeIds],
    editorIds: [...draft.value.editorIds],
    color: draft.value.color,
    recurrence,
  })
  showCreateForm.value = false
  router.push(`/meetings/${meeting.id}`)
}

function openMeeting(id) {
  router.push(`/meetings/${id}`)
}

function startEdit(meeting) {
  const d = new Date(meeting.date)
  editDraft.value = {
    title: meeting.title,
    date: d.toISOString().slice(0, 10),
    time: d.toTimeString().slice(0, 5),
    description: meeting.description || '',
    link: meeting.link || '',
    attendeeIds: [...(meeting.attendeeIds || [])],
    editorIds: [...(meeting.editorIds || [])],
    color: meeting.color || '#4f7cff',
    recurrenceEnabled: !!meeting.recurrence?.freq,
    recurrenceFreq: meeting.recurrence?.freq || 'weekly',
    recurrenceWeekdays: [...(meeting.recurrence?.weekdays || [])],
  }
  editAttendeePickerOpen.value = false
  editEditorPickerOpen.value = false
  editingMeetingId.value = meeting.id
}

function closeEdit() {
  editingMeetingId.value = null
}

function toggleWeekday(day) {
  const idx = editDraft.value.recurrenceWeekdays.indexOf(day)
  if (idx === -1) editDraft.value.recurrenceWeekdays.push(day)
  else editDraft.value.recurrenceWeekdays.splice(idx, 1)
}

async function saveEdit() {
  if (!editDraft.value.title.trim() || !editDraft.value.date) return
  const isoDate = new Date(`${editDraft.value.date}T${editDraft.value.time || '00:00'}`).toISOString()
  const recurrence = editDraft.value.recurrenceEnabled
    ? {
        freq: editDraft.value.recurrenceFreq,
        weekdays: ['weekly', 'biweekly'].includes(editDraft.value.recurrenceFreq)
          ? [...editDraft.value.recurrenceWeekdays].sort((a, b) => a - b)
          : [],
      }
    : null
  await meetingsStore.updateMeetingSeries(editingMeetingId.value, {
    title: editDraft.value.title.trim(),
    date: isoDate,
    description: editDraft.value.description,
    link: editDraft.value.link.trim(),
    attendeeIds: [...editDraft.value.attendeeIds],
    editorIds: [...editDraft.value.editorIds],
    color: editDraft.value.color,
    recurrence,
  })
  editingMeetingId.value = null
}

function requestRemoveMeeting(meeting) {
  meetingPendingRemoval.value = meeting
}

function cancelRemoveMeeting() {
  meetingPendingRemoval.value = null
}

async function confirmRemoveMeeting() {
  const meeting = meetingPendingRemoval.value
  if (!meeting) return
  for (const t of tasksStore.tasks.filter((x) => x.meetingId === meeting.id)) {
    await tasksStore.updateTaskField(t.id, 'meetingId', null)
  }
  await meetingsStore.removeMeeting(meeting.id)
  meetingPendingRemoval.value = null
}

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

function isRecurringMeeting(meeting) {
  return !!meeting?.recurrence?.freq
}
</script>

<template>
  <div class="view-header">
    <div class="view-title">
      <span class="list-icon"><AppIcon name="calendar" :size="18" /></span>
      <h2>Встречи</h2>
    </div>
    <div class="header-actions">
      <button class="btn btn-ghost btn-icon" :class="{ active: showArchived }" :title="showArchived ? 'К активным' : 'Архив'" @click="showArchived = !showArchived">
        <AppIcon name="folder" :size="14" />
      </button>
      <button v-if="!showArchived" class="btn btn-sm btn-primary" @click="openCreateForm"><AppIcon name="plus" :size="13" /> Новая встреча</button>
    </div>
  </div>

  <div class="filters-bar card">
    <input v-model="searchQuery" class="search-input" placeholder="Поиск по названию встречи..." />
    <div class="date-range">
      <input v-model="dateFrom" type="date" title="С" />
      <span class="date-sep">—</span>
      <input v-model="dateTo" type="date" title="По" />
    </div>
    <button v-if="searchQuery || dateFrom || dateTo" class="btn btn-ghost btn-sm" @click="resetFilters">Сбросить</button>
  </div>

  <div v-if="!filteredMeetings.length" class="empty-state">
    {{ showArchived ? 'В архиве пока пусто.' : 'Встреч пока нет — создайте первую с помощью кнопки выше.' }}
  </div>

  <TransitionGroup tag="div" name="fade" class="meetings-list" @dragleave.self="dragOverEnd" @dragover.prevent @drop="endDrag">
    <div
      v-for="m in displayMeetings" :key="m.id" class="meeting-card card fade-move"
      :class="{ dragging: draggingId === m.id }"
      draggable="true"
      @dragstart="startDrag(m.id)"
      @dragenter.prevent="dragOver(m.id)"
      @dragover.prevent
      @dragend="cancelDrag"
      @drop.stop="endDrag"
      @click="openMeeting(m.id)"
    >
      <span class="drag-handle" title="Перетащить для сортировки" @click.stop><AppIcon name="menu" :size="14" /></span>
      <span class="meeting-color-dot" :style="{ background: m.color || '#4f7cff' }" />
      <AppIcon class="meeting-type-icon" :name="isRecurringMeeting(m) ? 'repeat' : 'calendar'" :size="14" :title="isRecurringMeeting(m) ? 'Регулярная встреча' : 'Разовая встреча'" />
      <div class="meeting-card-main">
        <div class="meeting-card-title-row">
          <h3 class="meeting-card-title">{{ m.title }}</h3>
          <span class="tag recurrence-badge" :class="{ 'recurrence-badge-recurring': isRecurringMeeting(m) }">
            <AppIcon v-if="isRecurringMeeting(m)" name="repeat" :size="11" /><span v-else><AppIcon name="calendar" :size="11" /></span> {{ formatMeetingRecurrence(m.recurrence) }}
          </span>
        </div>
        <p v-if="m.description" class="meeting-card-desc">{{ stripHtml(m.description) }}</p>
      </div>
      <div class="meeting-card-meta">
        <span class="meeting-card-date"><AppIcon name="alarm" :size="11" /> {{ isRecurringMeeting(m) ? formatTime(m.date) : formatDateTime(m.date) }}</span>
        <a v-if="m.link" :href="m.link" target="_blank" class="tag link-tag" @click.stop><AppIcon name="link" :size="11" /> Звонок</a>
        <span v-if="m.attendeeIds?.length" class="tag attendees-tag"><AppIcon name="users" :size="11" /> {{ m.attendeeIds.length }}</span>
        <span v-if="taskCountByMeeting[m.id]" class="tag task-count-tag"><AppIcon name="check" :size="11" /> {{ taskCountByMeeting[m.id] }} задач</span>
        <button class="btn btn-ghost btn-icon btn-sm" title="Редактировать встречу" @click.stop="startEdit(m)"><AppIcon name="edit" :size="12" /></button>
        <button
          class="btn btn-ghost btn-icon btn-sm" :title="m.archived ? 'Вернуть из архива' : 'Архивировать'"
          @click.stop="m.archived ? meetingsStore.unarchiveMeeting(m.id) : meetingsStore.archiveMeeting(m.id)"
        ><AppIcon :name="m.archived ? 'undo' : 'copy'" :size="12" /></button>
        <button class="btn btn-ghost btn-icon btn-sm btn-danger-ghost" title="Удалить встречу" @click.stop="requestRemoveMeeting(m)"><AppIcon name="trash" :size="12" /></button>
      </div>
    </div>
  </TransitionGroup>

  <!-- Создание встречи -->
  <div v-if="showCreateForm" class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Новая встреча</h3>
        <button class="btn btn-ghost btn-sm" @click="showCreateForm = false"><AppIcon name="close" :size="13" /></button>
      </div>
      <div class="modal-body">
        <div class="field-group">
          <label>Название</label>
          <input v-model="draft.title" placeholder="Например: Планёрка по проекту" @keyup.enter="submitCreate" />
        </div>
        <div class="field-row">
          <div v-if="!draft.recurrenceEnabled" class="field-group">
            <label>Дата</label>
            <input v-model="draft.date" type="date" />
          </div>
          <div class="field-group">
            <label>{{ draft.recurrenceEnabled ? 'Время (для всех подвстреч серии по умолчанию)' : 'Время' }}</label>
            <input v-model="draft.time" type="time" step="300" />
          </div>
          <div class="field-group color-field">
            <label>Цвет</label>
            <input v-model="draft.color" type="color" />
          </div>
        </div>
        <p v-if="draft.recurrenceEnabled" class="hint-text">
          Для регулярной встречи датой серии считается дата создания — отображается только время.
          Подвстречи вы добавите отдельно после создания, каждая со своей датой.
        </p>
        <div class="field-group">
          <label>Ссылка на звонок (опционально)</label>
          <input v-model="draft.link" placeholder="https://meet.example.com/..." />
        </div>
        <div class="field-group recurrence-section">
          <label>Тип встречи</label>
          <div class="segmented-row">
            <button class="segmented-btn" :class="{ active: !draft.recurrenceEnabled }" @click="draft.recurrenceEnabled = false">Разовая</button>
            <button class="segmented-btn" :class="{ active: draft.recurrenceEnabled }" @click="draft.recurrenceEnabled = true">Регулярная</button>
          </div>
        </div>
        <div v-if="draft.recurrenceEnabled" class="field-group recurrence-box">
          <label>Периодичность</label>
          <div class="segmented-row recurrence-type-row">
            <button class="segmented-btn" :class="{ active: draft.recurrenceFreq === 'daily' }" @click="draft.recurrenceFreq = 'daily'">Каждый день</button>
            <button class="segmented-btn" :class="{ active: draft.recurrenceFreq === 'weekly' }" @click="draft.recurrenceFreq = 'weekly'">раз в неделю</button>
            <button class="segmented-btn" :class="{ active: draft.recurrenceFreq === 'biweekly' }" @click="draft.recurrenceFreq = 'biweekly'">раз в 2 недели</button>
          </div>
          <div v-if="draft.recurrenceFreq !== 'daily'" class="weekday-picker">
            <button
              v-for="day in WEEKDAY_OPTIONS" :key="day.value"
              class="weekday-btn" :class="{ active: draft.recurrenceWeekdays.includes(day.value) }"
              @click="toggleDraftWeekday(day.value)"
            >{{ day.label }}</button>
          </div>
        </div>
        <div class="field-group">
          <label>Описание (опционально)</label>
          <RichTextEditor v-model="draft.description" placeholder="Тема, контекст..." />
        </div>

        <!-- Участники — tag-пикер -->
        <div class="field-group">
          <label>Участники (опционально — если не выбрано никого, ассайн задач встречи доступен на всех)</label>
          <div class="tag-picker-area">
            <span v-for="uid in draft.attendeeIds" :key="uid" class="member-chip attendee-chip">
              <span class="mini-avatar">{{ usersStore.byId(uid)?.name?.charAt(0) || '?' }}</span>
              {{ usersStore.byId(uid)?.name || uid }}
              <button class="chip-remove" @click="removeDraftAttendee(uid)"><AppIcon name="close" :size="10" /></button>
            </span>
            <button class="btn btn-ghost btn-sm add-member-btn" @click="draftAttendeePickerOpen = !draftAttendeePickerOpen">
              <AppIcon name="plus" :size="12" /> Участник
            </button>
          </div>
          <div v-if="draftAttendeePickerOpen" class="inline-picker">
            <button
              v-for="u in availableAttendeesForDraft()" :key="u.id"
              class="picker-option" @click="addDraftAttendee(u.id)"
            >{{ u.name }}</button>
            <span v-if="!availableAttendeesForDraft().length" class="picker-empty">Все пользователи добавлены</span>
          </div>
        </div>

        <!-- Редакторы — tag-пикер -->
        <div class="field-group">
          <label>Редакторы (могут управлять этой встречей)</label>
          <div class="tag-picker-area">
            <span v-for="uid in draft.editorIds" :key="uid" class="member-chip editor-chip">
              <span class="mini-avatar mini-avatar-editor">{{ usersStore.byId(uid)?.name?.charAt(0) || '?' }}</span>
              {{ usersStore.byId(uid)?.name || uid }}
              <button class="chip-remove" @click="removeDraftEditor(uid)"><AppIcon name="close" :size="10" /></button>
            </span>
            <button class="btn btn-ghost btn-sm add-member-btn" @click="draftEditorPickerOpen = !draftEditorPickerOpen">
              <AppIcon name="plus" :size="12" /> Редактор
            </button>
          </div>
          <div v-if="draftEditorPickerOpen" class="inline-picker">
            <button
              v-for="u in availableEditorsForDraft()" :key="u.id"
              class="picker-option" @click="addDraftEditor(u.id)"
            >{{ u.name }}</button>
            <span v-if="!availableEditorsForDraft().length" class="picker-empty">Все пользователи добавлены</span>
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showCreateForm = false">Отмена</button>
        <button class="btn btn-primary" :disabled="!draft.title.trim() || (!draft.recurrenceEnabled && !draft.date)" @click="submitCreate">Создать</button>
      </div>
    </div>
  </div>

  <!-- Редактирование встречи -->
  <div v-if="editingMeetingId" class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Редактировать встречу</h3>
        <button class="btn btn-ghost btn-sm" @click="closeEdit"><AppIcon name="close" :size="13" /></button>
      </div>
      <div class="modal-body">
        <div class="field-group">
          <label>Название</label>
          <input v-model="editDraft.title" />
        </div>
        <div class="field-row">
          <div class="field-group">
            <label>Дата</label>
            <input v-model="editDraft.date" type="date" />
          </div>
          <div class="field-group">
            <label>Время</label>
            <input v-model="editDraft.time" type="time" step="300" />
          </div>
          <div class="field-group color-field">
            <label>Цвет</label>
            <input v-model="editDraft.color" type="color" />
          </div>
        </div>
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
            <button class="segmented-btn" :class="{ active: editDraft.recurrenceFreq === 'weekly' }" @click="editDraft.recurrenceFreq = 'weekly'">раз в неделю</button>
            <button class="segmented-btn" :class="{ active: editDraft.recurrenceFreq === 'biweekly' }" @click="editDraft.recurrenceFreq = 'biweekly'">раз в 2 недели</button>
          </div>
          <div v-if="editDraft.recurrenceFreq !== 'daily'" class="weekday-picker">
            <button
              v-for="day in WEEKDAY_OPTIONS" :key="day.value"
              class="weekday-btn" :class="{ active: editDraft.recurrenceWeekdays.includes(day.value) }"
              @click="toggleWeekday(day.value)"
            >{{ day.label }}</button>
          </div>
        </div>
        <div class="field-group">
          <label>Описание</label>
          <RichTextEditor v-model="editDraft.description" placeholder="Тема, контекст..." />
        </div>

        <!-- Участники — tag-пикер -->
        <div class="field-group">
          <label>Участники (опционально — если не выбрано никого, ассайн задач встречи доступен на всех)</label>
          <div class="tag-picker-area">
            <span v-for="uid in editDraft.attendeeIds" :key="uid" class="member-chip attendee-chip">
              <span class="mini-avatar">{{ usersStore.byId(uid)?.name?.charAt(0) || '?' }}</span>
              {{ usersStore.byId(uid)?.name || uid }}
              <button class="chip-remove" @click="removeEditAttendee(uid)"><AppIcon name="close" :size="10" /></button>
            </span>
            <button class="btn btn-ghost btn-sm add-member-btn" @click="editAttendeePickerOpen = !editAttendeePickerOpen">
              <AppIcon name="plus" :size="12" /> Участник
            </button>
          </div>
          <div v-if="editAttendeePickerOpen" class="inline-picker">
            <button
              v-for="u in availableAttendeesForEdit()" :key="u.id"
              class="picker-option" @click="addEditAttendee(u.id)"
            >{{ u.name }}</button>
            <span v-if="!availableAttendeesForEdit().length" class="picker-empty">Все пользователи добавлены</span>
          </div>
        </div>

        <!-- Редакторы — tag-пикер -->
        <div class="field-group">
          <label>Редакторы (могут управлять этой встречей)</label>
          <div class="tag-picker-area">
            <span v-for="uid in editDraft.editorIds" :key="uid" class="member-chip editor-chip">
              <span class="mini-avatar mini-avatar-editor">{{ usersStore.byId(uid)?.name?.charAt(0) || '?' }}</span>
              {{ usersStore.byId(uid)?.name || uid }}
              <button class="chip-remove" @click="removeEditEditor(uid)"><AppIcon name="close" :size="10" /></button>
            </span>
            <button class="btn btn-ghost btn-sm add-member-btn" @click="editEditorPickerOpen = !editEditorPickerOpen">
              <AppIcon name="plus" :size="12" /> Редактор
            </button>
          </div>
          <div v-if="editEditorPickerOpen" class="inline-picker">
            <button
              v-for="u in availableEditorsForEdit()" :key="u.id"
              class="picker-option" @click="addEditEditor(u.id)"
            >{{ u.name }