<script setup>
import { ref, computed } from 'vue'
import { onClickOutside } from '@vueuse/core'
import AppIcon from './AppIcon.vue'

// Общий компонент для фильтра "мультиселект с поиском" — используется
// в шапке фильтров аналитики для выбора нескольких встреч/списков из большого набора.
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true }, // [{ id, label }]
  placeholder: { type: String, default: 'Выбрать...' },
  searchPlaceholder: { type: String, default: 'Поиск...' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const search = ref('')
const rootEl = ref(null)

onClickOutside(rootEl, () => { open.value = false })

const filteredOptions = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.options
  return props.options.filter((o) => o.label.toLowerCase().includes(q))
})

function toggle(id) {
  const next = props.modelValue.includes(id)
    ? props.modelValue.filter((x) => x !== id)
    : [...props.modelValue, id]
  emit('update:modelValue', next)
}

function clear() {
  emit('update:modelValue', [])
}

const summary = computed(() => {
  if (!props.modelValue.length) return props.placeholder
  if (props.modelValue.length === 1) {
    return props.options.find((o) => o.id === props.modelValue[0])?.label || props.placeholder
  }
  return `Выбрано: ${props.modelValue.length}`
})
</script>

<template>
  <div ref="rootEl" class="search-multiselect">
    <button type="button" class="ms-trigger" :class="{ 'has-value': modelValue.length }" @click="open = !open">
      <span class="ms-summary">{{ summary }}</span>
      <AppIcon name="chevronDown" :size="12" />
    </button>
    <div v-if="open" class="ms-dropdown card scroll-thin">
      <input v-model="search" class="ms-search" :placeholder="searchPlaceholder" @click.stop />
      <div class="ms-options scroll-thin">
        <label v-for="o in filteredOptions" :key="o.id" class="ms-option">
          <input type="checkbox" :checked="modelValue.includes(o.id)" @change="toggle(o.id)" />
          {{ o.label }}
        </label>
        <div v-if="!filteredOptions.length" class="ms-empty">Ничего не найдено</div>
      </div>
      <button v-if="modelValue.length" type="button" class="btn btn-ghost btn-sm ms-clear" @click="clear">Очистить</button>
    </div>
  </div>
</template>

<style scoped>
.search-multiselect { position: relative; min-width: 160px; }
.ms-trigger {
  width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 6px;
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 6px;
  padding: 6px 8px; font-size: 12.5px; cursor: pointer; color: var(--color-text-muted);
}
.ms-trigger.has-value { color: var(--color-text); border-color: #cfd8ff; background: #f5f7ff; }
.ms-summary { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ms-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; width: 240px; z-index: 50;
  padding: 8px; display: flex; flex-direction: column; gap: 6px;
}
.ms-search { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12.5px; }
.ms-options { max-height: 200px; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; }
.ms-option { display: flex; align-items: center; gap: 8px; font-size: 12.5px; padding: 4px 4px; cursor: pointer; border-radius: 5px; }
.ms-option:hover { background: #f2f4f9; }
.ms-empty { font-size: 12px; color: var(--color-text-muted); padding: 8px 4px; text-align: center; }
.ms-clear { align-self: flex-end; }
</style>
