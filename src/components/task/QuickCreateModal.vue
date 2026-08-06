<script setup>
import { ref } from 'vue'
import { useTasksStore } from '../../stores/tasksStore'
import { useListsStore } from '../../stores/listsStore'
import { useUsersStore } from '../../stores/usersStore'
import { TaskPriority } from '../../domain/entities/enums'

const emit = defineEmits(['close'])
const tasksStore = useTasksStore()
const listsStore = useListsStore()
const usersStore = useUsersStore()

const title = ref('')
const listId = ref(listsStore.lists[0]?.id || null)
const priority = ref(TaskPriority.MEDIUM)
const assigneeId = ref(usersStore.currentUser?.id || null)
const dueDate = ref('')

async function submit() {
  if (!title.value.trim() || !listId.value) return
  await tasksStore.createTask({
    title: title.value.trim(), listId: listId.value, priority: priority.value,
    assigneeId: assigneeId.value || null,
    dueDate: dueDate.value ? new Date(dueDate.value).toISOString() : null,
  })
  emit('close')
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal card">
      <h3>Новая задача</h3>
      <input v-model="title" class="field-input" placeholder="Название задачи" autofocus @keyup.enter="submit" />
      <div class="field-row">
        <select v-model="listId" class="field-input">
          <option v-for="l in listsStore.lists" :key="l.id" :value="l.id">{{ l.title }}</option>
        </select>
        <select v-model="priority" class="field-input">
          <option v-for="p in Object.values(TaskPriority)" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="field-row">
        <select v-model="assigneeId" class="field-input">
          <option :value="null">Без исполнителя</option>
          <option v-for="u in usersStore.users" :key="u.id" :value="u.id">{{ u.name }}</option>
        </select>
        <input v-model="dueDate" type="date" class="field-input" />
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="emit('close')">Отмена</button>
        <button class="btn btn-primary" @click="submit">Создать</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex;
  align-items: center; justify-content: center; z-index: 100;
}
.modal { width: 420px; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
.modal h3 { margin: 0 0 4px; font-size: 16px; }
.field-input { border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 8px 10px; width: 100%; outline: none; }
.field-input:focus { border-color: var(--color-primary); }
.field-row { display: flex; gap: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 6px; }
</style>
