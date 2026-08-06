<script setup>
import { ref, computed, nextTick } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { useListsStore } from '../../stores/listsStore'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { relativeDay, isOverdue } from '../../utils/formatters'
import { useTaskPermissions } from '../../composables/usePermissions'
import PriorityBadge from './PriorityBadge.vue'
import TaskContextMenu from './TaskContextMenu.vue'

const props = defineProps({
  task: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  bubbleMode: { type: Boolean, default: false },
})
const emit = defineEmits(['open'])

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const prefs = usePreferencesStore()

const expanded = ref(true)
const editingTitle = ref(false)
const titleDraft = ref(props.task.title)
const titleInputEl = ref(null)

const addingSubtask = ref(false)
const subtaskDraft = ref('')
const subtaskInputEl = ref(null)

const contextMenu = ref(null) // { x, y }
const checklistExpanded = ref(false)
const newInlineChecklistTitle = ref('')
const inlineChecklistInputEl = ref(null)

const children = computed(() => tasksStore.childrenOf(props.task.id))
const assignee = computed(() => usersStore.byId(props.task.assigneeId))
const list = computed(() => listsStore.byId(props.task.listId))
const overdue = computed(() => isOverdue(props.task.dueDate, props.task.status))
const isDone = computed(() => props.task.status === 'done')

const checklistItems = computed(() => tasksStore.checklistByTask[props.task.id])
const checklistCount = checklistItems
const commentsCount = computed(() => tasksStore.commentsByTask[props.task.id]?.length)

const { canEditThisTask, canToggleStatus, reason: permissionReason } = useTaskPermissions(() => props.task)

const PRIORITY_COLOR = { low: '#9aa3b2', medium: '#4f7cff', high: '#e8a13a', urgent: '#e5484d' }

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

function togglePin() {
  tasksStore.togglePin(props.task.id)
}

function startEditTitle() {
  titleDraft.value = props.task.title
  editingTitle.value = true
  nextTick(() => titleInputEl.value?.focus())
}

function commitTitle() {
  editingTitle.value = false
  const trimmed = titleDraft.value.trim()
  if (trimmed && trimmed !== props.task.title) {
    tasksStore.updateTaskField(props.task.id, 'title', trimmed)
  }
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
      listId: props.task.listId,
      parentTaskId: props.task.id,
      title,
      priority: props.task.priority,
      assigneeId: props.task.assigneeId,
    })
  }
  subtaskDraft.value = ''
  if (keepOpen && title) {
    nextTick(() => subtaskInputEl.value?.focus())
  } else {
    addingSubtask.value = false
  }
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
}

function toggleChecklistDone(itemId) {
  tasksStore.toggleChecklistItem(props.task.id, itemId)
}

async function addInlineChecklistItem() {
  const title = newInlineChecklistTitle.value.trim()
  if (!title) return
  await tasksStore.addChecklistItem(props.task.id, title)
  newInlineChecklistTitle.value = ''
  nextTick(() => inlineChecklistInputEl.value?.focus())
}

function removeInlineChecklistItem(itemId) {
  tasksStore.removeChecklistItem(props.task.id, itemId)
}

function openContextMenu(e) {
  e.preventDefault()
  contextMenu.value = { x: e.clientX, y: e.clientY }
}

function closeContextMenu() {
  contextMenu.value = null
}
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
        {{ expanded ? '▾' : '▸' }}
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
          <span v-if="task.pinned" class="pin-icon">📌</span>
          {{ task.title }}
          <span v-if="prefs.showSubtaskCount && children.length" class="mini-count">🔗{{ children.length }}</span>
          <span
            v-if="prefs.showChecklistProgress && (checklistCount?.length || checklistExpanded)"
            class="mini-count mini-count-clickable"
            @click.stop="toggleChecklistExpand"
          >
            ☑{{ checklistCount?.filter(i => i.done).length || 0 }}/{{ checklistCount?.length || 0 }} {{ checklistExpanded ? '▾' : '▸' }}
          </span>
          <span v-if="prefs.showCommentsCount && commentsCount" class="mini-count">💬{{ commentsCount }}</span>
        </span>
        <div class="task-meta" v-if="!editingTitle">
          <PriorityBadge :priority="task.priority" />
          <span v-if="prefs.showDueDate && task.dueDate" class="due-date" :class="{ 'due-overdue': overdue }">{{ relativeDay(task.dueDate) }}</span>
          <span v-if="prefs.showListBadgeInMyTasks && list" class="tag list-badge" :style="{ background: list.color + '22', color: list.color }">{{ list.title }}</span>
          <span v-if="prefs.showTags && task.tags?.length" class="tag" v-for="tag in task.tags" :key="tag">{{ tag }}</span>
          <span v-if="prefs.showWatchers && task.watcherIds?.length" class="tag watcher-tag">👁 {{ task.watcherIds.length }}</span>
          <span v-if="prefs.showScoreDebug && task.__score !== undefined" class="tag score-tag">score {{ task.__score.toFixed(2) }}</span>
        </div>
      </div>

      <div v-if="prefs.showAssigneeAvatar" class="task-assignee" :title="assignee?.name">
        <span v-if="assignee" class="avatar" :class="{ 'avatar-compact': prefs.compactAvatars }">{{ assignee.name.charAt(0) }}</span>
      </div>

      <div class="task-quick-actions">
        <button v-if="canEditThisTask" class="btn btn-ghost btn-sm" title="Добавить подзадачу" @click.stop="startAddSubtask">＋</button>
        <button v-if="canEditThisTask" class="btn btn-ghost btn-sm" title="Закрепить" @click.stop="togglePin">📌</button>
        <button v-if="canEditThisTask" class="btn btn-ghost btn-sm" title="Отложить на день" @click.stop="snooze">⏰</button>
        <button class="btn btn-ghost btn-sm" title="Ещё" @click.stop="openContextMenu($event)">⋯</button>
      </div>
    </div>

    <div v-if="checklistExpanded" class="inline-checklist" :style="{ paddingLeft: `${36 + depth * 22}px` }">
      <div v-for="item in checklistItems" :key="item.id" class="inline-checklist-item">
        <input type="checkbox" :checked="item.done" @change="toggleChecklistDone(item.id)" />
        <span :class="{ done: item.done }">{{ item.title }}</span>
        <button class="btn btn-ghost btn-sm" @click="removeInlineChecklistItem(item.id)">✕</button>
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
        <span class="subtask-add-icon">↳</span>
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
      @close="closeContextMenu"
      @open-detail="emit('open', $event)"
      @add-subtask="startAddSubtask"
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
.expand-btn { border: none; background: none; cursor: pointer; width: 16px; color: var(--color-text-muted); font-size: 12px; }
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
.mini-count { font-size: 11px; color: var(--color-text-muted); }
.mini-count-clickable { cursor: pointer; padding: 1px 5px; border-radius: 4px; }
.mini-count-clickable:hover { background: #eef1f7; color: var(--color-text); }
.task-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.due-date { font-size: 11.5px; color: var(--color-text-muted); }
.list-badge { font-weight: 600; }
.watcher-tag, .score-tag { background: #f4f0ff; color: #7c5cd6; }
.task-assignee { width: 26px; flex-shrink: 0; }
.avatar {
  width: 24px; height: 24px; border-radius: 50%; background: var(--color-primary);
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600;
}
.avatar-compact { width: 18px; height: 18px; font-size: 9px; }
.task-quick-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.15s; }
.task-row:hover .task-quick-actions { opacity: 1; }
.task-children { border-left: 1px solid var(--color-border); margin-left: 20px; }
.subtask-add-row { display: flex; align-items: center; gap: 6px; padding: 6px 10px; background: #fafbfe; }
.subtask-add-icon { color: var(--color-text-muted); font-size: 12px; }
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
