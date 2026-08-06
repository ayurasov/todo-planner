<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingsStore } from '../stores/meetingsStore'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import { formatDateTime, formatMeetingRecurrence } from '../utils/formatters'

const router = useRouter()
const meetingsStore = useMeetingsStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()

const searchQuery = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const showCreateForm = ref(false)
const draft = ref({ title: '', date: '', time: '', description: '', attendeeIds: [] })

const editingMeetingId = ref(null)
const editDraft = ref({
  title: '', date: '', time: '', description: '', attendeeIds: [],
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})

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

const filteredMeetings = computed(() => {
  let list = meetingsStore.sortedByDate
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
    attendeeIds: [],
  }
  showCreateForm.value = true
}

function toggleDraftAttendee(userId) {
  const idx = draft.value.attendeeIds.indexOf(userId)
  if (idx === -1) draft.value.attendeeIds.push(userId)
  else draft.value.attendeeIds.splice(idx, 1)
}

async function submitCreate() {
  if (!draft.value.title.trim() || !draft.value.date) return
  const isoDate = new Date(`${draft.value.date}T${draft.value.time || '00:00'}`).toISOString()
  const meeting = await meetingsStore.createMeeting({
    title: draft.value.title.trim(),
    date: isoDate,
    description: draft.value.description.trim(),
    attendeeIds: [...draft.value.attendeeIds],
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
    attendeeIds: [...(meeting.attendeeIds || [])],
    recurrenceEnabled: !!meeting.recurrence,
    recurrenceFreq: meeting.recurrence?.freq || 'weekly',
    recurrenceWeekdays: [...(meeting.recurrence?.weekdays || [])],
  }
  editingMeetingId.value = meeting.id
}

function closeEdit() {
  editingMeetingId.value = null
}

function toggleEditAttendee(userId) {
  const idx = editDraft.value.attendeeIds.indexOf(userId)
  if (idx === -1) editDraft.value.attendeeIds.push(userId)
  else editDraft.value.attendeeIds.splice(idx, 1)
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
  await meetingsStore.updateMeeting(editingMeetingId.value, {
    title: editDraft.value.title.trim(),
    date: isoDate,
    description: editDraft.value.description.trim(),
    attendeeIds: [...editDraft.value.attendeeIds],
    recurrence,
  })
  editingMeetingId.value = null
}
</script>

<template>
  <div class="view-header">
    <div class="view-title">
      <span class="list-icon">📅</span>
      <h2>Встречи</h2>
    </div>
    <button class="btn btn-sm btn-primary" @click="openCreateForm">+ Новая встреча</button>
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
    Встреч пока нет — создайте первую с помощью кнопки выше.
  </div>

  <div class="meetings-list">
    <div v-for="m in filteredMeetings" :key="m.id" class="meeting-card card" @click="openMeeting(m.id)">
      <div class="meeting-card-main">
        <div class="meeting-card-title-row">
          <h3 class="meeting-card-title">{{ m.title }}</h3>
          <span class="tag recurrence-badge" :class="{ 'recurrence-badge-recurring': m.recurrence }">
            {{ m.recurrence ? '🔁' : '·' }} {{ formatMeetingRecurrence(m.recurrence) }}
          </span>
        </div>
        <p v-if="m.description" class="meeting-card-desc">{{ m.description }}</p>
      </div>
      <div class="meeting-card-meta">
        <span class="meeting-card-date">🕐 {{ formatDateTime(m.date) }}</span>
        <span v-if="m.attendeeIds?.length" class="tag attendees-tag">👥 {{ m.attendeeIds.length }}</span>
        <span v-if="taskCountByMeeting[m.id]" class="tag task-count-tag">✓ {{ taskCountByMeeting[m.id] }} задач</span>
        <button class="btn btn-ghost btn-sm edit-meeting-btn" title="Редактировать встречу" @click.stop="startEdit(m)">✎</button>
      </div>
    </div>
  </div>

  <div v-if="showCreateForm" class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Новая встреча</h3>
        <button class="btn btn-ghost btn-sm" @click="showCreateForm = false">✕</button>
      </div>
      <div class="modal-body">
        <div class="field-group">
          <label>Название</label>
          <input v-model="draft.title" placeholder="Например: Планёрка по проекту" @keyup.enter="submitCreate" />
        </div>
        <div class="field-row">
          <div class="field-group">
            <label>Дата</label>
            <input v-model="draft.date" type="date" />
          </div>
          <div class="field-group">
            <label>Время</label>
            <input v-model="draft.time" type="time" />
          </div>
        </div>
        <div class="field-group">
          <label>Описание (опционально)</label>
          <textarea v-model="draft.description" rows="3" placeholder="Тема, ссылка на созвон, контекст..." />
        </div>
        <div class="field-group">
          <label>Участники (опционально — если не выбрано никого, ассайн задач встречи доступен на всех)</label>
          <div class="attendee-picker">
            <label v-for="u in usersStore.users" :key="u.id" class="attendee-option">
              <input type="checkbox" :checked="draft.attendeeIds.includes(u.id)" @change="toggleDraftAttendee(u.id)" />
              {{ u.name }}
            </label>
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showCreateForm = false">Отмена</button>
        <button class="btn btn-primary" :disabled="!draft.title.trim() || !draft.date" @click="submitCreate">Создать</button>
      </div>
    </div>
  </div>

  <div v-if="editingMeetingId" class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Редактировать встречу</h3>
        <button class="btn btn-ghost btn-sm" @click="closeEdit">✕</button>
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
            <input v-model="editDraft.time" type="time" />
          </div>
        </div>
        <div class="field-group recurrence-section">
          <label>Тип встречи</label>
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
            <button class="segmented-btn" :class="{ active: editDraft.recurrenceFreq === 'biweekly' }" @click="editDraft.recurrenceFreq = 'biweekly'">Раз в 2 недели</button>
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
          <textarea v-model="editDraft.description" rows="3" />
        </div>
        <div class="field-group">
          <label>Участники (опционально — если не выбрано никого, ассайн задач встречи доступен на всех)</label>
          <div class="attendee-picker">
            <label v-for="u in usersStore.users" :key="u.id" class="attendee-option">
              <input type="checkbox" :checked="editDraft.attendeeIds.includes(u.id)" @change="toggleEditAttendee(u.id)" />
              {{ u.name }}
            </label>
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="closeEdit">Отмена</button>
        <button class="btn btn-primary" :disabled="!editDraft.title.trim() || !editDraft.date" @click="saveEdit">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.view-title { display: flex; align-items: center; gap: 8px; }
.view-title h2 { margin: 0; font-size: 19px; }
.list-icon { font-size: 18px; }

.filters-bar { display: flex; align-items: center; gap: 10px; padding: 8px 10px; margin-bottom: 14px; }
.search-input { flex: 1; border: none; outline: none; font-size: 13px; background: transparent; }
.date-range { display: flex; align-items: center; gap: 6px; }
.date-range input { border: 1px solid var(--color-border); border-radius: 6px; padding: 4px 6px; font-size: 12.5px; }
.date-sep { color: var(--color-text-muted); font-size: 12px; }

.empty-state { color: var(--color-text-muted); font-size: 13px; text-align: center; padding: 40px 0; }

.meetings-list { display: flex; flex-direction: column; gap: 8px; }
.meeting-card {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 12px 14px; cursor: pointer; transition: box-shadow 0.12s ease, border-color 0.12s ease;
}
.meeting-card:hover { border-color: var(--color-primary); box-shadow: 0 2px 8px rgba(79,124,255,0.08); }
.meeting-card-main { min-width: 0; flex: 1; }
.meeting-card-title-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px; }
.meeting-card-title { margin: 0; font-size: 14px; font-weight: 600; }
.recurrence-badge { background: #eef1f7; color: var(--color-text-muted); font-weight: 500; }
.recurrence-badge-recurring { background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; }
.meeting-card-desc {
  margin: 0; font-size: 12.5px; color: var(--color-text-muted);
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.meeting-card-meta { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.meeting-card-date { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; }
.task-count-tag { background: #eef1f7; color: var(--color-text-muted); }
.attendees-tag { background: #f4f0ff; color: #7c5cd6; }
.edit-meeting-btn { padding: 3px 7px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { width: 440px; max-height: 85vh; padding: 0; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 10px; }
.modal-header h3 { margin: 0; font-size: 15px; }
.modal-body { padding: 4px 18px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.field-group { display: flex; flex-direction: column; gap: 4px; }
.field-group label { font-size: 11.5px; color: var(--color-text-muted); }
.field-group input, .field-group textarea { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 8px; }
.field-row { display: flex; gap: 12px; }
.field-row .field-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--color-border); }
.attendee-picker { display: flex; flex-direction: column; gap: 4px; max-height: 160px; overflow-y: auto; border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 8px; }
.attendee-option { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 3px 2px; cursor: pointer; }

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
</style>
