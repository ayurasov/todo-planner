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

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const meetingsStore = useMeetingsStore()
const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const isAdmin = useIsAdmin()

const editing = ref(false)
const editDraft = ref({ title: '', date: '', time: '', description: '' })

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
</style>
