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
  title: '', date: '', time: '', description: '', link: '', attendeeIds: [], color: '#4f7cff',
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})

const editingMeetingId = ref(null)
const editDraft = ref({
  title: '', date: '', time: '', description: '', link: '', attendeeIds: [], color: '#4f7cff',
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})

// Удаление встречи из списка — раньше через window.confirm(), теперь через
// единый ConfirmModal (см. TaskContextMenu.vue), meetingPendingRemoval хранит
// саму встречу, чтобы модалка могла показать её название и выполнить удаление.
const meetingPendingRemoval = ref(null)

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
    color: '#4f7cff',
    recurrenceEnabled: false,
    recurrenceFreq: 'weekly',
    recurrenceWeekdays: [],
  }
  showCreateForm.value = true
}

function toggleDraftWeekday(day) {
  const idx = draft.value.recurrenceWeekdays.indexOf(day)
  if (idx === -1) draft.value.recurrenceWeekdays.push(day)
  else draft.value.recurrenceWeekdays.splice(idx, 1)
}

function toggleDraftAttendee(userId) {
  const idx = draft.value.attendeeIds.indexOf(userId)
  if (idx === -1) draft.value.attendeeIds.push(userId)
  else draft.value.attendeeIds.splice(idx, 1)
}

async function submitCreate() {
  if (!draft.value.title.trim()) return
  if (!draft.value.recurrenceEnabled && !draft.value.date) return
  // Для регулярной встречи date серии = момент создания (см. правило "дата — это
  // дата создания, отображается только время"); время суток берётся из поля "Время".
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
    color: meeting.color || '#4f7cff',
    recurrenceEnabled: !!meeting.recurrence?.freq,
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
  await meetingsStore.updateMeetingSeries(editingMeetingId.value, {
    title: editDraft.value.title.trim(),
    date: isoDate,
    description: editDraft.value.description,
    link: editDraft.value.link.trim(),
    attendeeIds: [...editDraft.value.attendeeIds],
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

  <ConfirmModal
    v-if="meetingPendingRemoval"
    title="Удалить встречу?"
    :message="`«${meetingPendingRemoval.title}» будет удалена. Задачи останутся, но потеряют привязку к встрече.`"
    confirm-text="Удалить"
    @confirm="confirmRemoveMeeting"
    @cancel="cancelRemoveMeeting"
  />
</template>

<style scoped>
.hint-text { font-size: 12px; color: var(--color-text-muted); line-height: 1.5; margin: 0 0 4px; }
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.view-title { display: flex; align-items: center; gap: 8px; }
.view-title h2 { margin: 0; font-size: 19px; }
.list-icon { display: flex; color: var(--color-primary); }
.header-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.header-actions .active { background: #eef2ff; border-color: #cfd8ff; color: var(--color-primary-dark); }

.filters-bar { display: flex; align-items: center; gap: 10px; padding: 8px 10px; margin-bottom: 14px; }
.search-input { flex: 1; border: none; outline: none; font-size: 13px; background: transparent; }
.date-range { display: flex; align-items: center; gap: 6px; }
.date-range input { border: 1px solid var(--color-border); border-radius: 6px; padding: 4px 6px; font-size: 12.5px; }
.date-sep { color: var(--color-text-muted); font-size: 12px; }

.empty-state { color: var(--color-text-muted); font-size: 13px; text-align: center; padding: 40px 0; }

.meetings-list { display: flex; flex-direction: column; gap: 8px; min-height: 40px; }
.meeting-card {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 12px 14px; cursor: pointer; transition: box-shadow 0.12s ease, border-color 0.12s ease;
}
.meeting-card:hover { border-color: var(--color-primary); box-shadow: 0 2px 8px rgba(79,124,255,0.08); }
.meeting-card.dragging { opacity: 0.35; }
.drag-handle { color: var(--color-text-muted); cursor: grab; flex-shrink: 0; }
.meeting-color-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.meeting-type-icon { color: var(--color-text-muted); flex-shrink: 0; }
.meeting-card-main { min-width: 0; flex: 1; }
.meeting-card-title-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px; }
.meeting-card-title { margin: 0; font-size: 14px; font-weight: 600; }
.recurrence-badge { background: #eef1f7; color: var(--color-text-muted); font-weight: 500; display: inline-flex; align-items: center; gap: 4px; }
.recurrence-badge-recurring { background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; }
.meeting-card-desc {
  margin: 0; font-size: 12.5px; color: var(--color-text-muted);
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.meeting-card-meta { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.meeting-card-date { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; display: inline-flex; align-items: center; gap: 4px; }
.task-count-tag { background: #eef1f7; color: var(--color-text-muted); display: inline-flex; align-items: center; gap: 4px; }
.attendees-tag { background: #f4f0ff; color: #7c5cd6; display: inline-flex; align-items: center; gap: 4px; }
.link-tag { background: #eaf0ff; color: var(--color-primary-dark); text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }
.link-tag:hover { text-decoration: underline; }
.btn-danger-ghost { color: var(--color-danger); }
.btn-danger-ghost:hover { background: #fdeceb; }

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
.color-field { flex: 0 0 auto; }
.color-field input[type=color] { padding: 2px; width: 40px; height: 32px; }
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
