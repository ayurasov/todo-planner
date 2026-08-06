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
import { formatDateTime } from '../utils/formatters'
import { meetingSummaryParser, MATCHED_PATTERN_LABEL } from '../services/MeetingSummaryParser'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const meetingsStore = useMeetingsStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const isAdmin = useIsAdmin()

const editing = ref(false)
const editDraft = ref({ title: '', date: '', time: '', description: '' })

const showSummaryParser = ref(false)
const summaryText = ref('')
const parsedCandidates = ref([])
const parseAttempted = ref(false)

onMounted(async () => {
  if (!meetingsStore.loaded) await meetingsStore.load()
  if (!tasksStore.loaded) await tasksStore.load()
  if (!listsStore.loaded) await listsStore.load()
})

const meeting = computed(() => meetingsStore.meetingById(props.id))
const author = computed(() => (meeting.value ? usersStore.byId(meeting.value.createdBy) : null))
const meetingTasks = computed(() => tasksStore.tasks.filter((t) => t.meetingId === props.id && !t.parentTaskId))

/**
 * Права на редактирование/удаление встречи: автор встречи или системный
 * администратор. Явное допущение: встреча — сущность вне ролевой модели
 * списков (у неё нет собственного списка участников), поэтому правило
 * "Owner/Editor" из ТЗ трактуется как "Owner/Editor хотя бы одного списка,
 * к которому привязаны задачи этой встречи" — это покрывает типичный кейс
 * (постановщик встречи обычно владеет соответствующим списком задач).
 */
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

const defaultListId = computed(() => listsStore.lists[0]?.id)

function openSummaryParser() {
  summaryText.value = meeting.value?.description || ''
  parsedCandidates.value = []
  parseAttempted.value = false
  showSummaryParser.value = true
}

/**
 * Разбор резюме — эвристика на regex (MockRegexSummaryParser), без
 * реального NLP (см. раздел 3.7 ТЗ и комментарий в MeetingSummaryParser.js).
 * Результат — предварительный список кандидатов, ничего не сохраняется
 * до явного подтверждения пользователем в форме ниже.
 */
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
      listId: defaultListId.value,
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
  }
  editing.value = true
}

async function saveEdit() {
  if (!editDraft.value.title.trim() || !editDraft.value.date) return
  const isoDate = new Date(`${editDraft.value.date}T${editDraft.value.time || '00:00'}`).toISOString()
  await meetingsStore.updateMeeting(props.id, {
    title: editDraft.value.title.trim(),
    date: isoDate,
    description: editDraft.value.description.trim(),
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
        <button class="btn btn-ghost btn-sm back-btn" @click="router.push('/meetings')">← Встречи</button>
      </div>
      <div v-if="canManageMeeting" class="header-actions">
        <button class="btn btn-sm" @click="openSummaryParser">🧩 Разбор резюме в задачи</button>
        <button class="btn btn-sm" @click="startEdit">✎ Редактировать</button>
        <button class="btn btn-sm btn-danger" @click="removeMeeting">🗑 Удалить</button>
      </div>
    </div>

    <div class="meeting-header card">
      <h2 class="meeting-title">📅 {{ meeting.title }}</h2>
      <div class="meeting-meta">
        <span>🕐 {{ formatDateTime(meeting.date) }}</span>
        <span v-if="author">· Автор: {{ author.name }}</span>
      </div>
      <p v-if="meeting.description" class="meeting-description">{{ meeting.description }}</p>
    </div>

    <h3 class="tasks-title">Задачи встречи</h3>
    <QuickFiltersBar />
    <QuickAddTaskRow
      v-if="defaultListId"
      :list-id="defaultListId"
      :meeting-id="props.id"
      placeholder="Добавить задачу по итогам встречи..."
    />
    <TaskListPanel :tasks="meetingTasks" empty-text="К этой встрече пока не привязано ни одной задачи" />

    <div v-if="showSummaryParser" class="modal-overlay" @click.self="showSummaryParser = false">
      <div class="modal modal-wide card scroll-thin">
        <div class="modal-header">
          <h3>Разбор резюме встречи в задачи</h3>
          <button class="btn btn-ghost btn-sm" @click="showSummaryParser = false">✕</button>
        </div>
        <div class="modal-body">
          <p class="hint-text">
            Вставьте текстовое резюме встречи. Кандидатами в задачи считаются строки,
            начинающиеся с "-", "•", номера пункта, либо в формате "Имя: сделать...".
            Это эвристика на основе regex, не NLP — ничего не создаётся без вашего подтверждения.
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
                <button class="btn btn-ghost btn-sm" @click="removeCandidate(idx)">✕</button>
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

    <div v-if="editing" class="modal-overlay" @click.self="editing = false">
      <div class="modal card scroll-thin">
        <div class="modal-header">
          <h3>Редактировать встречу</h3>
          <button class="btn btn-ghost btn-sm" @click="editing = false">✕</button>
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
            <label>Описание</label>
            <textarea v-model="editDraft.description" rows="3" />
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
.back-btn { padding-left: 4px; }
.header-actions { display: flex; gap: 8px; }

.meeting-header { padding: 16px 18px; margin-bottom: 18px; }
.meeting-title { margin: 0 0 6px; font-size: 18px; }
.meeting-meta { display: flex; gap: 10px; font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 8px; }
.meeting-description { margin: 0; font-size: 13px; color: var(--color-text); line-height: 1.5; white-space: pre-wrap; }

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
