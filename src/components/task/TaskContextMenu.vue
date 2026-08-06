<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useClickOutside } from '../../composables/useClickOutside'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { useTaskPermissions } from '../../composables/usePermissions'
import { useAssignableUsers } from '../../composables/useAssignableUsers'
import { TaskPriority, PRIORITY_LABEL } from '../../domain/entities/enums'

const props = defineProps({
  task: { type: Object, required: true },
  x: { type: Number, required: true },
  y: { type: Number, required: true },
})
const emit = defineEmits(['close', 'open-detail', 'add-subtask', 'rename'])

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const prefs = usePreferencesStore()
const menuEl = ref(null)
const mounted = ref(false)
const measuredSize = ref({ w: 264, h: 0 })

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

function remove() {
  if (confirm('Удалить задачу и все подзадачи?')) {
    tasksStore.removeTask(props.task.id)
  }
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
        <div class="ctx-header">
          <span class="ctx-title">{{ task.title }}</span>
        </div>

        <div class="ctx-section">
          <button v-if="canToggleStatus" class="ctx-item ctx-item-primary" @click="toggleComplete">
            <span class="ctx-icon" :class="isDone ? 'icon-neutral' : 'icon-success'">{{ isDone ? '↺' : '✓' }}</span>
            {{ isDone ? 'Вернуть в работу' : 'Завершить' }}
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="rename">
            <span class="ctx-icon icon-neutral">✎</span> Переименовать
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="addSubtask">
            <span class="ctx-icon icon-neutral">＋</span> Добавить подзадачу
          </button>
          <button class="ctx-item" @click="openDetail">
            <span class="ctx-icon icon-neutral">☰</span> Открыть детали
          </button>
          <button v-if="canEditThisTask" class="ctx-item" @click="togglePin">
            <span class="ctx-icon" :class="task.pinned ? 'icon-warning' : 'icon-neutral'">📌</span>
            {{ task.pinned ? 'Открепить' : 'Закрепить' }}
          </button>
          <button v-if="canEditThisTask && isSubtask" class="ctx-item" @click="toggleStandalone">
            <span class="ctx-icon icon-neutral">{{ task.displayStandalone ? '⊟' : '⊞' }}</span>
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
              <span v-if="task.assigneeId === u.id" class="ctx-check">✓</span>
            </button>
            <button class="ctx-item ctx-item-user" @click="assign(null)">
              <span class="ctx-avatar ctx-avatar-empty">—</span> Без исполнителя
            </button>
          </div>
        </div>

        <div class="ctx-divider" />

        <div class="ctx-section">
          <button class="ctx-item" @click="duplicate">
            <span class="ctx-icon icon-neutral">⧉</span> Дублировать
          </button>
        </div>
        </template>

        <div v-if="canDeleteThisTask" class="ctx-divider" />
        <div v-if="canDeleteThisTask" class="ctx-section">
          <button class="ctx-item ctx-item-danger" @click="remove">
            <span class="ctx-icon icon-danger">✖</span> Удалить
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
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

.ctx-header { padding: 8px 12px 6px; }
.ctx-title {
  font-size: 12px; font-weight: 600; color: var(--color-text-muted);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

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
  font-size: 12px; flex-shrink: 0;
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
.ctx-check { margin-left: auto; color: var(--color-primary); font-weight: 700; }
</style>
