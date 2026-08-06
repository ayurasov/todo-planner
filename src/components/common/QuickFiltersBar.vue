<script setup>
import { ref, computed } from 'vue'
import QuickToolbar from './QuickToolbar.vue'
import AppIcon from './AppIcon.vue'
import { useFiltersStore } from '../../stores/filtersStore'
import { useUsersStore } from '../../stores/usersStore'
import { usePreferencesStore } from '../../stores/preferencesStore'

const props = defineProps({
  taskCount: { type: Number, default: null },
  meetingMode: { type: Boolean, default: false },
})

const filtersStore = useFiltersStore()
const usersStore = useUsersStore()
const prefs = usePreferencesStore()

const STATUS_OPTIONS = [
  { value: 'all', label: 'Все' },
  { value: 'not_done', label: 'Не выполнено' },
  { value: 'done', label: 'Выполнено' },
]

const DATE_PRESETS = [
  { value: 'today', label: 'Сегодня' },
  { value: 'week', label: '7 дней' },
  { value: 'month', label: 'Месяц' },
]

const assigneePickerOpen = ref(false)

const assigneeSummary = computed(() => {
  if (!filtersStore.assigneeIds.length) return 'Исполнители'
  if (filtersStore.assigneeIds.length === 1) {
    return usersStore.byId(filtersStore.assigneeIds[0])?.name || 'Исполнитель'
  }
  return `Исполнители (${filtersStore.assigneeIds.length})`
})

function forceBubbleMode() {
  if (prefs.groupBy !== 'bubble') prefs.set('groupBy', 'bubble')
}

function setStatus(status) {
  filtersStore.setStatus(status)
  if (status !== 'all') forceBubbleMode()
}

function toggleAssignee(userId) {
  filtersStore.toggleAssignee(userId)
  if (filtersStore.assigneeIds.length) forceBubbleMode()
}

function toggleDatePreset(preset) {
  if (filtersStore.datePreset === preset) filtersStore.setCustomDateRange(null, null)
  else filtersStore.setDatePreset(preset)
  if (filtersStore.datePreset) forceBubbleMode()
}
</script>

<template>
  <div class="quick-filters-bar card">
    <div class="row row-toolbar">
      <QuickToolbar class="embedded-toolbar" :task-count="taskCount" :meeting-mode="meetingMode" compact />
    </div>

    <div class="row row-filters">
      <div class="filter-group" role="group" aria-label="Статус">
        <button
          v-for="opt in STATUS_OPTIONS" :key="opt.value"
          class="filter-btn" :class="{ active: filtersStore.status === opt.value }"
          @click="setStatus(opt.value)"
        >{{ opt.label }}</button>
      </div>

      <div class="filter-divider" />

      <div class="assignee-picker">
        <button class="filter-btn dropdown-trigger" :class="{ active: filtersStore.assigneeIds.length }" @click="assigneePickerOpen = !assigneePickerOpen">
          <AppIcon name="users" :size="13" /> {{ assigneeSummary }} <AppIcon name="chevronDown" :size="11" class="caret" />
        </button>
        <div v-if="assigneePickerOpen" class="assignee-dropdown card" @click.self="assigneePickerOpen = false">
          <label v-for="u in usersStore.users" :key="u.id" class="assignee-option">
            <input type="checkbox" :checked="filtersStore.assigneeIds.includes(u.id)" @change="toggleAssignee(u.id)" />
            {{ u.name }}
          </label>
          <div v-if="!usersStore.users.length" class="assignee-empty">Нет пользователей</div>
        </div>
      </div>

      <div class="filter-divider" />

      <div class="filter-group" role="group" aria-label="Диапазон дат">
        <button
          v-for="p in DATE_PRESETS" :key="p.value"
          class="filter-btn" :class="{ active: filtersStore.datePreset === p.value }"
          @click="toggleDatePreset(p.value)"
        >{{ p.label }}</button>
      </div>

      <button v-if="filtersStore.isActive" class="btn btn-ghost btn-sm reset-btn" @click="filtersStore.resetAll(); assigneePickerOpen = false">
        Сбросить все
      </button>
    </div>
  </div>
</template>

<style scoped>
.quick-filters-bar {
  display: flex; flex-direction: column; gap: 8px;
  padding: 8px 10px; margin-bottom: 12px;
}
.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
/* Вторая строка выровнена по левому краю с первым элементом верхней строки
   (блок «Группировка/Пузырьки»), поскольку quick-toolbar и filter-group используют
   одинаковый внешний padding у карточки. */
.row-toolbar { padding: 0 2px; }
.row-filters { padding: 0 2px; }
.embedded-toolbar { flex: 1 1 auto; min-width: 100%; }
.filter-group { display: flex; gap: 2px; background: #eef1f7; border-radius: 8px; padding: 2px; }
.filter-btn {
  border: none; background: transparent; padding: 5px 10px; border-radius: 6px;
  font-size: 12.5px; color: var(--color-text-muted); cursor: pointer; white-space: nowrap;
  display: flex; align-items: center; gap: 3px;
}
.filter-btn.active { background: var(--color-surface); color: var(--color-text); font-weight: 600; box-shadow: var(--shadow-1); }
.filter-divider { width: 1px; height: 20px; background: var(--color-border); }

.assignee-picker { position: relative; }
.dropdown-trigger {
  border: 1px solid var(--color-border); border-radius: 6px; background: var(--color-surface);
  padding: 5px 10px; font-size: 12.5px; color: var(--color-text-muted); cursor: pointer; display: flex; align-items: center; gap: 5px;
}
.dropdown-trigger.active { color: var(--color-text); font-weight: 600; border-color: var(--color-primary); }
.caret { opacity: 0.7; }
.assignee-dropdown {
  position: absolute; top: calc(100% + 6px); left: 0; z-index: 20; min-width: 200px;
  padding: 8px; display: flex; flex-direction: column; gap: 4px; max-height: 260px; overflow-y: auto;
}
.assignee-option { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 5px 6px; border-radius: 6px; cursor: pointer; }
.assignee-option:hover { background: #eef1f7; }
.assignee-empty { font-size: 12.5px; color: var(--color-text-muted); padding: 6px; }

.reset-btn { margin-left: auto; }
</style>
