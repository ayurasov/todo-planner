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

// Раньше настроить (иконка/цвет/доступ/поведение) и удалить список можно было
// только из ListsManagerView — при открытии самого списка не было ни одной
// кнопки управления, кроме архивации. Переиспользуем тот же ListSettingsModal
// и тот же ConfirmModal, что и в ListsManagerView.vue, чтобы поведение и вид
// формы были идентичны независимо от того, откуда её открыли.
const showSettings = ref(false)
const listPendingRemoval = ref(null)

const listPendingRemovalTaskCount = computed(() => {
  if (!listPendingRemoval.value) return 0
  return tasksStore.tasks.filter((t) => t.listId === listPendingRemoval.value.id).length
})

const listPendingRemovalMessage = computed(() => {
  if (!listPendingRemoval.value) return ''
  const count = listPendingRemovalTaskCount.value
  return count
    ? `Удалить список «${listPendingRemoval.value.title}»? ${count} задач(и) останутся, но потеряют привязку к нему.`
    : `Удалить список «${listPendingRemoval.value.title}»?`
})

function toggleArchived() {
  if (!list.value) return
  if (list.value.archived) listsStore.unarchiveList(list.value.id)
  else listsStore.archiveList(list.value.id)
}

function requestRemoveList() {
  if (!list.value) return
  listPendingRemoval.value = list.value
}

function cancelRemoveList() {
  listPendingRemoval.value = null
}

async function confirmRemoveList() {
  const target = listPendingRemoval.value
  if (!target) return
  for (const t of tasksStore.tasks.filter((x) => x.listId === target.id)) {
    await tasksStore.updateTaskField(t.id, 'listId', null)
  }
  await listsStore.removeList(target.id)
  listPendingRemoval.value = null
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
      <button class="btn btn-ghost btn-icon btn-danger-ghost" title="Удалить список" @click="requestRemoveList"><AppIcon name="trash" :size="15" /></button>
    </div>
  </div>
  <p v-if="list?.description" class="list-description">{{ list.description }}</p>
  <QuickFiltersBar :task-count="rankedRoots.length" />
  <QuickAddTaskRow :list-id="id" />
  <TaskListPanel :tasks="rankedRoots" empty-text="В этом списке пока нет задач" />

  <ListSettingsModal v-if="showSettings && list" :list="list" @close="showSettings = false" />

  <ConfirmModal
    v-if="listPendingRemoval"
    title="Удалить список?"
    :message="listPendingRemovalMessage"
    confirm-text="Удалить"
    @confirm="confirmRemoveList"
    @cancel="cancelRemoveList"
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
