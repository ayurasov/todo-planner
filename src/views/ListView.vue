<script setup>
import { ref, computed } from 'vue'
import { useTasksStore } from '../stores/tasksStore'
import { useListsStore } from '../stores/listsStore'
import TaskListPanel from '../components/task/TaskListPanel.vue'
import QuickAddTaskRow from '../components/task/QuickAddTaskRow.vue'
import ListSettingsModal from '../components/common/ListSettingsModal.vue'
import QuickFiltersBar from '../components/common/QuickFiltersBar.vue'
import AppIcon from '../components/common/AppIcon.vue'

const props = defineProps({ id: { type: String, required: true } })
const tasksStore = useTasksStore()
const listsStore = useListsStore()
const showSettings = ref(false)

const list = computed(() => listsStore.byId(props.id))
const rankedRoots = computed(() => tasksStore.rankedTasksForList(props.id).filter((t) => !t.parentTaskId))

function toggleArchived() {
  if (!list.value) return
  if (list.value.archived) listsStore.unarchiveList(list.value.id)
  else listsStore.archiveList(list.value.id)
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
      <button
        class="btn btn-ghost btn-icon" :title="list?.archived ? 'Вернуть из архива' : 'Архивировать список'"
        @click="toggleArchived"
      ><AppIcon :name="list?.archived ? 'undo' : 'copy'" :size="15" /></button>
      <button class="btn btn-ghost btn-icon" title="Настроить список" @click="showSettings = true"><AppIcon name="settings" :size="15" /></button>
    </div>
  </div>
  <p v-if="list?.description" class="list-description">{{ list.description }}</p>
  <QuickFiltersBar :task-count="rankedRoots.length" />
  <QuickAddTaskRow :list-id="id" />
  <TaskListPanel :tasks="rankedRoots" empty-text="В этом списке пока нет задач" />
  <ListSettingsModal v-if="showSettings && list" :list="list" @close="showSettings = false" />
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.view-title { display: flex; align-items: center; gap: 8px; }
.view-title h2 { margin: 0; font-size: 19px; }
.list-icon { width: 30px; height: 30px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.archived-tag { background: #eef1f7; color: var(--color-text-muted); }
.header-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.list-description { color: var(--color-text-muted); font-size: 13px; margin-bottom: 14px; }
</style>
