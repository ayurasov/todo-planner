<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingsStore } from '../stores/meetingsStore'
import { useTasksStore } from '../stores/tasksStore'
import { useUsersStore } from '../stores/usersStore'
import { useListsStore } from '../stores/listsStore'
import { useIsAdmin } from '../composables/usePermissions'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'
import AppIcon from '../components/common/AppIcon.vue'
import { formatDateTime, formatMeetingRecurrence } from '../utils/formatters'
import { meetingSummaryParser, MATCHED_PATTERN_LABEL } from '../services/MeetingSummaryParser'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const meetingsStore = useMeetingsStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const isAdmin = useIsAdmin()

const editing = ref(false)
const editDraft = ref({
  title: '', date: '', time: '', description: '', link: '', attendeeIds: [],
  recurrenceEnabled: false, recurrenceFreq: 'weekly', recurrenceWeekdays: [],
})

const showSummaryParser = ref(false)
const summaryText = ref('')
const parsedCandidates = ref([])
const parseAttempted = ref(false)

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
})

const meeting = computed(() => meetingsStore.meetingById(props.id))
const author = computed(() => (meeting.value ? usersStore.byId(meeting.value.createdBy) : null))
const meetingTasks = computed(() => tasksStore.tasks.filter((t) => t.meetingId === props.id && !t.parentTaskId))
const attendees = computed(() => (meeting.value?.attendeeIds || []).map((id) => usersStore.byId(id)).filter(Boolean))
const recurrenceLabel = computed(() => formatMeetingRecurrence(meeting.value?.recurrence))

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

function openSummaryParser() {
  summaryText.value = meeting.value?.description || ''
  parsedCandidates.value = []
  parseAttempted.value = false
  showSummaryParser.value = true
}

function runParse() {
  parsedCandidates.value = meetingSummaryParser.parse(summaryText.value, { knownUsers: usersStore.users })
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
    recurrenceEnabled: !!meeting.value.recurrence,
    recurrenceFreq: meeting.value.recurrence?.freq || 'weekly',
    recurrenceWeekdays: [...(meeting.value.recurrence?.weekdays || [])],
  }
  editing.value = true
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
  await meetingsStore.updateMeeting(props.id, {
    title: editDraft.value.title.trim(),
    date: isoDate,
    description: editDraft.value.description.trim(),
    link: editDraft.value.link.trim(),
    attendeeIds: [...editDraft.value.attendeeIds],
    recurrence,
  })
  editing.value = false
}

async function removeMeeting() {
  if (!confirm('Удалить встречу? Задачи останутся, но потеряют привязку к ней.')) return
  for (const t of tasksStore.tasks.filter((x) => x.meetingId === props.id)) {
    await tasksStore.updateTaskField(t.id, 'meetingId', null)
  }
  await meetingsStore.removeMeeting(props.id)
  router.push('/meetings')
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
        <button class="btn btn-sm" @click="openSummaryParser"><AppIcon name="layers" :size="13" /> Разбор резюме в задачи</button>
        <button class="btn btn-sm" @click="startEdit"><AppIcon name="edit" :size="13" /> Редактировать</button>
        <button class="btn btn-sm btn-danger" @click="removeMeeting"><AppIcon name="trash" :size="13" /> Удалить</button>
      </div>
    </div>

    <div class="meeting-header card">
      <h2 class="meeting-title"><AppIcon name="calendar" :size="17" /> {{ meeting.title }}</h2>
      <div class="meeting-meta meeting-meta-wrap">
        <span class="meta-item"><AppIcon name="alarm" :size="12" /> {{ formatDateTime(meeting.date) }}</span>
        <span class="meeting-recurrence meta-item"><AppIcon name="repeat" :size="12" /> {{ recurrenceLabel }}</span>
        <a v-if="meeting.link" :href="meeting.link" target="_blank" rel="noopener" class="meta-item meeting-link"><AppIcon name="link" :size="12" /> Присоединиться к звонку</a>
        <span v-if="author">· Автор: {{ author.name }}</span>
      </div>
      <p v-if="meeting.description" class="meeting-description">{{ meeting.description }}</p>
      <div v-if="attendees.length" class="meeting-attendees">
        <span class="attendees-label">Участники:</span>
        <span v-for="u in attendees" :key="u.id" class="tag attendee-tag">{{ u.name }}</span>
      </div>
    </div>

    <h3 class="tasks-title">Задачи встречи</h3>
    <QuickFiltersBar :task-count="meetingTasks.length" :meeting-mode="true" />
    <QuickAddTaskRow
      :meeting-id="props.id"
      placeholder="Добавить задачу по итогам встречи..."
    />
    <TaskListPanel :tasks="meetingTasks" :meeting-mode="true" empty-text="К этой встрече пока не привязано ни одной задачи" />

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
            Его эвристика на основе regex, не NLP — ничего не создаётся без вашего подтверждения.
          </p>
          <div class="field-group">
            <label>Текст резюме</label>
            <textarea v-model="summaryText" rows="8" placeholder="- Согласовать бюджет до пятницы&#10;Иван: подготовить презентацию&#10;1. Отправить письмо клиенту" />
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
            <div class="field-group">
              <label>Дата</label>
              <input v-model="editDraft.date" type="date" />
            </div>
            <div class="field-group">
              <label>Время</label>
              <input v-model="editDraft.time" type="time" />
            </div>
          </div>
          <div class="field-group">
            <label>Ссылка на звонок</label>
            <input v-model="editDraft.link" placeholder="https://meet.example.com/..." />
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
          <button class="btn btn-ghost" @click="editing = false">Отмена</button>
          <button class="btn btn-primary" :disabled="!editDraft.title.trim() || !editDraft.date" @click="saveEdit">Сохранить</button>
        </div>
      </div>
    </div>
  </template>
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.back-btn { padding-left: 4px; display: inline-flex; align-items: center; gap: 4px; }
.header-actions { display: flex; gap: 8px; }

.meeting-header { padding: 16px 18px; margin-bottom: 18px; }
.meeting-title { margin: 0 0 6px; font-size: 18px; display: flex; align-items: center; gap: 8px; }
.meeting-meta { display: flex; gap: 10px; font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 8px; }
.meeting-meta-wrap { flex-wrap: wrap; }
.meta-item { display: inline-flex; align-items: center; gap: 5px; }
.meeting-recurrence { color: var(--color-text); font-weight: 500; }
.meeting-link { color: var(--color-primary); font-weight: 600; text-decoration: none; }
.meeting-link:hover { text-decoration: underline; }
.meeting-description { margin: 0 0 8px; font-size: 13px; color: var(--color-text); line-height: 1.5; white-space: pre-wrap; }
.meeting-attendees { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.attendees-label { font-size: 11.5px; color: var(--color-text-muted); }
.attendee-tag { background: #f4f0ff; color: #7c5cd6; }

.tasks-title { font-size: 13px; font-weight: 600; margin: 0 0 8px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.03em; }
.empty-state { color: var(--color-text-muted); font-size: 13px; text-align: center; padding: 40px 0; }

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

.modal-wide { width: 560px; }
.hint-text { font-size: 12px; color: var(--color-text-muted); line-height: 1.5; margin: 0 0 4px; }
.parse-results { margin-top: 8px; display: flex; flex-direction: column; gap: 8px; }
.empty-state-inline { font-size: 12.5px; color: var(--color-text-muted); padding: 10px; text-align: center; }
.section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted); border-top: 1px solid var(--color-border); padding-top: 10px; }
.candidate-row { display: flex; align-items: flex-start; gap: 8px; padding: 6px 4px; border-bottom: 1px solid var(--color-border); }
.candidate-main { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.candidate-title-input { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 13px; width: 100%; }
.candidate-meta { display: flex; gap: 6px; flex-wrap: wrap; font-size: 11px; }
</style>
