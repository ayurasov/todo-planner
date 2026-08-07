<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useClickOutside } from '../../composables/useClickOutside'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { useTaskPermissions } from '../../composables/usePermissions'
import { useAssignableUsers } from '../../composables/useAssignableUsers'
import { TaskPriority, PRIORITY_LABEL } from '../../domain/entities/enums'
import AppIcon from '../common/AppIcon.vue'
import ConfirmModal from '../common/ConfirmModal.vue'

const props = defineProps({
  task: { type: Object, required: true },
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  checklistExpanded: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'open-detail', 'add-subtask', 'rename', 'toggle-checklist'])

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const prefs = usePreferencesStore()
const menuEl = ref(null)
const mounted = ref(false)
const measuredSize = ref({ w: 264, h: 0 })

// Подтверждение удаления вынесено в отдельное состояние — пока confirmDeleteOpen
// открыт, контекстное меню уже скрыто (close() вызван раньше), а клик вне области
// самого ConfirmModal (через @click.self) закрывает его без удаления.
const confirmDeleteOpen = ref(false)

useClickOutside(menuEl, () => emit('close'))
onMounted(() => {
  mounted.value = true
  nextTick(() => {
    if (menuEl.value) {
      const rect = menuEl.value.getBoundingClientRect()
      measuredSize.value = { w: rect.width || 264, h: rect.height || 0 }
    }
  })
})

const isDone = computed(() => props.task.status === 'done')
const isSubtask = computed(() => !!props.task.parentTaskId)
const { canEditThisTask, canToggleStatus, canDeleteThisTask } = useTaskPermissions(() => props.task)
const assignableUsers = useAssignableUsers(() => props.task)

const hasChecklist = computed(() => {
  const items = tasksStore.checklistByTask[props.task.id]
  return Array.isArray(items) && items.length > 0
})

const style = computed(() => {
  const margin = 8
  const menuW = measuredSize.value.w
  const menuH = measuredSize.value.h || Math.min(window.innerHeight - margin * 2, 520)
  const maxX = Math.max(margin, window.innerWidth - menuW - margin)
  const maxY = Math.max(margin, window.innerHeight - menuH - margin)
  return { left: `${Math.min(props.x, maxX)}px`, top: `${Math.max(margin, Math.min(props.y, maxY))}px` }
})

const PRIORITY_COLOR = { low: '#9aa3b2', medium: '#4f7cff', high: '#e8a13a', urgent: '#e5484d' }

function close() { emit('close') }

function toggleComplete() {
  if (!canToggleStatus.value) return
  if (isDone.value) tasksStore.reopenTask(props.task.id)
  else tasksStore.completeTask(props.task.id)
  close()
}

function addSubtask() {
  emit('add-subtask', props.task)
  close()
}

function rename() {
  emit('rename', props.task)
  close()
}

function toggleChecklist() {
  emit('toggle-checklist', props.task)
  close()
}

function togglePin() {
  tasksStore.togglePin(props.task.id)
  close()
}

function setPriority(p) {
  tasksStore.updateTaskField(props.task.id, 'priority', p)
  close()
}

function assign(userId) {
  tasksStore.assignTask(props.task.id, userId)
  close()
}

function reschedule(days) {
  const base = props.task.dueDate ? new Date(props.task.dueDate) : new Date()
  base.setDate(base.getDate() + days)
  tasksStore.rescheduleTask(props.task.id, base.toISOString())
  close()
}

function rescheduleToday() {
  tasksStore.rescheduleTask(props.task.id, new Date().toISOString())
  close()
}

function toggleStandalone() {
  tasksStore.updateTaskField(props.task.id, 'displayStandalone', !props.task.displayStandalone)
  close()
}

function duplicate() {
  tasksStore.createTask({
    listId: props.task.listId, parentTaskId: props.task.parentTaskId,
    title: `${props.task.title} (копия)`, priority: props.task.priority,
    assigneeId: props.task.assigneeId, dueDate: props.task.dueDate,
  })
  close()
}

// Раньше подтверждение шло через window.confirm() — теперь открываем
// ConfirmModal и держим меню видимым до явного решения пользователя.
function askRemove() {
  confirmDeleteOpen.value = true
}

function confirmRemove() {
  tasksStore.removeTask(props.task.id)
  confirmDeleteOpen.value = false
  close()
}

function cancelRemove() {
  confirmDeleteOpen.value = false
  close()
}

function openDetail() {
  emit('open-detail', props.task)
  close()
}

const currentAssignee = computed(() => usersStore.byId(props.task.assigneeId))
</script>

<template>
  <Teleport to="body">
    <Transition name="menu-pop">
      <div ref="menuEl" v-if="mounted" class="ctx-menu" :style="style" @click.stop @contextmenu.prevent>
        <div class="ctx-section">
          <button class="ctx-item" @click="openDetail">
            <span class="ctx-icon icon-neutral"><AppIcon name="detail" :size="13" /></span> Открыть детали
          </button>
          <button v-if="canToggleStatus" class="ctx-item ctx-item-primary" @click="toggleComplete">
            <span class="ctx-icon" :class="isDone ? 'icon-neutral' : 'icon-success'"><AppIcon :name="isDone ? 'undo' : 'check'" :size="13" /></span>
            {{ isDone ? 'Вернуть в работу' : 'Завершить' }}
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="rename">
            <span class="ctx-icon icon-neutral"><AppIcon name="edit" :size="13" /></span> Переименовать
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="addSubtask">
            <span class="ctx-icon icon-neutral"><AppIcon name="plus" :size="13" /></span> Добавить подзадачу
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="toggleChecklist">
            <span class="ctx-icon icon-neutral"><AppIcon name="checklist" :size="13" /></span>
            {{ hasChecklist ? (checklistExpanded ? 'Скрыть чек-лист' : 'Раскрыть чек-лист') : 'Добавить чек-лист' }}
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="togglePin">
            <span class="ctx-icon" :class="task.pinned ? 'icon-warning' : 'icon-neutral'"><AppIcon name="pin" :size="13" /></span>
            {{ task.pinned ? 'Открепить' : 'Закрепить' }}
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="duplicate">
            <span class="ctx-icon icon-neutral"><AppIcon name="copy" :size="13" /></span> Дублировать
          </button>
          <button v-if="canDeleteThisTask" class="ctx-item ctx-item-danger" @click="askRemove">
            <span class="ctx-icon icon-danger"><AppIcon name="trash" :size="13" /></span> Удалить
          </button>
          <button v-if="canEditThisTask && isSubtask" class="ctx-item" @click="toggleStandalone">
            <span class="ctx-icon icon-neutral"><AppIcon :name="task.displayStandalone ? 'standaloneOff' : 'standaloneOn'" :size="13" /></span>
            {{ task.displayStandalone ? 'Скрыть из общих списков' : 'Показывать отдельно' }}
          </button>
          <p v-if="!canEditThisTask" class="ctx-readonly-hint">Только просмотр — недостаточно прав для этой задачи</p>
        </div>

        <template v-if="canEditThisTask">
        <div class="ctx-divider" />

        <div class="ctx-section">
          <div class="ctx-label">Перенести</div>
          <div class="ctx-chip-row">
            <button class="ctx-chip" @click="rescheduleToday">Сегодня</button>
            <button class="ctx-chip" @click="reschedule(1)">Завтра</button>
            <button class="ctx-chip" @click="reschedule(7)">+Неделя</button>
          </div>
        </div>

        <div class="ctx-divider" />

        <div class="ctx-section">
          <div class="ctx-label">Приоритет</div>
          <div class="ctx-chip-row">
            <button
              v-for="p in Object.values(TaskPriority)" :key="p"
              class="ctx-chip ctx-chip-dot" :class="{ active: task.priority === p }"
              :style="task.priority === p ? { background: PRIORITY_COLOR[p], borderColor: PRIORITY_COLOR[p], color: '#fff' } : {}"
              @click="setPriority(p)"
            >
              <span class="dot" :style="{ background: task.priority === p ? '#fff' : PRIORITY_COLOR[p] }" />
              {{ PRIORITY_LABEL[p] }}
            </button>
          </div>
        </div>

        <div class="ctx-divider" />

        <div class="ctx-section">
          <div class="ctx-label">Назначить</div>
          <div class="ctx-scroll scroll-thin">
            <button
              v-for="u in assignableUsers" :key="u.id"
              class="ctx-item ctx-item-user" :class="{ active: task.assigneeId === u.id }"
              @click="assign(u.id)"
            >
              <span class="ctx-avatar" :style="task.assigneeId === u.id ? { background: 'var(--color-primary)' } : {}">{{ u.name.charAt(0) }}</span>
              {{ u.name }}
              <span v-if="task.assigneeId === u.id" class="ctx-check"><AppIcon name="check" :size="12" /></span>
            </button>
            <button class="ctx-item ctx-item-user" @click="assign(null)">
              <span class="ctx-avatar ctx-avatar-empty">—</span> Без исполнителя
            </button>
          </div>
        </div>
        </template>
      </div>
    </Transition>
  </Teleport>

  <ConfirmModal
    v-if="confirmDeleteOpen"
    title="Удалить задачу?"
    :message="`«${task.title}» и все её подзадачи будут удалены без возможности восстановления.`"
    confirm-text="Удалить"
    @confirm="confirmRemove"
    @cancel="cancelRemove"
  />
</template>

<style scoped>
.ctx-menu {
  position: fixed; width: 264px; z-index: 200; padding: 6px;
  background: var(--color-surface); border-radius: 14px;
  box-shadow: 0 4px 12px rgba(20, 24, 38, 0.08), 0 16px 40px rgba(20, 24, 38, 0.16);
  border: 1px solid rgba(20, 24, 38, 0.06);
  max-height: calc(100vh - 16px); overflow-y: auto;
}
.menu-pop-enter-active { transition: opacity 0.14s ease, transform 0.14s ease; }
.menu-pop-enter-from { opacity: 0; transform: scale(0.96) translateY(-4px); }
.menu-pop-leave-active { transition: opacity 0.1s ease; }
.menu-pop-leave-to { opacity: 0; }

.ctx-section { padding: 2px 2px; display: flex; flex-direction: column; gap: 1px; }
.ctx-item {
  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left; border: none; background: none;
  padding: 7px 8px; border-radius: 9px; font-size: 13px; cursor: pointer; color: var(--color-text);
  transition: background 0.1s ease;
}
.ctx-item:hover { background: #f1f3f9; }
.ctx-item.active { background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; }
.ctx-item-danger { color: var(--color-danger); }
.ctx-item-danger:hover { background: #fdeeee; }
.ctx-readonly-hint { font-size: 11px; color: var(--color-text-muted); padding: 4px 10px 6px; margin: 0; }

.ctx-icon {
  width: 22px; height: 22px; border-radius: 7px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.icon-neutral { background: #eef1f7; color: var(--color-text-muted); }
.icon-success { background: #e4f6ea; color: #1e9e4d; }
.icon-warning { background: #fdf1de; color: #c67d16; }
.icon-danger { background: #fdeeee; color: var(--color-danger); }

.ctx-divider { height: 1px; background: var(--color-border); margin: 5px 6px; }
.ctx-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); padding: 4px 10px 6px; }

.ctx-chip-row { display: flex; gap: 5px; padding: 0 6px 4px; flex-wrap: wrap; }
.ctx-chip {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 20px;
  padding: 5px 11px; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 5px;
  transition: all 0.1s ease;
}
.ctx-chip:hover { background: #f1f3f9; }
.ctx-chip-dot.active { font-weight: 600; }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }

.ctx-scroll { max-height: 160px; overflow-y: auto; display: flex; flex-direction: column; gap: 1px; }
.ctx-item-user { font-size: 12.5px; position: relative; }
.ctx-avatar {
  width: 22px; height: 22px; border-radius: 50%; background: #b7bfd1; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 700;
}
.ctx-avatar-empty { background: #d9dde8; color: var(--color-text-muted); }
.ctx-check { margin-left: auto; color: var(--color-primary); font-weight: 700; display: flex; }
</style>
