<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useListsStore } from '../../stores/listsStore'
import { useUsersStore } from '../../stores/usersStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { useAssignableUsers } from '../../composables/useAssignableUsers'
import { TaskPriority, PRIORITY_LABEL } from '../../domain/entities/enums'

const props = defineProps({
  context: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close'])
const tasksStore = useTasksStore()
const listsStore = useListsStore()
const usersStore = useUsersStore()
const meetingsStore = useMeetingsStore()

const titleEl = ref(null)
const title = ref('')
const listId = ref(props.context.listId || null)
const parentTaskId = ref(props.context.parentTaskId || null)
const meetingId = ref(props.context.meetingId || null)
const priority = ref(props.context.priority || TaskPriority.MEDIUM)
const assigneeId = ref(props.context.assigneeId || usersStore.currentUser?.id || null)
const dueDate = ref(props.context.dueDate ? props.context.dueDate.slice(0, 10) : '')
const createMore = ref(false)

const contextList = computed(() => listsStore.byId(listId.value))
const parentTask = computed(() => parentTaskId.value ? tasksStore.byId(parentTaskId.value) : null)
const contextMeeting = computed(() => meetingId.value ? meetingsStore.meetingById(meetingId.value) : null)
const PRIORITY_COLOR = { low: '#9aa3b2', medium: '#4f7cff', high: '#e8a13a', urgent: '#e5484d' }

// Список исполнителей ограничивается участниками встречи (attendeeIds), если
// задача привязана к встрече и участники для неё настроены владельцем —
// см. useAssignableUsers.js. При создании из карточки встречи через верхнюю
// кнопку «+ Создать задачу» meetingId уже приходит в context (AppTopBar.vue).
const assignableUsers = useAssignableUsers(() => ({ meetingId: meetingId.value }))

// Если пользователь вручную сменил встречу (или очистил её) и текущий
// assignee больше не входит в список доступных участников — сбрасываем,
// чтобы не отправить задачу с исполнителем, не имеющим отношения к встрече.
watch(assignableUsers, (users) => {
  if (assigneeId.value && !users.some((u) => u.id === assigneeId.value)) {
    assigneeId.value = null
  }
})

onMounted(() => nextTick(() => titleEl.value?.focus()))

async function submit() {
  if (!title.value.trim()) return
  await tasksStore.createTask({
    title: title.value.trim(), listId: listId.value, priority: priority.value,
    parentTaskId: parentTaskId.value || null,
    assigneeId: assigneeId.value || null,
    dueDate: dueDate.value ? new Date(dueDate.value).toISOString() : null,
    meetingId: meetingId.value || null,
  })
  if (createMore.value) {
    title.value = ''
    nextTick(() => titleEl.value?.focus())
  } else {
    emit('close')
  }
}

function quickDue(days) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  dueDate.value = d.toISOString().slice(0, 10)
}
</script>

<template>
  <div class="modal-overlay">
    <Transition name="modal-pop" appear>
      <div class="modal card">
        <div class="modal-head">
          <h3>Новая задача</h3>
          <span v-if="parentTask" class="context-hint">↳ подзадача «{{ parentTask.title }}»</span>
          <span v-else-if="contextList" class="context-hint">
            <span class="list-dot" :style="{ background: contextList.color }" /> {{ contextList.title }}
          </span>
        </div>

        <input ref="titleEl" v-model="title" class="title-input" placeholder="Что нужно сделать?" @keyup.enter="submit" @keyup.escape="emit('close')" />

        <div class="field-block" v-if="!parentTask">
          <span class="field-caption">Список (необязательно)</span>
          <select v-model="listId" class="field-select">
            <option :value="null">Без списка</option>
            <option v-for="l in listsStore.lists" :key="l.id" :value="l.id">{{ l.title }}</option>
          </select>
        </div>

        <div class="field-block">
          <span class="field-caption">Встреча (необязательно)</span>
          <select v-model="meetingId" class="field-select">
            <option :value="null">Без встречи</option>
            <option v-for="m in meetingsStore.sortedByDate" :key="m.id" :value="m.id">{{ m.title }}</option>
          </select>
          <span v-if="contextMeeting" class="field-hint">
            Исполнитель ограничен участниками этой встречи{{ contextMeeting.attendeeIds?.length ? '' : ' (участники не заданы — доступны все)' }}
          </span>
        </div>

        <div class="field-block">
          <span class="field-caption">Приоритет</span>
          <div class="segmented-pills">
            <button
              v-for="p in Object.values(TaskPriority)" :key="p"
              class="pill" :class="{ active: priority === p }"
              :style="priority === p ? { background: PRIORITY_COLOR[p], color: '#fff', borderColor: PRIORITY_COLOR[p] } : {}"
              @click="priority = p"
            >
              <span class="dot" :style="{ background: priority === p ? '#fff' : PRIORITY_COLOR[p] }" />
              {{ PRIORITY_LABEL[p] }}
            </button>
          </div>
        </div>

        <div class="field-block">
          <span class="field-caption">Исполнитель</span>
          <div class="assignee-pills">
            <button class="assignee-pill" :class="{ active: !assigneeId }" @click="assigneeId = null">Не назначен</button>
            <button
              v-for="u in assignableUsers" :key="u.id"
              class="assignee-pill" :class="{ active: assigneeId === u.id }"
              @click="assigneeId = u.id"
            >
              <span class="mini-avatar">{{ u.name.charAt(0) }}</span>{{ u.name }}
            </button>
            <span v-if="!assignableUsers.length" class="field-hint">Нет доступных участников</span>
          </div>
        </div>

        <div class="field-block">
          <span class="field-caption">Срок</span>
          <div class="due-row">
            <button class="chip" @click="quickDue(0)">Сегодня</button>
            <button class="chip" @click="quickDue(1)">завтра</button>
            <button class="chip" @click="quickDue(7)">+Неделя</button>
            <input v-model="dueDate" type="date" class="date-input" />
          </div>
        </div>

        <div class="modal-footer">
          <label class="create-more-toggle">
            <input type="checkbox" v-model="createMore" /> Создавать ещё
          </label>
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="emit('close')">Отмена</button>
            <button class="btn btn-primary" @click="submit">Создать</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex;
  align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(1px);
}
.modal { width: 460px; padding: 20px; display: flex; flex-direction: column; gap: 14px; border-radius: 16px; box-shadow: 0 20px 60px rgba(20,24,38,0.25); }
.modal-pop-enter-active { transition: opacity 0.16s ease, transform 0.16s cubic-bezier(0.32,0.72,0,1); }
.modal-pop-enter-from { opacity: 0; transform: scale(0.95) translateY(6px); }
.modal-head { display: flex; flex-direction: column; gap: 3px; }
.modal-head h3 { margin: 0; font-size: 16px; }
.context-hint { font-size: 12px; color: var(--color-text-muted); display: flex; align-items: center; gap: 5px; }
.list-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.title-input { border: none; border-bottom: 1.5px solid var(--color-border); border-radius: 0; padding: 8px 2px; font-size: 16px; font-weight: 500; outline: none; }
.title-input:focus { border-bottom-color: var(--color-primary); }
.field-block { display: flex; flex-direction: column; gap: 6px; }
.field-caption { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted); }
.field-select { border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 10px; font-size: 13px; }
.field-hint { font-size: 11px; color: var(--color-text-muted); }
.segmented-pills { display: flex; gap: 5px; flex-wrap: wrap; }
.pill {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 20px;
  padding: 5px 12px; font-size: 12.5px; cursor: pointer; color: var(--color-text-muted); display: flex; align-items: center; gap: 5px;
}
.pill:hover { background: #f1f3f9; }
.pill.active { font-weight: 600; color: var(--color-text); }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.assignee-pills { display: flex; gap: 5px; flex-wrap: wrap; align-items: center; }
.assignee-pill {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 20px;
  padding: 5px 10px; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.assignee-pill:hover { background: #f1f3f9; }
.assignee-pill.active { background: #eef2ff; border-color: var(--color-primary); color: var(--color-primary-dark); font-weight: 600; }
.mini-avatar { width: 16px; height: 16px; border-radius: 50%; background: var(--color-primary); color: #fff; font-size: 8.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.due-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.chip { border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 16px; padding: 5px 11px; font-size: 12px; cursor: pointer; }
.chip:hover { background: #f1f3f9; }
.date-input { border: 1px solid var(--color-border); border-radius: 16px; padding: 5px 10px; font-size: 12px; }
.modal-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; }
.create-more-toggle { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-text-muted); cursor: pointer; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
