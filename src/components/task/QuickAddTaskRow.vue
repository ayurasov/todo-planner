<script setup>
import { ref, nextTick } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'

const props = defineProps({
  // listId необязателен: базово задача создаётся без списка. Автоматическая
  // подстановка listId происходит только тогда, когда компонент используется
  // непосредственно внутри конкретного списка (ListView передаёт свой id).
  listId: { type: String, default: null },
  meetingId: { type: String, default: null },
  placeholder: { type: String, default: 'Добавить задачу — Enter, чтобы продолжить' },
})

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const draft = ref('')
const inputEl = ref(null)
const active = ref(false)

function activate() {
  active.value = true
  nextTick(() => inputEl.value?.focus())
}

async function commit(keepOpen = true) {
  const title = draft.value.trim()
  if (title) {
    await tasksStore.createTask({ listId: props.listId, title, meetingId: props.meetingId, assigneeId: usersStore.currentUser?.id || null })
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
</style>
