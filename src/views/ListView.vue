<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '../stores/tasksStore'
import { useListsStore } from '../stores/listsStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'
import AppIcon from '../components/common/AppIcon.vue'
import ListSettingsModal from '../components/common/ListSettingsModal.vue'
import ConfirmModal from '../components/common/ConfirmModal.vue'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const tasksStore = useTasksStore()
const listsStore = useListsStore()

const list = computed(() => listsStore.byId(props.id))
const rankedRoots = computed(() => tasksStore.rankedTasksForList(props.id).filter((t) => !t.parentTaskId))

// Раньше настроить (иконка/цвет/доступ/поведение) или удалить список было только
// со страницы "Управление списками" (ListsManagerView.vue) — сам список (ListView) не
// давал такой возможности, хотя пользователь ожидает те же действия со страницы
// самого списка, а не только из общего реестра. Кнопки "Настроить"/"удалить" здесь
// открывают тот же ListSettingsModal/ConfirmModal, что и ListsManagerView.vue — один
// и тот же UI редактирования списка, без дублирования логики.
const showSettings = ref(false)
const showDeleteConfirm = ref(false)

const listTaskCount = computed(() => tasksStore.tasks.filter((t) => t.listId === props.id).length)
const deleteMessage = computed(() => {
  const count = listTaskCount.value
  return count
    ? `Удалить список «${list.value?.title}»? ${count} задач(и) останутся, но потеряют привязку к нему.`
    : `Удалить список «${list.value?.title}»?`
})

function toggleArchived() {
  if (!list.value) return
  if (list.value.archived) listsStore.unarchiveList(list.value.id)
  else listsStore.archiveList(list.value.id)
}

async function confirmDeleteList() {
  for (const t of tasksStore.tasks.filter((x) => x.listId === props.id)) {
    await tasksStore.updateTaskField(t.id, 'listId', null)
  }
  await listsStore.removeList(props.id)
  showDeleteConfirm.value = false
  router.push('/lists')
}
</script>

<template>
  <div class="view-header">
    <div class="view-title">
      <span class="list-icon" :style="{ background: (list?.color || 'var(--color-primary)') + '22', color: list?.color || 'var(--color-primary)' }">
        <AppIcon :name="list?.settings?.icon || 'folder'" :size="16" />
      </span>
      <h2>{{ list?.title }}</h2>
      <span v-if="list?.archived" class="tag archived-tag">В архиве</span>
    </div>
    <div class="header-actions">
      <button class="btn btn-ghost btn-icon" title="Настроить список" @click="showSettings = true"><AppIcon name="settings" :size="15" /></button>
      <button
        class="btn btn-ghost btn-icon" :title="list?.archived ? 'Вернуть из архива' : 'Архивировать список'"
        @click="toggleArchived"
      ><AppIcon :name="list?.archived ? 'undo' : 'copy'" :size="15" /></button>
      <button class="btn btn-ghost btn-icon btn-danger-ghost" title="удалить список" @click="showDeleteConfirm = true"><AppIcon name="trash" :size="15" /></button>
    </div>
  </div>
  <p v-if="list?.description" class="list-description">{{ list.description }}</p>
  <QuickFiltersBar :task-count="rankedRoots.length" />
  <QuickAddTaskRow :list-id="id" />
  <TaskListPanel :tasks="rankedRoots" empty-text="В этом списке пока нет задач" />

  <ListSettingsModal v-if="showSettings && list" :list="list" @close="showSettings = false" />
  <ConfirmModal
    v-if="showDeleteConfirm"
    title="удалить список?"
    :message="deleteMessage"
    confirm-text="удалить"
    @confirm="confirmDeleteList"
    @cancel="showDeleteConfirm = false"
  />
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.view-title { display: flex; align-items: center; gap: 8px; }
.view-title h2 { margin: 0; font-size: 19px; }
.list-icon { width: 30px; height: 30px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.archived-tag { background: #eef1f7; color: var(--color-text-muted); }
.header-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.btn-danger-ghost { color: var(--color-danger); }
.btn-danger-ghost:hover { background: #fdeceb; }
.list-description { color: var(--color-text-muted); font-size: 13px; margin-bottom: 14px; }
</style>
