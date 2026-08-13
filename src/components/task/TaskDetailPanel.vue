<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { useHistoryStore } from '../../stores/historyStore'
import { useListsStore } from '../../stores/listsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { TaskPriority, TaskStatus, PRIORITY_LABEL } from '../../domain/entities/enums'
import { formatDateTime, formatDate } from '../../utils/formatters'
import { useTaskPermissions } from '../../composables/usePermissions'
import AppIcon from '../common/AppIcon.vue'
import RichTextEditor from '../common/RichTextEditor.vue'
import ConfirmModal from '../common/ConfirmModal.vue'

const props = defineProps({ task: { type: Object, required: true } })
const emit = defineEmits(['close'])

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const historyStore = useHistoryStore()
const listsStore = useListsStore()
const meetingsStore = useMeetingsStore()
const prefs = usePreferencesStore()

const activityTab = ref('comments')
const newChecklistTitle = ref('')
const newCommentTab = ref('')
const noteContent = ref('')
const editingTitle = ref(false)
const titleDraft = ref(props.task.title)
const titleInputEl = ref(null)
const assigneeMenuOpen = ref(false)
const assigneeSearch = ref('')
const assigneeSearchInput = ref(null)
const confirmDeleteOpen = ref(false)

const liveTask = computed(() => tasksStore.byId(props.task.id) || props.task)
const { canEditThisTask, canToggleStatus, canDeleteThisTask, reason: permissionReason } = useTaskPermissions(liveTask)
const checklist = computed(() => tasksStore.checklistByTask[props.task.id] || [])
const notes = computed(() => tasksStore.notesByTask[props.task.id] || [])
const timeline = computed(() => historyStore.timelineByTask[props.task.id] || [])
const comments = computed(() => tasksStore.commentsByTask[props.task.id] || [])
const parentList = computed(() => listsStore.byId(liveTask.value.listId))
const commentsAllowed = computed(() => parentList.value?.settings?.allowComments !== false)
const isSubtask = computed(() => !!liveTask.value.parentTaskId)
const parentTask = computed(() => isSubtask.value ? tasksStore.byId(liveTask.value.parentTaskId) : null)
const linkedMeeting = computed(() => liveTask.value.meetingId ? meetingsStore.meetingById(liveTask.value.meetingId) : null)
const linkedMeetingOccurrences = computed(() => (
  linkedMeeting.value?.recurrence ? meetingsStore.occurrencesOf(linkedMeeting.value.id) : []
))
async function changeTaskOccurrence(event) {
  const value = event.target.value
  await tasksStore.updateTaskField(liveTask.value.id, 'occurrenceId', value || null)
}
const currentAssignee = computed(() => usersStore.byId(liveTask.value.assigneeId))
const checklistProgress = computed(() => {
  if (!checklist.value.length) return null
  const done = checklist.value.filter((i) => i.done).length
  return `${done}/${checklist.value.length}`
})
const checklistPercent = computed(() => {
  if (!checklist.value.length) return 0
  return Math.round((checklist.value.filter((i) => i.done).length / checklist.value.length) * 100)
})

const assignableUsers = computed(() => usersStore.assignableUsers || [])
const meetingAttendeeIds = computed(() => new Set(linkedMeeting.value?.attendeeIds || []))
const searchQuery = computed(() => assigneeSearch.value.trim().toLowerCase())

const suggestedUsers = computed(() => {
  if (!meetingAttendeeIds.value.size) return []
  return assignableUsers.value.filter((u) => {
    if (!meetingAttendeeIds.value.has(u.id)) return false
    if (!searchQuery.value) return true
    return u.name.toLowerCase().includes(searchQuery.value)
  })
})

const allOtherUsers = computed(() => {
  return assignableUsers.value.filter((u) => {
    if (meetingAttendeeIds.value.has(u.id)) return false
    if (!searchQuery.value) return true
    return u.name.toLowerCase().includes(searchQuery.value)
  })
})

const allUsersFiltered = computed(() => {
  if (meetingAttendeeIds.value.size) return allOtherUsers.value
  return assignableUsers.value.filter((u) => {
    if (!searchQuery.value) return true
    return u.name.toLowerCase().includes(searchQuery.value)
  })
})

watch(assigneeMenuOpen, (val) => {
  if (val) {
    assigneeSearch.value = ''
    nextTick(() => assigneeSearchInput.value?.focus())
  }
})

const PRIORITY_COLOR = { low: '#9aa3b2', medium: '#4f7cff', high: '#e8a13a', urgent: '#e5484d' }
const STATUS_META = {
  open: { label: 'Не начато', color: '#6b7280', bg: '#eef1f7' },
  in_progress: { label: 'В работе', color: '#4f7cff', bg: '#eaf0ff' },
  done: { label: 'Выполнено', color: '#1e9e4d', bg: '#e4f6ea' },
  cancelled: { label: 'Отменено', color: '#9aa3b2', bg: '#f1f2f5' },
}

function htmlToNoteDoc(html) {
  return { type: 'doc', content: [{ type: 'paragraph', text: html || '' }] }
}

onMounted(async () => {
  if (!meetingsStore.loaded) await meetingsStore.load()
  await tasksStore.loadChecklist(props.task.id)
  await tasksStore.loadNotes(props.task.id)
  await tasksStore.loadComments(props.task.id)
  await historyStore.loadTaskTimeline(props.task.id)
  if (notes.value[0]) noteContent.value = notes.value[0].contentJSON?.content?.[0]?.text || ''
})

function updateField(field, value) {
  tasksStore.updateTaskField(props.task.id, field, value)
}
function startEditTitle() { titleDraft.value = liveTask.value.title; editingTitle.value = true; nextTick(() => titleInputEl.value?.focus()) }
function commitTitle() { editingTitle.value = false; const trimmed = titleDraft.value.trim(); if (trimmed && trimmed !== liveTask.value.title) updateField('title', trimmed) }
function cancelEditTitle() { editingTitle.value = false; titleDraft.value = liveTask.value.title }
function requestDelete() { confirmDeleteOpen.value = true }
function confirmDelete() { tasksStore.removeTask(liveTask.value.id); confirmDeleteOpen.value = false; emit('close') }
function cancelDelete() { confirmDeleteOpen.value = false }
function setStatus(s) { updateField('status', s) }
function setPriority(p) { updateField('priority', p) }
function assign(userId) { tasksStore.assignTask(liveTask.value.id, userId); assigneeMenuOpen.value = false }
async function addChecklistItem() { if (!newChecklistTitle.value.trim()) return; await tasksStore.addChecklistItem(props.task.id, newChecklistTitle.value.trim()); newChecklistTitle.value = '' }
async function submitComment() { if (!newCommentTab.value.trim()) return; await tasksStore.addComment(props.task.id, newCommentTab.value.trim()); newCommentTab.value = ''; await historyStore.loadTaskTimeline(props.task.id) }
async function saveNote() { const existingNoteId = notes.value[0]?.id; await tasksStore.saveNote(props.task.id, existingNoteId, htmlToNoteDoc(noteContent.value)) }
function updateDescription(html) { updateField('description', html) }

const HISTORY_LABEL = {
  created: 'Создана', field_changed: 'Изменено поле', commented: 'Комментарий',
  assignee_changed: 'Изменён исполнитель', rescheduled: 'Перенесён срок', completed: 'Выполнена', reopened: 'Возвращена в работу',
}
const HISTORY_ICON = {
  created: 'plus', field_changed: 'edit', commented: 'message', assignee_changed: 'team',
  rescheduled: 'calendar', completed: 'check', reopened: 'undo',
}
</script>

<template>
  <Teleport to="body">
    <div class="panel-overlay" @click.self="emit('close')">
      <Transition name="modal-pop" appear>
        <div class="detail-modal card">
          <div class="panel-header">...</div>
        </div>
      </Transition>
    </div>
  </Teleport>

  <ConfirmModal
    v-if="confirmDeleteOpen"
    title="Удалить задачу?"
    message="Задача и все её подзадачи будут удалены без возможности восстановления."
    confirm-text="Удалить"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
