<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { useAssignableUsers } from '../../composables/useAssignableUsers'
import { useClickOutside } from '../../composables/useClickOutside'
import { getInitials, getAvatarColor } from '../../utils/avatar'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  // listId необязателен: базово задача создаётся без списка. Автоматическая
  // подстановка listId происходит только тогда, когда компонент используется
  // непосредственно внутри конкретного списка (ListView передаёт свой id).
  listId: { type: String, default: null },
  // meetingId — если задан (например, на экране конкретной встречи), поле
  // встречи скрывается и жёстко фиксируется на этой встрече. Если не задан —
  // пользователь может сам выбрать любую из существующих встреч в выпадающем
  // списке (раньше такой возможности не было вообще: новая задача либо не
  // привязывалась к встрече, либо привязка работала только через служебный
  // context из другого места приложения).
  meetingId: { type: String, default: null },
  // occurrenceId — если задан, задача создаётся привязанной не просто к серии
  // встречи, а к конкретной подвстрече регулярной серии (см. MeetingDetailView,
  // блок с перечислением подвстреч). Имеет смысл только совместно с meetingId.
  occurrenceId: { type: String, default: null },
  placeholder: { type: String, default: 'Добавить задачу — Enter, чтобы продолжить' },
})

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const meetingsStore = useMeetingsStore()
const draft = ref('')
const inputEl = ref(null)
const active = ref(false)

const selectedMeetingId = ref(props.meetingId || null)
const meetingPickerOpen = ref(false)
const meetingPickerEl = ref(null)
useClickOutside(meetingPickerEl, () => { meetingPickerOpen.value = false })
const selectedMeeting = computed(() => (selectedMeetingId.value ? meetingsStore.meetingById(selectedMeetingId.value) : null))

function pickMeeting(id) {
  selectedMeetingId.value = id
  meetingPickerOpen.value = false
}

// Список кандидатов на исполнителя — если задача создаётся в контексте встречи,
// то только из её участников (если они настроены) — см. useAssignableUsers.
const assignableUsers = useAssignableUsers(() => ({ meetingId: selectedMeetingId.value }))
const selectedAssigneeId = ref(usersStore.currentUser?.id || null)
const assignPickerOpen = ref(false)
const assignPickerEl = ref(null)
useClickOutside(assignPickerEl, () => { assignPickerOpen.value = false })

const selectedAssignee = computed(() => usersStore.byId(selectedAssigneeId.value))

// Если пользователь сменил встречу и текущий исполнитель больше не входит
// в список участников этой встречи — сбрасываем, чтобы не создать задачу
// с исполнителем, не имеющим отношения к выбранной встрече.
watch(assignableUsers, (users) => {
  if (selectedAssigneeId.value && !users.some((u) => u.id === selectedAssigneeId.value)) {
    selectedAssigneeId.value = null
  }
})

function pickAssignee(userId) {
  selectedAssigneeId.value = userId
  assignPickerOpen.value = false
}

function activate() {
  active.value = true
  nextTick(() => inputEl.value?.focus())
}

async function commit(keepOpen = true) {
  const title = draft.value.trim()
  if (title) {
    await tasksStore.createTask({
      listId: props.listId,
      title,
      meetingId: selectedMeetingId.value,
      occurrenceId: props.occurrenceId || null,
      assigneeId: selectedAssigneeId.value,
    })
  }
  draft.value = ''
  if (keepOpen && title) {
    nextTick(() => inputEl.value?.focus())
  } else {
    active.value = false
  }
}
</script>

<template>
  <div class="quick-add-row card" :class="{ active }">
    <span class="add-icon">＋</span>
    <input
      ref="inputEl"
      v-model="draft"
      :placeholder="placeholder"
      @focus="activate"
      @keyup.enter="commit(true)"
      @keyup.escape="commit(false)"
      @blur="commit(false)"
    />

    <div v-if="!props.meetingId" ref="meetingPickerEl" class="quick-assign">
      <button
        class="quick-assign-btn"
        :title="selectedMeeting ? `Встреча: ${selectedMeeting.title}` : 'Привязать к встрече'"
        @mousedown.prevent="meetingPickerOpen = !meetingPickerOpen"
      >
        <AppIcon name="calendar" :size="13" />
        <span class="quick-assign-label">{{ selectedMeeting ? selectedMeeting.title : 'Встреча' }}</span>
      </button>
      <div v-if="meetingPickerOpen" class="quick-assign-dropdown card scroll-thin" @mousedown.prevent>
        <button class="quick-assign-option" @click="pickMeeting(null)">
          <span class="quick-assign-avatar quick-assign-avatar-empty">—</span> Без встречи
          <span v-if="!selectedMeetingId" class="quick-assign-check">✓</span>
        </button>
        <button
          v-for="m in meetingsStore.sortedByDate" :key="m.id"
          class="quick-assign-option" :class="{ active: selectedMeetingId === m.id }"
          @click="pickMeeting(m.id)"
        >
          <AppIcon name="calendar" :size="13" />
          {{ m.title }}
          <span v-if="selectedMeetingId === m.id" class="quick-assign-check">✓</span>
        </button>
        <div v-if="!meetingsStore.sortedByDate.length" class="quick-assign-empty">Нет созданных встреч</div>
      </div>
    </div>

    <div ref="assignPickerEl" class="quick-assign">
      <button
        class="quick-assign-btn"
        :title="selectedAssignee ? `Исполнитель: ${selectedAssignee.name}` : 'Выбрать исполнителя'"
        @mousedown.prevent="assignPickerOpen = !assignPickerOpen"
      >
        <span
          v-if="selectedAssignee"
          class="quick-assign-avatar"
          :style="{ background: getAvatarColor(selectedAssignee.name) }"
        >{{ getInitials(selectedAssignee.name) }}</span>
        <span v-else class="quick-assign-avatar quick-assign-avatar-empty">+</span>
        <span class="quick-assign-label">{{ selectedAssignee ? selectedAssignee.name : 'Исполнитель' }}</span>
      </button>
      <div v-if="assignPickerOpen" class="quick-assign-dropdown card scroll-thin" @mousedown.prevent>
        <button
          v-for="u in assignableUsers" :key="u.id"
          class="quick-assign-option" :class="{ active: selectedAssigneeId === u.id }"
          @click="pickAssignee(u.id)"
        >
          <span class="quick-assign-avatar" :style="{ background: getAvatarColor(u.name) }">{{ getInitials(u.name) }}</span>
          {{ u.name }}
          <span v-if="selectedAssigneeId === u.id" class="quick-assign-check">✓</span>
        </button>
        <button class="quick-assign-option" @click="pickAssignee(null)">
          <span class="quick-assign-avatar quick-assign-avatar-empty">—</span> Без исполнителя
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-add-row {
  display: flex; align-items: center; gap: 8px; padding: 9px 12px; margin-bottom: 10px;
  border-style: dashed;
}
.quick-add-row.active { border-color: var(--color-primary); border-style: solid; }
.add-icon { color: var(--color-text-muted); font-size: 13px; }
.quick-add-row input { flex: 1; border: none; outline: none; font-size: 13.5px; background: transparent; }

.quick-assign { position: relative; flex-shrink: 0; }
.quick-assign-btn {
  display: flex; align-items: center; gap: 6px; border: 1px solid var(--color-border); background: var(--color-surface);
  border-radius: 20px; padding: 3px 10px 3px 3px; cursor: pointer; font-size: 12px; color: var(--color-text-muted);
}
.quick-assign-btn:hover { border-color: var(--color-primary); }
.quick-assign-avatar {
  width: 22px; height: 22px; border-radius: 50%; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700;
}
.quick-assign-avatar-empty { background: #d9dde8; color: var(--color-text-muted); font-weight: 700; }
.quick-assign-label { max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.quick-assign-dropdown {
  position: absolute; top: calc(100% + 6px); right: 0; z-index: 60; min-width: 200px;
  padding: 4px; display: flex; flex-direction: column; gap: 1px; max-height: 240px; overflow-y: auto;
}
.quick-assign-option {
  display: flex; align-items: center; gap: 8px; width: 100%; text-align: left; border: none; background: none;
  padding: 6px 8px; border-radius: 7px; font-size: 12.5px; cursor: pointer; color: var(--color-text);
}
.quick-assign-option:hover { background: #eef1f7; }
.quick-assign-option.active { background: #eef2ff; color: var(--color-primary-dark); font-weight: 600; }
.quick-assign-check { margin-left: auto; color: var(--color-primary); font-weight: 700; }
.quick-assign-empty { padding: 8px; font-size: 12px; color: var(--color-text-muted); text-align: center; }
</style>
