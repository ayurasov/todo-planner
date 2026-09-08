<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import QuickToolbar from './QuickToolbar.vue'
import AppIcon from './AppIcon.vue'
import { useFiltersStore } from '../../stores/filtersStore'
import { useUsersStore } from '../../stores/usersStore'
import { usePreferencesStore } from '../../stores/preferencesStore'

const props = defineProps({
  taskCount: { type: Number, default: null },
  meetingMode: { type: Boolean, default: false },
  showAssigneeFilter: { type: Boolean, default: true },
  showSearch: { type: Boolean, default: false },
  assigneeUsers: { type: Array, default: null },
  showRecentDoneFilters: { type: Boolean, default: false },
})

const filtersStore = useFiltersStore()
const usersStore = useUsersStore()
const prefs = usePreferencesStore()

const STATUS_OPTIONS = [
  { value: 'all', label: 'Все' },
  { value: 'not_done', label: 'Не выполнено' },
  { value: 'done', label: 'Выполнено' },
]
const RECENT_DONE_OPTIONS = [
  { value: '7', label: '7д', title: 'Не выполнено + выполнено за последнюю неделю' },
  { value: '14', label: '14д', title: 'Не выполнено + выполнено за последние 2 недели' },
]
const DUE_DATE_PRESETS = [
  { value: 'overdue', label: 'Просрочено' },
  { value: 'no_due', label: 'Нет срока' },
  { value: 'today', label: 'Сегодня' },
  { value: 'tomorrow', label: 'Завтра' },
  { value: 'week', label: '7 дней' },
  { value: 'month', label: 'Месяц' },
]
const CREATED_DATE_PRESETS = [
  { value: 'today', label: 'Сегодня' },
  { value: 'yesterday', label: 'Вчера' },
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
]

const assigneePickerOpen = ref(false)
const assigneePicker = ref(null)
const assigneeSummary = computed(() => {
  if (!filtersStore.assigneeIds.length) return 'Исполнители'
  if (filtersStore.assigneeIds.length === 1) return usersStore.byId(filtersStore.assigneeIds[0])?.name || 'Исполнитель'
  return `Исполнители (${filtersStore.assigneeIds.length})`
})
const visibleAssigneeUsers = computed(() => props.assigneeUsers || usersStore.users)

function forceBubbleMode() {
  if (prefs.groupBy !== 'bubble') prefs.set('groupBy', 'bubble')
}
function setStatus(status) { filtersStore.setStatus(status); if (status !== 'all') forceBubbleMode() }
function setRecentDone(preset) { filtersStore.setRecentDonePreset(preset); if (filtersStore.recentDonePreset) forceBubbleMode() }
function toggleAssignee(userId) { filtersStore.toggleAssignee(userId); if (filtersStore.assigneeIds.length) forceBubbleMode() }
function toggleDueDatePreset(preset) {
  if (filtersStore.dueDatePreset === preset) filtersStore.setCustomDateRange(null, null)
  else filtersStore.setDueDatePreset(preset)
  if (filtersStore.dueDatePreset) forceBubbleMode()
}
function toggleCreatedDatePreset(preset) {
  if (filtersStore.createdDatePreset === preset) filtersStore.resetCreatedDate()
  else filtersStore.setCreatedDatePreset(preset)
  if (filtersStore.createdDatePreset) forceBubbleMode()
}
function closeAssigneeOnOutsideClick(event) {
  if (assigneePickerOpen.value && assigneePicker.value && !assigneePicker.value.contains(event.target)) assigneePickerOpen.value = false
}
onMounted(() => document.addEventListener('click', closeAssigneeOnOutsideClick, true))
onBeforeUnmount(() => document.removeEventListener('click', closeAssigneeOnOutsideClick, true))
</script>

<template>
  <div class="quick-filters-bar card">
    <div class="row row-toolbar">
      <QuickToolbar class="embedded-toolbar" :task-count="taskCount" :meeting-mode="meetingMode" compact>
        <template #after-view-mode>
          <div class="filter-group" role="group" aria-label="Статус">
            <button v-for="opt in STATUS_OPTIONS" :key="opt.value" class="filter-btn" :class="{ active: filtersStore.status === opt.value && !filtersStore.recentDonePreset }" @click="setStatus(opt.value)">{{ opt.label }}</button>
          </div>
          <div v-if="showRecentDoneFilters" class="filter-group recent-done-group" role="group" aria-label="Статус и недавнее выполнение">
            <button v-for="opt in RECENT_DONE_OPTIONS" :key="opt.value" class="filter-btn compact-filter" :class="{ active: filtersStore.recentDonePreset === opt.value }" :title="opt.title" :aria-label="opt.title" @click="setRecentDone(opt.value)">{{ opt.label }}</button>
          </div>
          <div v-if="showAssigneeFilter" ref="assigneePicker" class="assignee-picker">
            <button class="filter-btn dropdown-trigger" :class="{ active: filtersStore.assigneeIds.length }" @click.stop="assigneePickerOpen = !assigneePickerOpen">
              <AppIcon name="users" :size="13" /> {{ assigneeSummary }} <AppIcon name="chevronDown" :size="11" class="caret" />
            </button>
            <div v-if="assigneePickerOpen" class="assignee-dropdown card">
              <label v-for="u in visibleAssigneeUsers" :key="u.id" class="assignee-option">
                <input type="checkbox" :checked="filtersStore.assigneeIds.includes(u.id)" @change="toggleAssignee(u.id)" />
                {{ u.name }}
              </label>
              <div v-if="!visibleAssigneeUsers.length" class="assignee-empty">Нет исполнителей с видимыми задачами</div>
            </div>
          </div>
          <label v-if="showSearch" class="task-search">
            <AppIcon name="search" :size="13" />
            <input :value="filtersStore.searchText" placeholder="Поиск по задачам" @input="filtersStore.setSearchText($event.target.value)" />
          </label>
        </template>
      </QuickToolbar>
    </div>

    <div class="row row-filters">
      <div class="created-filters-block">
        <span class="row-label">Создано:</span>
        <div class="filter-group" role="group" aria-label="Дата создания">
          <button v-for="p in CREATED_DATE_PRESETS" :key="p.value" class="filter-btn" :class="{ active: filtersStore.createdDatePreset === p.value }" @click="toggleCreatedDatePreset(p.value)">{{ p.label }}</button>
        </div>
      </div>
      <div class="filter-group" role="group" aria-label="Срок">
        <button v-for="p in DUE_DATE_PRESETS" :key="p.value" class="filter-btn" :class="{ active: filtersStore.dueDatePreset === p.value }" @click="toggleDueDatePreset(p.value)">{{ p.label }}</button>
      </div>
      <button v-if="filtersStore.isActive" class="btn btn-ghost btn-sm reset-btn" @click="filtersStore.resetAll(); assigneePickerOpen = false">Сбросить все</button>
    </div>
  </div>
</template>

<style scoped>
.quick-filters-bar { display: flex; flex-direction: column; gap: 8px; padding: 8px 10px; margin-bottom: 12px; }
.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.row-toolbar, .row-filters { padding: 0 2px; }
.embedded-toolbar { flex: 1 1 auto; min-width: 100%; }
.created-filters-block { display: flex; align-items: center; gap: 8px; }
.row-label { font-size: 12px; color: var(--color-text-muted); font-weight: 600; }
.filter-group { display: flex; gap: 2px; background: #eef1f7; border-radius: 8px; padding: 2px; }
.filter-btn { border: none; background: transparent; padding: 5px 10px; border-radius: 6px; font-size: 12.5px; color: var(--color-text-muted); cursor: pointer; white-space: nowrap; display: flex; align-items: center; gap: 3px; }
.filter-btn.active { background: var(--color-surface); color: var(--color-text); font-weight: 600; box-shadow: var(--shadow-1); }
.compact-filter { min-width: 32px; padding-inline: 7px; font-weight: 700; }
.assignee-picker { position: relative; }
.dropdown-trigger { border: 1px solid var(--color-border); border-radius: 6px; background: var(--color-surface); padding: 5px 10px; font-size: 12.5px; color: var(--color-text-muted); cursor: pointer; display: flex; align-items: center; gap: 5px; }
.dropdown-trigger.active { color: var(--color-text); font-weight: 600; border-color: var(--color-primary); }
.caret { opacity: 0.7; }
.assignee-dropdown { position: absolute; top: calc(100% + 6px); left: 0; z-index: 20; min-width: 200px; padding: 8px; display: flex; flex-direction: column; gap: 4px; max-height: 260px; overflow-y: auto; }
.assignee-option { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 5px 6px; border-radius: 6px; cursor: pointer; }
.assignee-option:hover { background: #eef1f7; }
.assignee-empty { font-size: 12.5px; color: var(--color-text-muted); padding: 6px; }
.task-search { display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--color-border); border-radius: 7px; background: var(--color-surface); padding: 4px 8px; min-width: 210px; color: var(--color-text-muted); }
.task-search input { border: none; outline: none; min-width: 0; width: 100%; background: transparent; font-size: 12.5px; color: var(--color-text); }
.reset-btn { margin-left: auto; }
</style>
