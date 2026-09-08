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

const props = defineProps({ task: { type: Object, required: true }, depth: { type: Number, default: 0 }, bubbleMode: { type: Boolean, default: false } })
const emit = defineEmits(['open'])
const router = useRouter(); const tasksStore = useTasksStore(); const usersStore = useUsersStore(); const listsStore = useListsStore(); const meetingsStore = useMeetingsStore(); const prefs = usePreferencesStore()
const expanded = ref(true); const editingTitle = ref(false); const titleDraft = ref(props.task.title); const titleInputEl = ref(null); const addingSubtask = ref(false); const subtaskDraft = ref(''); const subtaskInputEl = ref(null); const contextMenu = ref(null); const checklistExpanded = ref(false); const newInlineChecklistTitle = ref(''); const inlineChecklistInputEl = ref(null)
const children = computed(() => tasksStore.childrenOf(props.task.id)); const assignee = computed(() => usersStore.byId(props.task.assigneeId)); const list = computed(() => listsStore.byId(props.task.listId)); const overdue = computed(() => isOverdue(props.task.dueDate, props.task.status)); const isDone = computed(() => props.task.status === 'done')
const occurrenceInfo = computed(() => (props.task.occurrenceId ? meetingsStore.occurrenceById(props.task.occurrenceId) : null))
const occurrenceBadgeLabel = computed(() => {
  if (props.task.occurrenceTitle) return props.task.occurrenceTitle
  if (!occurrenceInfo.value) return null
  return `${occurrenceInfo.value.meeting.title} · ${formatDateTime(occurrenceInfo.value.occurrence.date)}`
})
function openOccurrenceMeeting() { if (!occurrenceInfo.value) return; const meetingId = occurrenceInfo.value.meeting.id; const occurrenceId = occurrenceInfo.value.occurrence.id; const anchor = `occurrence-${occurrenceId}`; if (router.currentRoute.value.path === `/meetings/${meetingId}`) document.getElementById(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'center' }); else router.push({ path: `/meetings/${meetingId}`, hash: `#${anchor}` }) }
const checklistItems = computed(() => tasksStore.checklistByTask[props.task.id]); const checklistCount = checklistItems; const commentsCount = computed(() => tasksStore.commentsByTask[props.task.id]?.length); const { canEditThisTask, canToggleStatus, reason: permissionReason } = useTaskPermissions(() => props.task)
</script>

<template>
  <div class="task-row-wrapper"><div class="task-row" :class="[`density-${prefs.density}`, { done: isDone, overdue: overdue && prefs.highlightOverdue, 'bubble-overdue': bubbleMode && overdue }]" @contextmenu="openContextMenu"><input type="checkbox" :checked="isDone" class="task-checkbox" :disabled="!canToggleStatus" :title="canToggleStatus ? '' : permissionReason" /><div class="task-main"><span class="task-title" @click="emit('open', task)">{{ task.title }}</span><div class="task-meta"><span v-if="occurrenceBadgeLabel && occurrenceInfo" class="tag occurrence-badge" @click.stop="openOccurrenceMeeting">{{ occurrenceBadgeLabel }}</span><span v-else-if="occurrenceBadgeLabel" class="tag occurrence-badge occurrence-badge-static">{{ occurrenceBadgeLabel }}</span></div></div></div></div>
</template>

<style scoped>
.task-row { display:flex; align-items:center; gap:8px; padding:8px 10px; border-bottom:1px solid var(--color-border); background:var(--color-surface); }
.task-main { flex:1; min-width:0; }.task-title { font-size:13.5px; font-weight:500; cursor:pointer; }.task-meta { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }.occurrence-badge { background:#eef2ff; color:var(--color-primary-dark); font-weight:600; display:inline-flex; align-items:center; gap:4px; font-size:11px; padding:2px 8px; border-radius:999px; }.occurrence-badge-static { cursor:default; }.occurrence-badge:not(.occurrence-badge-static) { cursor:pointer; }.occurrence-badge:not(.occurrence-badge-static):hover { background:#dfe6ff; }
</style>
