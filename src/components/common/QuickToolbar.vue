<script setup>
import { computed } from 'vue'
import { usePreferencesStore } from '../../stores/preferencesStore'
import { GroupByMode, GROUP_LABEL } from '../../domain/entities/enums'

const props = defineProps({
  taskCount: { type: Number, default: null },
  // Во встречах режим с единой лентой должен быть упрощён: оставляем только
  // сортировку «Обновлено», чтобы не конкурировать с контекстом встречи и не
  // дублировать смысл пузырькового режима, где уже есть прозрачная логика
  // «Не выполнено / Выполнено».
  meetingMode: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
})
const prefs = usePreferencesStore()

const QUICK_SORTS = computed(() => {
  if (props.meetingMode) return [{ field: 'updated_at', label: 'Обновлено' }]
  return [
    { field: 'score', label: 'Актуальность' },
    { field: 'due_date', label: 'Срок' },
    { field: 'priority', label: 'Приоритет' },
    { field: 'updated_at', label: 'Обновлено' },
  ]
})

function setSort(field) {
  if (prefs.sortField === field) prefs.set('sortDir', prefs.sortDir === 'asc' ? 'desc' : 'asc')
  else { prefs.set('sortField', field); prefs.set('sortDir', 'desc') }
}

function cycleDensity() {
  const order = ['compact', 'comfortable', 'spacious']
  const next = order[(order.indexOf(prefs.density) + 1) % order.length]
  prefs.set('density', next)
}

const viewMode = computed(() => (prefs.groupBy === 'bubble' ? 'bubble' : 'grouping'))
let lastNonBubbleGroupBy = prefs.groupBy === 'bubble' ? 'none' : prefs.groupBy
function setViewMode(mode) {
  if (mode === 'bubble') {
    if (prefs.groupBy !== 'bubble') lastNonBubbleGroupBy = prefs.groupBy
    prefs.set('groupBy', 'bubble')
  } else {
    prefs.set('groupBy', lastNonBubbleGroupBy)
  }
}

const DENSITY_ICON = { compact: '≡', comfortable: '☰', spacious: '▤' }
</script>

<template>
  <div class="quick-toolbar" :class="{ compact }">
    <span v-if="taskCount !== null" class="task-count">{{ taskCount }} задач</span>

    <div class="quick-group" role="group" aria-label="Режим отображения">
      <button
        class="quick-btn" :class="{ active: viewMode === 'grouping' }"
        @click="setViewMode('grouping')"
        title="Обычный режим: группировка и сортировка списка"
      >Группировка</button>
      <button
        class="quick-btn" :class="{ active: viewMode === 'bubble' }"
        @click="setViewMode('bubble')"
        title="Два блока: Не выполнено (просрочка → срок → без срока) и Выполнено (по дате завершения)"
      >Пузырьки</button>
    </div>

    <template v-if="viewMode === 'grouping'">
      <div class="quick-group" role="group" aria-label="Сортировка">
        <button
          v-for="s in QUICK_SORTS" :key="s.field"
          class="quick-btn" :class="{ active: prefs.sortField === s.field }"
          @click="setSort(s.field)"
          :title="`Сортировать по: ${s.label}`"
        >
          {{ s.label }}
          <span v-if="prefs.sortField === s.field" class="dir-arrow">{{ prefs.sortDir === 'asc' ? '↑' : '↓' }}</span>
        </button>
      </div>

      <select class="quick-select" :value="prefs.groupBy" title="Группировка" @change="prefs.set('groupBy', $event.target.value)">
        <option v-for="g in Object.values(GroupByMode).filter((g) => g !== 'bubble')" :key="g" :value="g">{{ GROUP_LABEL[g] }}</option>
      </select>

      <label class="quick-toggle" title="Показывать выполненные задачи">
        <input type="checkbox" :checked="prefs.showCompleted" @change="prefs.toggle('showCompleted')" />
        Выполненные
      </label>
    </template>

    <div class="quick-toolbar-spacer" />

    <button class="quick-icon-btn" title="Плотность строк" @click="cycleDensity">{{ DENSITY_ICON[prefs.density] }}</button>

    <router-link to="/settings" class="quick-icon-btn" title="Все настройки отображения">⋯</router-link>
  </div>
</template>

<style scoped>
.quick-toolbar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 6px 2px 12px; font-size: 12.5px;
}
.quick-toolbar.compact { padding: 0; gap: 8px; flex: 1; }
.task-count { color: var(--color-text-muted); margin-right: 4px; }
.quick-group { display: flex; gap: 2px; background: #eef1f7; border-radius: 8px; padding: 2px; }
.quick-btn {
  border: none; background: transparent; padding: 5px 10px; border-radius: 6px;
  font-size: 12.5px; color: var(--color-text-muted); cursor: pointer; display: flex; align-items: center; gap: 3px;
}
.quick-btn.active { background: var(--color-surface); color: var(--color-text); font-weight: 600; box-shadow: var(--shadow-1); }
.dir-arrow { font-size: 11px; }
.quick-select {
  border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12.5px; background: var(--color-surface);
}
.quick-toggle { display: flex; align-items: center; gap: 5px; cursor: pointer; color: var(--color-text-muted); }
.quick-toolbar-spacer { flex: 1; min-width: 0; }
.quick-icon-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 6px;
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; text-decoration: none; color: var(--color-text); font-size: 13px;
}
.quick-icon-btn:hover { background: #eef1f7; }
</style>
