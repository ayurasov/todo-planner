<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { useListsStore } from '../../stores/listsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { relativeDay, isOverdue, relativeTimeAgo, formatDate, formatDateTime } from '../../utils/formatters'
import { useTaskPermissions } from '../../composables/usePermissions'
import { useAssignableUsers } from '../../composables/useAssignableUsers'
import { useClickOutside } from '../../composables/useClickOutside'
import { getInitials, getAvatarColor } from '../../utils/avatar'
import PriorityBadge from './PriorityBadge.vue'
import TaskContextMenu from './TaskContextMenu.vue'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  task: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  bubbleMode: { type: Boolean, default: false },
})
const emit = defineEmits(['open'])

const router = useRouter()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const meetingsStore = useMeetingsStore()
const prefs = usePreferencesStore()

const expanded = ref(true)
const editingTitle = ref(false)
const titleDraft = ref(props.task.title)
const titleInputEl = ref(null)

const addingSubtask = ref(false)
const subtaskDraft = ref('')
const subtaskInputEl = ref(null)

const contextMenu = ref(null)
const checklistExpanded = ref(false)
const newInlineChecklistTitle = ref('')
const inlineChecklistInputEl = ref(null)

const children = computed(() => tasksStore.childrenOf(props.task.id))
const assignee = computed(() => usersStore.byId(props.task.assigneeId))
const list = computed(() => listsStore.byId(props.task.listId))
const overdue = computed(() => isOverdue(props.task.dueDate, props.task.status))
const isDone = computed(() => props.task.status === 'done')

const occurrenceInfo = computed(() => (props.task.occurrenceId ? meetingsStore.occurrenceById(props.task.occurrenceId) : null))
const occurrenceBadgeLabel = computed(() => {
  if (!occurrenceInfo.value) return null
  return `${occurrenceInfo.value.meeting.title} · ${formatDateTime(occurrenceInfo.value.occurrence.date)}`
})

function openOccurrenceMeeting() {
  if (!occurrenceInfo.value) return
  router.push(`/meetings/${occurrenceInfo.value.meeting.id}`)
}

const checklistItems = computed(() => tasksStore.checklistByTask[props.task.id])
const checklistCount = checklistItems
const commentsCount = computed(() => tasksStore.commentsByTask[props.task.id]?.length)

const { canEditThisTask, canToggleStatus, reason: permissionReason } = useTaskPermissions(() => props.task)

// --- Быстрое назначение исполнителя ---
const assignPickerOpen = ref(false)
const avatarBtnEl = ref(null)
const dropdownEl = ref(null)
const dropdownPos = ref({ top: 0, left: 0 })
const assignableUsers = useAssignableUsers(() => props.task)
useClickOutside(dropdownEl, () => { assignPickerOpen.value = false })

function toggleAssignPicker() {
  if (!canEditThisTask.value) return
  if (assignPickerOpen.value) { assignPickerOpen.value = false; return }
  const margin = 8
  const rect = avatarBtnEl.value.getBoundingClientRect()
  const dropdownW = 220
  const estimatedH = Math.min(260, 40 + assignableUsers.value.length * 34)
  let left = rect.right - dropdownW
  left = Math.min(Math.max(margin, left), window.innerWidth - dropdownW - margin)
  let top = rect.bottom + 4
  if (top + estimatedH > window.innerHeight - margin) top = Math.max(margin, rect.top - estimatedH - 4)
  dropdownPos.value = { top, left }
  assignPickerOpen.value = true
}

function quickAssign(userId) {
  tasksStore.assignTask(props.task.id, userId)
  assignPickerOpen.value = false
}

// --- Быстрый выбор срока ---
const datePickerOpen = ref(false)
const dueDateBtnEl = ref(null)
const datePickerEl = ref(null)
const datePickerPos = ref({ top: 0, left: 0 })
const customDate = ref('')
useClickOutside(datePickerEl, () => { datePickerOpen.value = false })

function toLocalYYYYMMDD(date) {
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function offsetDate(days) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d
}

function openDatePicker(e) {
  if (!canEditThisTask.value) return
  e.stopPropagation()
  if (datePickerOpen.value) { datePickerOpen.value = false; return }
  customDate.value = props.task.dueDate ? toLocalYYYYMMDD(props.task.dueDate) : toLocalYYYYMMDD(new Date())
  const margin = 8
  const rect = dueDateBtnEl.value.getBoundingClientRect()
  const dropdownW = 210
  const estimatedH = 210
  let left = rect.left
  left = Math.min(Math.max(margin, left), window.innerWidth - dropdownW - margin)
  let top = rect.bottom + 4
  if (top + estimatedH > window.innerHeight - margin) top = Math.max(margin, rect.top - estimatedH - 4)
  datePickerPos.value = { top, left }
  datePickerOpen.value = true
}

function applyDate(isoOrDate) {
  const iso = isoOrDate instanceof Date ? isoOrDate.toISOString() : new Date(isoOrDate).toISOString()
  tasksStore.rescheduleTask(props.task.id, iso)
  datePickerOpen.value = false
}

function clearDueDate() {
  tasksStore.rescheduleTask(props.task.id, null)
  datePickerOpen.value = false
}

function applyCustomDate() {
  if (!customDate.value) return
  applyDate(customDate.value)
}

const DATE_PRESETS = [
  { label: 'Сегодня', days: 0 },
  { label: 'Завтра', days: 1 },
  { label: 'Через 3 дня', days: 3 },
  { label: 'Через неделю', days: 7 },
]

const PRIORITY_COLOR = { low: '#9aa3b2', medium: '#4f7cff', high: '#e8a13a', urgent: '#e5484d' }
const PRIORITY_LABEL = { low: 'Низкий', medium: 'Средний', high: 'Высокий', urgent: 'Срочный' }
const PRIORITIES = ['low', 'medium', 'high', 'urgent']

// --- Быстрый выбор приоритета ---
const priorityPickerOpen = ref(false)
const priorityBadgeBtnEl = ref(null)
const priorityPickerEl = ref(null)
const priorityPickerPos = ref({ top: 0, left: 0 })
useClickOutside(priorityPickerEl, () => { priorityPickerOpen.value = false })

function openPriorityPicker(e) {
  if (!canEditThisTask.value) return
  e.stopPropagation()
  if (priorityPickerOpen.value) { priorityPickerOpen.value = false; return }
  const margin = 8
  const rect = priorityBadgeBtnEl.value.getBoundingClientRect()
  const dropdownW = 160
  const estimatedH = 4 * 36 + 12
  let left = rect.left
  left = Math.min(Math.max(margin, left), window.innerWidth - dropdownW - margin)
  let top = rect.bottom + 4
  if (top + estimatedH > window.innerHeight - margin) top = Math.max(margin, rect.top - estimatedH - 4)
  priorityPickerPos.value = { top, left }
  priorityPickerOpen.value = true
}

function applyPriority(priority) {
  tasksStore.updateTaskField(props.task.id, 'priority', priority)
  priorityPickerOpen.value = false
}

const rowAccentColor = computed(() => {
  if (prefs.colorCode === 'priority') return PRIORITY_COLOR[props.task.priority]
  if (prefs.colorCode === 'list') return list.value?.color
  if (prefs.colorCode === 'overdue') return overdue.value ? '#e5484d' : 'transparent'
  if (prefs.colorCode === 'assignee') return assignee.value ? '#4f7cff' : 'transparent'
  return 'transparent'
})

function toggleComplete() {
  if (!canToggleStatus.value) return
  if (isDone.value) tasksStore.reopenTask(props.task.id)
  else tasksStore.completeTask(props.task.id)
}

function snooze() {
  const d = new Date(props.task.dueDate || new Date())
  d.setDate(d.getDate() + 1)
  tasksStore.rescheduleTask(props.task.id, d.toISOString())
}

function startEditTitle() {
  titleDraft.value = props.task.title
  editingTitle.value = true
  nextTick(() => titleInputEl.value?.focus())
}

function commitTitle() {
  editingTitle.value = false
  const trimmed = titleDraft.value.trim()
  if (trimmed && trimmed !== props.task.title) tasksStore.updateTaskField(props.task.id, 'title', trimmed)
}

function cancelEditTitle() {
  editingTitle.value = false
  titleDraft.value = props.task.title
}

function startAddSubtask() {
  addingSubtask.value = true
  expanded.value = true
  subtaskDraft.value = ''
  nextTick(() => subtaskInputEl.value?.focus())
}

async function commitSubtask(keepOpen = false) {
  const title = subtaskDraft.value.trim()
  if (title) {
    await tasksStore.createTask({
      listId: props.task.listId, parentTaskId: props.task.id, title,
      priority: props.task.priority, assigneeId: props.task.assigneeId,
    })
  }
  subtaskDraft.value = ''
  if (keepOpen && title) nextTick(() => subtaskInputEl.value?.focus())
  else addingSubtask.value = false
}

function cancelAddSubtask() {
  addingSubtask.value = false
  subtaskDraft.value = ''
}

async function toggleChecklistExpand() {
  checklistExpanded.value = !checklistExpanded.value
  if (checklistExpanded.value && !tasksStore.checklistByTask[props.task.id]) {
    await tasksStore.loadChecklist(props.task.id)
  }
  if (checklistExpanded.value) nextTick(() => inlineChecklistInputEl.value?.focus())
}

function toggleChecklistDone(itemId) { tasksStore.toggleChecklistItem(props.task.id, itemId) }

async function addInlineChecklistItem() {
  const title = newInlineChecklistTitle.value.trim()
  if (!title) return
  await tasksStore.addChecklistItem(props.task.id, title)
  newInlineChecklistTitle.value = ''
  nextTick(() => inlineChecklistInputEl.value?.focus())
}

function removeInlineChecklistItem(itemId) { tasksStore.removeChecklistItem(props.task.id, itemId) }

function openContextMenu(e) {
  e.preventDefault()
  contextMenu.value = { x: e.clientX, y: e.clientY }
}

function closeContextMenu() { contextMenu.value = null }
</script>

<template>
  <div class="task-row-wrapper">
    <div
      class="task-row"
      :class="[`density-${prefs.density}`, { done: isDone, overdue: overdue && prefs.highlightOverdue, 'bubble-overdue': bubbleMode && overdue, 'bubble-no-due': bubbleMode && !task.dueDate && !isDone }]"
      :style="{ paddingLeft: `${8 + depth * 22}px`, borderLeftColor: rowAccentColor, borderLeftWidth: rowAccentColor !== 'transparent' ? '3px' : '0' }"
      @contextmenu="openContextMenu"
    >
      <button v-if="children.length" class="expand-btn" @click="expanded = !expanded">
        <AppIcon :name="expanded ? 'chevronDown' : 'chevronRight'" :size="12" />
      </button>
      <span v-else class="expand-spacer" />

      <input
        type="checkbox" :checked="isDone" class="task-checkbox"
        :disabled="!canToggleStatus"
        :title="canToggleStatus ? '' : permissionReason"
        @change="toggleComplete"
      />

      <div class="task-main">
        <input
          v-if="editingTitle"
          ref="titleInputEl"
          v-model="titleDraft"
          class="title-edit-input"
          @blur="commitTitle"
          @keyup.enter="commitTitle"
          @keyup.escape="cancelEditTitle"
        />
        <span v-else class="task-title" :class="{ 'wrap-title': prefs.wrapLongTitles, 'truncate-title': !prefs.wrapLongTitles }" @click="emit('open', task)" @dblclick.stop="startEditTitle">
          <span v-if="task.pinned" class="pin-icon"><AppIcon name="pin" :size="12" /></span>
          {{ task.title }}
          <span v-if="prefs.showSubtaskCount && children.length" class="mini-count"><AppIcon name="link" :size="11" />{{ children.length }}</span>
          <span
            v-if="prefs.showChecklistProgress && (checklistCount?.length || checklistExpanded)"
            class="mini-count mini-count-clickable"
            @click.stop="toggleChecklistExpand"
          >
            <AppIcon name="checklist" :size="11" />{{ checklistCount?.filter(i => i.done).length || 0 }}/{{ checklistCount?.length || 0 }}
            <AppIcon :name="checklistExpanded ? 'chevronDown' : 'chevronRight'" :size="10" />
          </span>
          <span v-if="prefs.showCommentsCount && commentsCount" class="mini-count"><AppIcon name="message" :size="11" />{{ commentsCount }}</span>
        </span>
        <div v-if="!editingTitle" class="task-meta">
          <span v-if="prefs.showCreatedDate && task.createdAt" class="date-meta" :title="`Создано: ${formatDate(task.createdAt)}`">
            <AppIcon name="plus" :size="11" /> создано {{ relativeTimeAgo(task.createdAt) }}
          </span>

          <span
            v-if="prefs.showDueDate"
            ref="dueDateBtnEl"
            class="due-date" :class="{ 'due-overdue': overdue, 'due-date-clickable': canEditThisTask }"
            :title="canEditThisTask ? 'Нажмите, чтобы изменить срок' : 'Крайний срок'"
            @click.stop="openDatePicker"
          >
            <AppIcon name="calendar" :size="11" />
            {{ task.dueDate ? relativeDay(task.dueDate) : 'срок не установлен' }}
            <AppIcon v-if="canEditThisTask" name="chevronDown" :size="9" class="due-date-caret" />
          </span>

          <span
            ref="priorityBadgeBtnEl"
            :class="['badge', `badge-${task.priority}`, { 'priority-badge-clickable': canEditThisTask }]"
            :title="canEditThisTask ? 'Нажмите, чтобы изменить приоритет' : 'Приоритет'"
            @click.stop="openPriorityPicker"
          >
            {{ PRIORITY_LABEL[task.priority] }}
            <AppIcon v-if="canEditThisTask" name="chevronDown" :size="9" class="due-date-caret" />
          </span>

          <button
            v-if="occurrenceBadgeLabel"
            class="tag occurrence-badge"
            :title="'Открыть встречу: ' + occurrenceBadgeLabel"
            @click.stop="openOccurrenceMeeting"
          ><AppIcon name="repeat" :size="11" /> {{ occurrenceBadgeLabel }}</button>
          <span v-if="prefs.showCompletedDate && task.completedAt" class="date-meta date-meta-done" :title="`Выполнено: ${formatDate(task.completedAt)}`">
            <AppIcon name="check" :size="11" /> {{ formatDate(task.completedAt) }}
          </span>
          <span v-if="prefs.showLastUpdatedDate && task.updatedAt" class="date-meta" :title="`Последнее изменение: ${formatDate(task.updatedAt)}`">
            <AppIcon name="edit" :size="11" /> {{ relativeTimeAgo(task.updatedAt) }}
          </span>
          <span v-if="prefs.showListBadgeInMyTasks && list" class="tag list-badge" :style="{ background: list.color + '22', color: list.color }">{{ list.title }}</span>
          <span v-if="prefs.showTags && task.tags?.length" v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
          <span v-if="prefs.showWatchers && task.watcherIds?.length" class="tag watcher-tag"><AppIcon name="eye" :size="11" /> {{ task.watcherIds.length }}</span>
        </div>
      </div>

      <div v-if="prefs.showAssigneeAvatar" class="task-assignee" :class="{ 'task-assignee-detailed': prefs.detailedAssigneeView }">
        <button
          ref="avatarBtnEl"
          class="avatar-btn" :class="{ 'avatar-btn-disabled': !canEditThisTask, 'avatar-btn-detailed': prefs.detailedAssigneeView }"
          :title="canEditThisTask ? (assignee ? `Исполнитель: ${assignee.name} — нажмите, чтобы изменить` : 'Назначить исполнителя') : assignee?.name"
          @click.stop="toggleAssignPicker"
        >
          <span v-if="assignee" class="avatar" :class="{ 'avatar-compact': prefs.compactAvatars && !prefs.detailedAssigneeView }" :style="{ background: getAvatarColor(assignee.name) }">{{ getInitials(assignee.name) }}</span>
          <span v-else class="avatar avatar-empty" :class="{ 'avatar-compact': prefs.compactAvatars && !prefs.detailedAssigneeView }">+</span>
          <span v-if="prefs.detailedAssigneeView" class="assignee-name">{{ assignee ? assignee.name : 'Без исполнителя' }}</span>
        </button>
      </div>

      <div class="task-quick-actions">
        <button v-if="canEditThisTask" class="btn btn-ghost btn-sm" title="Добавить подзадачу" @click.stop="startAddSubtask"><AppIcon name="plus" :size="13" /></button>
        <button v-if="canEditThisTask" class="btn btn-ghost btn-sm" title="Добавить чек-лист" @click.stop="toggleChecklistExpand"><AppIcon name="checklist" :size="13" /></button>
        <button v-if="canEditThisTask" class="btn btn-ghost btn-sm" title="Отложить на день" @click.stop="snooze"><AppIcon name="alarm" :size="13" /></button>
      </div>
    </div>

    <!-- Quick due-date picker -->
    <Teleport to="body">
      <div
        v-if="datePickerOpen"
        ref="datePickerEl"
        class="date-picker-dropdown card"
        :style="{ top: `${datePickerPos.top}px`, left: `${datePickerPos.left}px` }"
        @click.stop
      >
        <div class="date-picker-label">Срок выполнения</div>
        <div class="date-presets">
          <button
            v-for="p in DATE_PRESETS" :key="p.days"
            class="date-preset-btn"
            @click="applyDate(offsetDate(p.days))"
          >{{ p.label }}</button>
        </div>
        <div class="date-picker-custom">
          <input
            v-model="customDate"
            type="date"
            class="date-input"
            @change="applyCustomDate"
          />
        </div>
        <button class="date-clear-btn" @click="clearDueDate">
          <AppIcon name="close" :size="11" /> Без срока
        </button>
      </div>
    </Teleport>

    <!-- Quick priority picker -->
    <Teleport to="body">
      <div
        v-if="priorityPickerOpen"
        ref="priorityPickerEl"
        class="priority-picker-dropdown card"
        :style="{ top: `${priorityPickerPos.top}px`, left: `${priorityPickerPos.left}px` }"
        @click.stop
      >
        <div class="date-picker-label">Приоритет</div>
        <button
          v-for="p in PRIORITIES" :key="p"
          class="priority-option"
          :class="{ active: task.priority === p }"
          @click="applyPriority(p)"
        >
          <span class="priority-dot" :style="{ background: PRIORITY_COLOR[p] }"></span>
          {{ PRIORITY_LABEL[p] }}
          <span v-if="task.priority === p" class="assign-check"><AppIcon name="check" :size="12" /></span>
        </button>
      </div>
    </Teleport>

    <!-- Quick assign picker -->
    <Teleport to="body">
      <div
        v-if="assignPickerOpen"
        ref="dropdownEl"
        class="assign-dropdown card scroll-thin"
        :style="{ top: `${dropdownPos.top}px`, left: `${dropdownPos.left}px` }"
        @click.stop
      >
        <div class="assign-dropdown-label">Назначить исполнителя</div>
        <button
          v-for="u in assignableUsers" :key="u.id"
          class="assign-option" :class="{ active: task.assigneeId === u.id }"
          @click="quickAssign(u.id)"
        >
          <span class="assign-avatar" :style="{ background: getAvatarColor(u.name) }">{{ getInitials(u.name) }}</span>
          {{ u.name }}
          <span v-if="task.assigneeId === u.id" class="assign-check"><AppIcon name="check" :size="12" /></span>
        </button>
        <button class="assign-option" @click="quickAssign(null)">
          <span class="assign-avatar assign-avatar-empty">—</span> Без исполнителя
        </button>
      </div>
    </Teleport>

    <div v-if="checklistExpanded" class="inline-checklist" :style="{ paddingLeft: `${36 + depth * 22}px` }">
      <div v-for="item in checklistItems" :key="item.id" class="inline-checklist-item">
        <input type="checkbox" :checked="item.done" @change="toggleChecklistDone(item.id)" />
        <span :class="{ done: item.done }">{{ item.title }}</span>
        <button class="btn btn-ghost btn-sm" @click="removeInlineChecklistItem(item.id)"><AppIcon name="close" :size="11" /></button>
      </div>
      <div class="inline-checklist-add">
        <input
          ref="inlineChecklistInputEl"
          v-model="newInlineChecklistTitle"
          placeholder="Новый пункт чек-листа"
          @keyup.enter="addInlineChecklistItem"
        />
        <button class="btn btn-sm" @click="addInlineChecklistItem">Добавить</button>
      </div>
    </div>

    <div v-if="expanded && (children.length || addingSubtask)" class="task-children">
      <TaskRow v-for="child in children" :key="child.id" :task="child" :depth="depth + 1" :bubble-mode="bubbleMode" @open="emit('open', $event)" />
      <div v-if="addingSubtask" class="subtask-add-row" :style="{ paddingLeft: `${28 + (depth + 1) * 22}px` }">
        <span class="subtask-add-icon"><AppIcon name="link" :size="11" /></span>
        <input
          ref="subtaskInputEl"
          v-model="subtaskDraft"
          class="subtask-add-input"
          placeholder="Название подзадачи, Enter — добавить и продолжить"
          @keyup.enter="commitSubtask(true)"
          @keyup.escape="cancelAddSubtask"
          @blur="commitSubtask(false)"
        />
      </div>
    </div>

    <TaskContextMenu
      v-if="contextMenu"
      :task="task"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :checklist-expanded="checklistExpanded"
      @close="closeContextMenu"
      @open-detail="emit('open', $event)"
      @add-subtask="startAddSubtask"
      @rename="startEditTitle"
      @toggle-checklist="toggleChecklistExpand"
    />
  </div>
</template>

<style scoped>
.task-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border-bottom: 1px solid var(--color-border); background: var(--color-surface);
  border-left: 0 solid transparent;
}
.task-row.density-compact { padding-top: 4px; padding-bottom: 4px; }
.task-row.density-comfortable { padding-top: 8px; padding-bottom: 8px; }
.task-row.density-spacious { padding-top: 14px; padding-bottom: 14px; }
.task-row:hover { background: #fafbfe; }
.task-row.done .task-title { color: var(--color-text-muted); text-decoration: line-through; }
.task-row.overdue .due-date { color: var(--color-danger); font-weight: 600; }
.task-row.bubble-overdue { background: rgba(229, 72, 77, 0.07); }
.task-row.bubble-no-due { box-shadow: inset 3px 0 0 var(--color-text-muted); }
.expand-btn { border: none; background: none; cursor: pointer; width: 16px; color: var(--color-text-muted); display: flex; align-items: center; justify-content: center; }
.expand-spacer { width: 16px; display: inline-block; }
.task-checkbox { accent-color: var(--color-primary); cursor: pointer; }
.task-checkbox:disabled { cursor: not-allowed; opacity: 0.45; }
.task-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.task-title { font-size: 13.5px; font-weight: 500; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; cursor: pointer; }
.truncate-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wrap-title { white-space: normal; }
.title-edit-input {
  font-size: 13.5px; font-weight: 500; border: 1px solid var(--color-primary); border-radius: 5px;
  padding: 3px 6px; width: 100%; outline: none;
}
.pin-icon { display: flex; color: #c67d16; }
.mini-count { font-size: 11px; color: var(--color-text-muted); display: inline-flex; align-items: center; gap: 3px; }
.mini-count-clickable { cursor: pointer; padding: 1px 5px; border-radius: 4px; }
.mini-count-clickable:hover { background: #eef1f7; color: var(--color-text); }
.task-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.due-date {
  font-size: 11.5px; color: var(--color-text-muted);
  display: inline-flex; align-items: center; gap: 3px;
}
.due-date-clickable {
  cursor: pointer; border-radius: 5px; padding: 1px 5px; margin: -1px -5px;
  transition: background 120ms;
}
.due-date-clickable:hover { background: #eef1f7; color: var(--color-text); }
.due-date-caret { opacity: 0.5; }
.due-overdue { color: var(--color-danger) !important; font-weight: 600; }
.date-meta { font-size: 11px; color: var(--color-text-muted); opacity: 0.75; white-space: nowrap; display: inline-flex; align-items: center; gap: 3px; }
.date-meta-done { color: #1e9e4d; opacity: 0.85; }
.list-badge { font-weight: 600; }
.watcher-tag { background: #f4f0ff; color: #7c5cd6; display: inline-flex; align-items: center; gap: 3px; }
.occurrence-badge {
  background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; border: none; cursor: pointer;
  display: inline-flex; align-items: center; gap: 4px; font-size: 11px; padding: 2px 8px; border-radius: 999px;
}
.occurrence-badge:hover { background: #dfe6ff; }
.task-assignee { width: 26px; flex-shrink: 0; position: relative; }
.task-assignee-detailed { width: auto; max-width: 180px; flex-shrink: 0; }
.avatar-btn { border: none; background: none; padding: 0; cursor: pointer; display: flex; border-radius: 50%; }
.avatar-btn-disabled { cursor: default; }
.avatar-btn-detailed {
  border-radius: 999px; align-items: center; gap: 6px; padding: 3px 10px 3px 3px;
  background: #eef1f7; max-width: 100%;
}
.avatar-btn-detailed:hover { background: #e4e8f2; }
.avatar-btn-detailed.avatar-btn-disabled:hover { background: #eef1f7; }
.assignee-name { font-size: 12px; font-weight: 600; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.avatar {
  width: 24px; height: 24px; border-radius: 50%; background: var(--color-primary);
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; flex-shrink: 0;
}
.avatar-empty { background: #d9dde8; color: var(--color-text-muted); font-weight: 700; }
.avatar-compact { width: 18px; height: 18px; font-size: 8px; }

/* --- Date picker dropdown --- */
.date-picker-dropdown {
  position: fixed; z-index: 500; width: 210px;
  padding: 8px; display: flex; flex-direction: column; gap: 6px;
  box-shadow: 0 4px 12px rgba(20, 24, 38, 0.08), 0 16px 40px rgba(20, 24, 38, 0.16);
}
.date-picker-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--color-text-muted); padding: 2px 4px 4px;
}
.date-presets { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
.date-preset-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 7px;
  padding: 6px 8px; font-size: 12px; cursor: pointer; color: var(--color-text); text-align: center;
}
.date-preset-btn:hover { background: #eef1f7; border-color: var(--color-primary); color: var(--color-primary); }
.date-picker-custom { display: flex; }
.date-input {
  flex: 1; border: 1px solid var(--color-border); border-radius: 7px;
  padding: 6px 8px; font-size: 12.5px; outline: none; cursor: pointer;
}
.date-input:focus { border-color: var(--color-primary); }
.date-clear-btn {
  display: flex; align-items: center; justify-content: center; gap: 5px;
  border: none; background: none; padding: 5px 8px; border-radius: 7px;
  font-size: 12px; cursor: pointer; color: var(--color-text-muted);
}
.date-clear-btn:hover { background: #ffeaea; color: var(--color-danger); }

/* --- Priority picker dropdown --- */
.priority-picker-dropdown {
  position: fixed; z-index: 500; width: 160px;
  padding: 6px; display: flex; flex-direction: column; gap: 1px;
  box-shadow: 0 4px 12px rgba(20, 24, 38, 0.08), 0 16px 40px rgba(20, 24, 38, 0.16);
}
.priority-option {
  display: flex; align-items: center; gap: 8px; width: 100%; text-align: left;
  border: none; background: none; padding: 7px 8px; border-radius: 7px;
  font-size: 12.5px; cursor: pointer; color: var(--color-text);
}
.priority-option:hover { background: #eef1f7; }
.priority-option.active { background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; }
.priority-dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}
.priority-badge-clickable {
  cursor: pointer;
  transition: opacity 120ms;
}
.priority-badge-clickable:hover { opacity: 0.75; }

/* --- Assign dropdown --- */
.assign-dropdown {
  position: fixed; z-index: 500; min-width: 220px;
  padding: 6px; display: flex; flex-direction: column; gap: 1px; max-height: 280px; overflow-y: auto;
  box-shadow: 0 4px 12px rgba(20, 24, 38, 0.08), 0 16px 40px rgba(20, 24, 38, 0.16);
}
.assign-dropdown-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); padding: 4px 8px 6px; }
.assign-option {
  display: flex; align-items: center; gap: 8px; width: 100%; text-align: left; border: none; background: none;
  padding: 7px 8px; border-radius: 7px; font-size: 12.5px; cursor: pointer; color: var(--color-text);
}
.assign-option:hover { background: #eef1f7; }
.assign-option.active { background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; }
.assign-avatar {
  width: 22px; height: 22px; border-radius: 50%; background: #b7bfd1; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 9.5px; font-weight: 700;
}
.assign-avatar-empty { background: #d9dde8; color: var(--color-text-muted); }
.assign-check { margin-left: auto; color: var(--color-primary); font-weight: 700; display: flex; }

.task-quick-actions { display: flex; gap: 2px; opacity: 1; }
.task-children { border-left: 1px solid var(--color-border); margin-left: 20px; }
.subtask-add-row { display: flex; align-items: center; gap: 6px; padding: 6px 10px; background: #fafbfe; }
.subtask-add-icon { color: var(--color-text-muted); display: flex; }
.subtask-add-input {
  flex: 1; border: 1px dashed var(--color-border); border-radius: 6px; padding: 5px 8px;
  font-size: 13px; outline: none; background: var(--color-surface);
}
.subtask-add-input:focus { border-color: var(--color-primary); border-style: solid; }
.inline-checklist { padding: 6px 10px 8px; background: #fbfcfe; border-bottom: 1px solid var(--color-border); }
.inline-checklist-item { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 12.5px; }
.inline-checklist-item span { flex: 1; }
.inline-checklist-item span.done { text-decoration: line-through; color: var(--color-text-muted); }
.inline-checklist-add { display: flex; gap: 6px; margin-top: 4px; }
.inline-checklist-add input { flex: 1; border: 1px dashed var(--color-border); border-radius: 6px; padding: 4px 8px; font-size: 12.5px; outline: none; }
.inline-checklist-add input:focus { border-color: var(--color-primary); border-style: solid; }
</style>
