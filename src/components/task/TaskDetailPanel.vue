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

// Сортировка списков комментариев/истории по давности.
// История по умолчанию — от новых к старым (desc). Комментарии по умолчанию — от старых к новым (desc = false),
// чтобы вести диалог сверху вниз как обычно принято, но пользователь может переключить порядок иконкой.
const commentsSortDesc = ref(false)
const historySortDesc = ref(true)

const liveTask = computed(() => tasksStore.byId(props.task.id) || props.task)
const { canEditThisTask, canToggleStatus, canDeleteThisTask, reason: permissionReason } = useTaskPermissions(liveTask)
const checklist = computed(() => tasksStore.checklistByTask[props.task.id] || [])
const notes = computed(() => tasksStore.notesByTask[props.task.id] || [])
const timeline = computed(() => historyStore.timelineByTask[props.task.id] || [])
const comments = computed(() => tasksStore.commentsByTask[props.task.id] || [])

const sortedComments = computed(() => {
  const arr = [...comments.value].sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
  return commentsSortDesc.value ? arr.reverse() : arr
})

const sortedTimeline = computed(() => {
  const arr = [...timeline.value].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  return historySortDesc.value ? arr.reverse() : arr
})

function toggleCommentsSort() { commentsSortDesc.value = !commentsSortDesc.value }
function toggleHistorySort() { historySortDesc.value = !historySortDesc.value }

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

// Используем assignableUsers чтобы исключить системных пользователей
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

function startEditTitle() {
  titleDraft.value = liveTask.value.title
  editingTitle.value = true
  nextTick(() => titleInputEl.value?.focus())
}

function commitTitle() {
  editingTitle.value = false
  const trimmed = titleDraft.value.trim()
  if (trimmed && trimmed !== liveTask.value.title) updateField('title', trimmed)
}

function cancelEditTitle() {
  editingTitle.value = false
  titleDraft.value = liveTask.value.title
}

function requestDelete() {
  confirmDeleteOpen.value = true
}

function confirmDelete() {
  tasksStore.removeTask(liveTask.value.id)
  confirmDeleteOpen.value = false
  emit('close')
}

function cancelDelete() {
  confirmDeleteOpen.value = false
}

function setStatus(s) { updateField('status', s) }
function setPriority(p) { updateField('priority', p) }

function assign(userId) {
  tasksStore.assignTask(liveTask.value.id, userId)
  assigneeMenuOpen.value = false
}

async function addChecklistItem() {
  if (!newChecklistTitle.value.trim()) return
  await tasksStore.addChecklistItem(props.task.id, newChecklistTitle.value.trim())
  newChecklistTitle.value = ''
}

async function submitComment() {
  if (!newCommentTab.value.trim()) return
  await tasksStore.addComment(props.task.id, newCommentTab.value.trim())
  newCommentTab.value = ''
  await historyStore.loadTaskTimeline(props.task.id)
}

async function saveNote() {
  const existingNoteId = notes.value[0]?.id
  await tasksStore.saveNote(props.task.id, existingNoteId, htmlToNoteDoc(noteContent.value))
}

function updateDescription(html) {
  updateField('description', html)
}

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
          <div class="panel-header">
            <div class="header-top">
              <div class="meta-crumbs">
                <span v-if="isSubtask && parentTask" class="parent-crumb">↓ {{ parentTask.title }}</span>
                <div v-if="parentList" class="list-crumb">
                  <AppIcon name="folder" :size="13" /> <span class="list-crumb-title">{{ parentList.title }}</span>
                </div>
                <div v-if="linkedMeeting" class="meeting-crumb">
                  <AppIcon name="calendar" :size="13" /> <span class="meeting-crumb-title">{{ linkedMeeting.title }}</span>
                  <span class="meeting-crumb-date">{{ formatDateTime(linkedMeeting.date) }}</span>
                  <select
                    v-if="linkedMeetingOccurrences.length" class="occurrence-picker" :value="liveTask.occurrenceId || ''"
                    :disabled="!canEditThisTask" title="Подвстреча серии" @change="changeTaskOccurrence"
                  >
                    <option value="">Без привязки к подвстрече</option>
                    <option v-for="occ in linkedMeetingOccurrences" :key="occ.id" :value="occ.id">{{ formatDateTime(occ.date) }}</option>
                  </select>
                </div>
              </div>
              <div class="header-actions">
                <button v-if="canDeleteThisTask" class="btn btn-ghost close-btn btn-danger" title="Удалить задачу" @click="requestDelete"><AppIcon name="trash" :size="15" /></button>
                <button class="btn btn-ghost close-btn" @click="emit('close')"><AppIcon name="close" :size="15" /></button>
              </div>
            </div>
            <input
              v-if="editingTitle"
              ref="titleInputEl"
              v-model="titleDraft"
              class="title-edit-input"
              @blur="commitTitle"
              @keyup.enter="commitTitle"
              @keyup.escape="cancelEditTitle"
            />
            <h2 v-else class="title-display" :class="{ 'title-readonly': !canEditThisTask }" @click="canEditThisTask && startEditTitle()">
              <span v-if="liveTask.pinned" class="pin-icon"><AppIcon name="pin" :size="15" /></span>{{ liveTask.title }}
            </h2>
            <p v-if="!canEditThisTask" class="readonly-banner"><AppIcon name="eye" :size="12" /> Только просмотр — {{ permissionReason }}</p>
          </div>

          <div class="panel-body scroll-thin">
            <div class="body-columns">
              <div class="main-column">
                <section class="content-section">
                  <h3 class="section-heading"><AppIcon name="edit" :size="13" /> Описание</h3>
                  <RichTextEditor
                    :model-value="liveTask.description"
                    :editable="canEditThisTask"
                    placeholder="Добавьте описание задачи..."
                    class="description-editor"
                    @update:model-value="updateDescription"
                  />
                </section>

                <section class="content-section checklist-section">
                  <h3 class="section-heading">
                    <AppIcon name="checklist" :size="13" /> Чек-лист
                    <span v-if="checklistProgress" class="tab-badge">{{ checklistProgress }}</span>
                  </h3>
                  <div v-if="checklist.length" class="progress-bar-track">
                    <div class="progress-bar-fill" :style="{ width: checklistPercent + '%' }" />
                  </div>
                  <div v-for="item in checklist" :key="item.id" class="checklist-item">
                    <input type="checkbox" :checked="item.done" :disabled="!canEditThisTask" @change="tasksStore.toggleChecklistItem(liveTask.id, item.id)" />
                    <span :class="{ done: item.done }">{{ item.title }}</span>
                    <button v-if="canEditThisTask" class="btn btn-ghost btn-sm remove-btn" @click="tasksStore.removeChecklistItem(liveTask.id, item.id)"><AppIcon name="close" :size="11" /></button>
                  </div>
                  <div v-if="canEditThisTask" class="checklist-add">
                    <input v-model="newChecklistTitle" placeholder="Новый пункт чек-листа" @keyup.enter="addChecklistItem" />
                    <button class="btn btn-primary btn-sm" @click="addChecklistItem">Добавить</button>
                  </div>
                  <p v-else-if="!checklist.length" class="hint-text">Пунктов чек-листа пока нет</p>
                </section>
              </div>

              <aside class="side-column">
                <div class="field-block">
                  <span class="field-caption">Статус</span>
                  <div class="segmented-pills segmented-pills-vertical">
                    <button
                      v-for="s in Object.values(TaskStatus)" :key="s"
                      class="pill" :class="{ active: liveTask.status === s }"
                      :disabled="!canToggleStatus"
                      :style="liveTask.status === s ? { background: STATUS_META[s].bg, color: STATUS_META[s].color } : {}"
                      @click="setStatus(s)"
                    >{{ STATUS_META[s].label }}</button>
                  </div>
                </div>

                <div class="field-block">
                  <span class="field-caption">Приоритет</span>
                  <div class="segmented-pills segmented-pills-vertical">
                    <button
                      v-for="p in Object.values(TaskPriority)" :key="p"
                      class="pill pill-dot" :class="{ active: liveTask.priority === p }"
                      :disabled="!canEditThisTask"
                      :style="liveTask.priority === p ? { background: PRIORITY_COLOR[p], color: '#fff', borderColor: PRIORITY_COLOR[p] } : {}"
                      @click="setPriority(p)"
                    >
                      <span class="dot" :style="{ background: liveTask.priority === p ? '#fff' : PRIORITY_COLOR[p] }" />
                      {{ PRIORITY_LABEL[p] }}
                    </button>
                  </div>
                </div>

                <div class="field-block">
                  <span class="field-caption">Исполнитель</span>
                  <div class="assignee-picker">
                    <button class="assignee-trigger" :disabled="!canEditThisTask" @click="canEditThisTask && (assigneeMenuOpen = !assigneeMenuOpen)">
                      <span class="assignee-avatar" :class="{ empty: !currentAssignee }">
                        {{ currentAssignee ? currentAssignee.name.charAt(0) : '—' }}
                      </span>
                      <span>{{ currentAssignee ? currentAssignee.name : 'Не назначен' }}</span>
                      <span class="chevron"><AppIcon name="chevronDown" :size="10" /></span>
                    </button>

                    <div v-if="assigneeMenuOpen" class="assignee-dropdown card scroll-thin">
                      <div class="assignee-search-wrap">
                        <input
                          ref="assigneeSearchInput"
                          v-model="assigneeSearch"
                          class="assignee-search-input"
                          placeholder="Поиск пользователя..."
                          @keyup.escape="assigneeMenuOpen = false"
                        />
                      </div>

                      <template v-if="suggestedUsers.length">
                        <div class="assignee-section-label">Участники встречи</div>
                        <button
                          v-for="u in suggestedUsers" :key="u.id"
                          class="assignee-option" :class="{ active: liveTask.assigneeId === u.id }"
                          @click="assign(u.id)"
                        >
                          <span class="assignee-avatar">{{ u.name.charAt(0) }}</span>{{ u.name }}
                        </button>
                        <div class="assignee-section-divider" />
                      </template>

                      <div class="assignee-section-label">Все пользователи</div>
                      <template v-if="allUsersFiltered.length">
                        <button
                          v-for="u in allUsersFiltered" :key="u.id"
                          class="assignee-option" :class="{ active: liveTask.assigneeId === u.id }"
                          @click="assign(u.id)"
                        >
                          <span class="assignee-avatar">{{ u.name.charAt(0) }}</span>{{ u.name }}
                        </button>
                      </template>
                      <div v-else class="assignee-no-results">Пользователи не найдены</div>

                      <div class="assignee-section-divider" />
                      <button class="assignee-option" @click="assign(null)">
                        <span class="assignee-avatar empty">—</span>Без исполнителя
                      </button>
                    </div>
                  </div>
                </div>

                <div class="field-block">
                  <span class="field-caption">Срок</span>
                  <input type="date" class="date-input" :disabled="!canEditThisTask" :value="liveTask.dueDate ? liveTask.dueDate.slice(0,10) : ''"
                    @change="tasksStore.rescheduleTask(liveTask.id, $event.target.value ? new Date($event.target.value).toISOString() : null)" />
                </div>

                <div v-if="(prefs.showCompletedDate && liveTask.completedAt) || (prefs.showLastUpdatedDate && liveTask.updatedAt)" class="dates-meta-block">
                  <span v-if="prefs.showCompletedDate && liveTask.completedAt" class="dates-meta-item dates-meta-done"><AppIcon name="check" :size="11" /> Выполнено: {{ formatDate(liveTask.completedAt) }}</span>
                  <span v-if="prefs.showLastUpdatedDate && liveTask.updatedAt" class="dates-meta-item"><AppIcon name="edit" :size="11" /> Изменено: {{ formatDate(liveTask.updatedAt) }}</span>
                </div>
              </aside>
            </div>

            <section class="activity-section">
              <div class="tabs-row">
                <div class="tabs">
                  <button :class="{ active: activityTab === 'comments' }" @click="activityTab = 'comments'" v-if="commentsAllowed">
                    Комментарии <span v-if="comments.length" class="tab-badge">{{ comments.length }}</span>
                  </button>
                  <button :class="{ active: activityTab === 'notes' }" @click="activityTab = 'notes'">Заметки</button>
                  <button :class="{ active: activityTab === 'history' }" @click="activityTab = 'history'">История</button>
                </div>
                <button
                  v-if="activityTab === 'comments' && commentsAllowed && comments.length > 1"
                  class="sort-toggle-btn"
                  :title="commentsSortDesc ? 'Сначала новые' : 'Сначала старые'"
                  @click="toggleCommentsSort"
                >
                  <AppIcon name="sort" :size="14" />
                </button>
                <button
                  v-if="activityTab === 'history' && timeline.length > 1"
                  class="sort-toggle-btn"
                  :title="historySortDesc ? 'Сначала новые' : 'Сначала старые'"
                  @click="toggleHistorySort"
                >
                  <AppIcon name="sort" :size="14" />
                </button>
              </div>

              <div class="activity-content">
                <Transition name="fade-tab" mode="out-in">
                <div v-if="activityTab === 'comments' && commentsAllowed" key="comments" class="comments-tab">
                  <div v-for="c in sortedComments" :key="c.id" class="comment-row">
                    <span class="comment-avatar">{{ (usersStore.byId(c.authorId)?.name || '?').charAt(0) }}</span>
                    <div class="comment-body">
                      <div class="comment-header">
                        <strong>{{ usersStore.byId(c.authorId)?.name || c.authorId }}</strong>
                        <span class="comment-time">{{ formatDateTime(c.createdAt) }}<span v-if="c.editedAt"> (ред.)</span></span>
                      </div>
                      <p class="comment-text">{{ c.text }}</p>
                    </div>
                  </div>
                  <div v-if="!comments.length" class="hint-text">Пока нет комментариев</div>
                  <div class="comment-box">
                    <textarea v-model="newCommentTab" placeholder="Написать комментарий..." rows="2" />
                    <button class="btn btn-primary btn-sm comment-submit-btn" @click="submitComment">Отправить</button>
                  </div>
                </div>

                <div v-else-if="activityTab === 'notes'" key="notes" class="notes-tab">
                  <RichTextEditor v-model="noteContent" placeholder="Текст заметки..." @update:model-value="saveNote" />
                </div>

                <div v-else-if="activityTab === 'history'" key="history" class="history-tab">
                  <div v-for="entry in sortedTimeline" :key="entry.id" class="history-entry">
                    <span class="history-icon"><AppIcon :name="HISTORY_ICON[entry.type] || 'more'" :size="12" /></span>
                    <div class="history-body">
                      <span class="history-type">{{ HISTORY_LABEL[entry.type] || entry.type }}</span>
                      <span class="history-detail" v-if="entry.field">{{ entry.field }}: {{ entry.oldValue }} → {{ entry.newValue }}</span>
                      <span class="history-detail" v-if="entry.comment">"{{ entry.comment }}"</span>
                      <span class="history-meta">{{ historyStore.actorName(entry.actorId) }} · {{ formatDateTime(entry.timestamp) }}</span>
                    </div>
                  </div>
                  <div v-if="!timeline.length" class="hint-text">История пока пуста</div>
                </div>
                </Transition>
              </div>
            </section>
          </div>

          <div class="panel-footer">
            <button class="btn btn-secondary btn-sm" @click="emit('close')">Закрыть</button>
          </div>
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

<style scoped>
.panel-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; padding: 24px; backdrop-filter: blur(1px); }
.detail-modal {
  width: min(920px, 100%); max-height: 92vh; border-radius: 14px; display: flex; flex-direction: column;
  overflow: hidden; box-shadow: var(--shadow-2, 0 12px 40px rgba(20,24,38,0.22));
}

.modal-pop-enter-active, .modal-pop-leave-active { transition: transform 0.18s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.18s ease; }
.modal-pop-enter-from, .modal-pop-leave-to { transform: scale(0.97) translateY(6px); opacity: 0; }

.panel-header { padding: 18px 24px 12px; border-bottom: 1px solid var(--color-border); flex-shrink: 0; }
.header-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.meta-crumbs { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.parent-crumb { font-size: 12px; color: var(--color-text-muted); }
.header-actions { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.close-btn { border-radius: 8px; width: 30px; height: 30px; padding: 0; display: flex; align-items: center; justify-content: center; }
.close-btn.btn-danger { color: var(--color-danger); }
.close-btn.btn-danger:hover { background: #fdeeee; }
.title-display { margin: 4px 0 0; font-size: 20px; font-weight: 650; cursor: text; padding: 4px 6px; border-radius: 8px; display: flex; align-items: center; gap: 6px; }
.title-display:hover { background: #f6f7fb; }
.title-readonly { cursor: default; }
.title-readonly:hover { background: none; }
.readonly-banner { font-size: 12px; color: var(--color-text-muted); background: #f1f3f9; border-radius: 8px; padding: 6px 10px; margin: 8px 0 0; display: flex; align-items: center; gap: 6px; width: fit-content; }
.title-edit-input { width: 100%; font-size: 20px; font-weight: 650; border: 1.5px solid var(--color-primary); border-radius: 8px; padding: 6px 8px; margin: 4px 0 0; outline: none; }

.panel-body { flex: 1; overflow-y: auto; padding: 20px 24px 24px; }
.body-columns { display: grid; grid-template-columns: minmax(0, 1fr) 240px; gap: 28px; align-items: start; }

.main-column { display: flex; flex-direction: column; gap: 24px; min-width: 0; }
.content-section { min-width: 0; }
.section-heading {
  display: flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.03em; color: var(--color-text-muted); margin: 0 0 10px;
}

/* Пункт 1: увеличенная стандартная высота поля описания задачи */
.description-editor :deep(.rich-content) { min-height: 260px; }

.side-column { display: flex; flex-direction: column; gap: 18px; background: #fafbfd; border: 1px solid var(--color-border); border-radius: 12px; padding: 14px; }
.field-block { display: flex; flex-direction: column; gap: 6px; }
.field-caption { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted); }

.segmented-pills { display: flex; gap: 5px; flex-wrap: wrap; }
.segmented-pills-vertical { flex-direction: column; align-items: stretch; }
.pill {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 8px;
  padding: 6px 12px; font-size: 12.5px; cursor: pointer; color: var(--color-text-muted);
  transition: all 0.12s ease; display: flex; align-items: center; gap: 5px; text-align: left;
}
.pill:hover { background: #f1f3f9; }
.pill.active { font-weight: 600; color: var(--color-text); border-color: transparent; }
.pill:disabled { opacity: 0.55; cursor: not-allowed; }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; flex-shrink: 0; }

.assignee-picker { position: relative; }
.assignee-trigger {
  display: flex; align-items: center; gap: 7px; border: 1px solid var(--color-border); background: var(--color-surface);
  border-radius: 8px; padding: 6px 10px 6px 5px; font-size: 12.5px; cursor: pointer; width: 100%;
}
.assignee-trigger:hover { background: #f1f3f9; }
.assignee-avatar {
  width: 22px; height: 22px; border-radius: 50%; background: var(--color-primary); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 700; flex-shrink: 0;
}
.assignee-avatar.empty { background: #d9dde8; color: var(--color-text-muted); }
.chevron { color: var(--color-text-muted); display: flex; margin-left: auto; }
.assignee-dropdown {
  position: absolute; top: 100%; left: 0; margin-top: 4px; width: 220px; z-index: 20;
  padding: 6px 0 4px; max-height: 320px; overflow-y: auto; box-shadow: var(--shadow-2);
}

.assignee-search-wrap { padding: 4px 8px 6px; }
.assignee-search-input {
  width: 100%; border: 1px solid var(--color-border); border-radius: 7px;
  padding: 5px 9px; font-size: 12.5px; outline: none; background: #f6f7fb;
}
.assignee-search-input:focus { border-color: var(--color-primary); background: #fff; }

.assignee-section-label {
  padding: 4px 12px 2px; font-size: 10.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-text-muted); user-select: none;
}

.assignee-section-divider { height: 1px; background: var(--color-border); margin: 4px 8px; }

.assignee-option {
  display: flex; align-items: center; gap: 8px; width: 100%; text-align: left; border: none; background: none;
  padding: 6px 12px; font-size: 12.5px; cursor: pointer;
}
.assignee-option:hover { background: #f1f3f9; }
.assignee-option.active { background: #eef2ff; font-weight: 600; }

.assignee-no-results { padding: 6px 12px; font-size: 12px; color: var(--color-text-muted); }

.date-input { border: 1px solid var(--color-border); border-radius: 8px; padding: 6px 10px; font-size: 12.5px; width: 100%; }

.dates-meta-block { display: flex; flex-direction: column; gap: 6px; font-size: 11.5px; color: var(--color-text-muted); border-top: 1px solid var(--color-border); padding-top: 12px; }
.dates-meta-item { opacity: 0.8; display: inline-flex; align-items: center; gap: 4px; }
.dates-meta-done { color: #1e9e4d; }

.checklist-section .progress-bar-track { height: 6px; background: #eef1f7; border-radius: 4px; margin-bottom: 12px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: var(--color-primary); border-radius: 4px; transition: width 0.2s ease; }
.checklist-item { display: flex; align-items: center; gap: 9px; padding: 6px 2px; border-radius: 8px; }
.checklist-item:hover { background: #fafbfe; }
.checklist-item:hover .remove-btn { opacity: 1; }
.checklist-item span.done { text-decoration: line-through; color: var(--color-text-muted); }
.checklist-item span { flex: 1; font-size: 13.5px; }
.remove-btn { opacity: 0; transition: opacity 0.12s; }
.checklist-add { display: flex; gap: 8px; margin-top: 12px; }
.checklist-add input { flex: 1; border: 1px dashed var(--color-border); border-radius: 8px; padding: 7px 10px; font-size: 13px; outline: none; }
.checklist-add input:focus { border-style: solid; border-color: var(--color-primary); }

.activity-section { margin-top: 26px; border-top: 1px solid var(--color-border); padding-top: 6px; }
.tabs-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.tabs { display: flex; gap: 2px; }
.tabs button {
  border: none; background: none; padding: 10px 12px; font-size: 13px; color: var(--color-text-muted);
  cursor: pointer; border-bottom: 2px solid transparent; display: flex; align-items: center; gap: 5px; transition: color 0.12s;
}
.tabs button:hover { color: var(--color-text); }
.tabs button.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 600; }
.tab-badge { background: #eef1f7; border-radius: 10px; padding: 1px 6px; font-size: 10.5px; font-weight: 700; color: var(--color-text-muted); }
.tabs button.active .tab-badge { background: #e6ecff; color: var(--color-primary-dark); }

/* Пункт 4: маленькая иконка сортировки комментариев/истории по давности справа от вкладок */
.sort-toggle-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 7px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--color-text-muted); cursor: pointer; flex-shrink: 0; transition: all 0.12s ease;
}
.sort-toggle-btn:hover { background: #f1f3f9; color: var(--color-text); }

.activity-content { padding: 14px 2px 4px; }
.fade-tab-enter-active, .fade-tab-leave-active { transition: opacity 0.12s ease; }
.fade-tab-enter-from, .fade-tab-leave-to { opacity: 0; }

.hint-text { font-size: 12px; color: var(--color-text-muted); margin-bottom: 10px; line-height: 1.5; }
.notes-tab :deep(.rich-content) { min-height: 180px; }

.history-entry { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--color-border); }
.history-entry:last-child { border-bottom: none; }
.history-icon { width: 24px; height: 24px; border-radius: 7px; background: #eef1f7; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: var(--color-text-muted); }
.history-body { display: flex; flex-direction: column; gap: 2px; font-size: 12.5px; }
.history-type { font-weight: 600; }
.history-detail { color: var(--color-text); }
.history-meta { color: var(--color-text-muted); font-size: 11px; }

.comment-row { display: flex; gap: 9px; padding: 10px 0; border-bottom: 1px solid var(--color-border); }
.comment-row:last-of-type { border-bottom: none; }
.comment-avatar { width: 26px; height: 26px; border-radius: 50%; background: var(--color-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.comment-body { flex: 1; }
.comment-header { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px; }
.comment-time { color: var(--color-text-muted); font-size: 11px; }
.comment-text { margin: 0; font-size: 13px; }
.comment-box { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.comment-box textarea { border: 1px solid var(--color-border); border-radius: 10px; padding: 10px; resize: vertical; font-size: 13px; outline: none; }
.comment-box textarea:focus { border-color: var(--color-primary); }
/* Пункт 2: кнопка отправки комментария по размеру текста, прижата к левому краю */
.comment-submit-btn { align-self: flex-start; width: auto; }
.pin-icon { display: flex; color: #c67d16; }
.meeting-crumb,
.list-crumb {
  display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--color-text-muted);
  background: #eef1f7; border-radius: 8px; padding: 6px 10px; width: fit-content;
}
.meeting-crumb-title,
.list-crumb-title { font-weight: 600; color: var(--color-text); }
.meeting-crumb-date { color: var(--color-text-muted); }
.occurrence-picker {
  font-size: 12px; border: 1px solid var(--color-border); border-radius: 6px;
  padding: 2px 6px; background: #fff; color: var(--color-text); margin-left: 4px;
}

/* Пункт 3: подвал окна с кнопкой «Закрыть», дублирующей закрытие окна */
.panel-footer {
  flex-shrink: 0; display: flex; justify-content: flex-end; align-items: center;
  padding: 12px 24px; border-top: 1px solid var(--color-border); background: var(--color-surface);
}

@media (max-width: 720px) {
  .body-columns { grid-template-columns: 1fr; }
  .side-column { order: -1; }
}
</style>
