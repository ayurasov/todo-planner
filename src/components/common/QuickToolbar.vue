<script setup>
import { usePreferencesStore } from '../../stores/preferencesStore'
import { GroupByMode, GROUP_LABEL } from '../../domain/entities/enums'

defineProps({ taskCount: { type: Number, default: null } })
const prefs = usePreferencesStore()

function cycleDensity() {
  const order = ['compact', 'comfortable', 'spacious']
  const next = order[(order.indexOf(prefs.density) + 1) % order.length]
  prefs.set('density', next)
}

const DENSITY_ICON = { compact: '≡', comfortable: '☰', spacious: '▤' }
</script>

<template>
  <div class="quick-toolbar">
    <span v-if="taskCount !== null" class="task-count">{{ taskCount }} задач</span>

    <select class="quick-select" :value="prefs.groupBy" title="Группировка внутри блоков Не выполнено / Выполнено" @change="prefs.set('groupBy', $event.target.value)">
      <option v-for="g in Object.values(GroupByMode)" :key="g" :value="g">{{ GROUP_LABEL[g] }}</option>
    </select>

    <button class="quick-icon-btn" title="Плотность строк" @click="cycleDensity">{{ DENSITY_ICON[prefs.density] }}</button>

    <router-link to="/settings" class="quick-icon-btn" title="Все настройки отображения">⋯</router-link>
  </div>
</template>

<style scoped>
.quick-toolbar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 6px 2px 12px; font-size: 12.5px;
}
.task-count { color: var(--color-text-muted); margin-right: 4px; }
.quick-select {
  border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12.5px; background: var(--color-surface);
}
.quick-icon-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 6px;
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; text-decoration: none; color: var(--color-text); font-size: 13px;
}
.quick-icon-btn:hover { background: #eef1f7; }
</style>
