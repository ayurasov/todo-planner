<script setup>
import { ref, computed, nextTick } from 'vue'
import { useClickOutside } from '../../composables/useClickOutside'
import AppIcon from './AppIcon.vue'

// Мультиселект пользователей с выпадающим списком и поиском, идентичный
// по паттерну дропдауну исполнителя в задачах (TaskRow.vue/TaskDetailPanel.vue):
// список рендерится через Teleport в body и позиционируется абсолютно
// по экранным координатам кнопки-триггера. Это гарантирует, что открытие
// списка никогда не меняет размер родительского окна/модалки и не вызывает
// появление скроллбара — список просто "плавает" поверх всего интерфейса.
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  users: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Добавить участника' },
  emptyHint: { type: String, default: 'Никого не выбрано' },
  chipClass: { type: String, default: 'attendee-chip' },
  avatarClass: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const search = ref('')
const triggerEl = ref(null)
const dropdownEl = ref(null)
const dropdownPos = ref({ top: 0, left: 0, width: 220 })

useClickOutside(dropdownEl, () => { open.value = false }, triggerEl)

function byId(id) {
  return props.users.find((u) => u.id === id)
}

const available = computed(() => {
  const selected = new Set(props.modelValue)
  const q = search.value.trim().toLowerCase()
  return props.users
    .filter((u) => !u.is_system)          // Скрываем системных пользователей
    .filter((u) => !selected.has(u.id))
    .filter((u) => !q || u.name.toLowerCase().includes(q))
})

function toggleOpen() {
  if (open.value) {
    open.value = false
    return
  }
  const margin = 8
  const rect = triggerEl.value.getBoundingClientRect()
  const dropdownW = Math.max(rect.width, 240)
  const estimatedH = Math.min(280, 48 + available.value.length * 34)
  let left = rect.left
  left = Math.min(Math.max(margin, left), window.innerWidth - dropdownW - margin)
  let top = rect.bottom + 4
  if (top + estimatedH > window.innerHeight - margin) {
    top = Math.max(margin, rect.top - estimatedH - 4)
  }
  dropdownPos.value = { top, left, width: dropdownW }
  search.value = ''
  open.value = true
  nextTick(() => dropdownEl.value?.querySelector('input')?.focus())
}

function add(userId) {
  emit('update:modelValue', [...props.modelValue, userId])
  search.value = ''
}

function remove(userId) {
  emit('update:modelValue', props.modelValue.filter((id) => id !== userId))
}
</script>

<template>
  <div class="user-multiselect">
    <button ref="triggerEl" type="button" class="assignee-trigger" @click="toggleOpen">
      <span class="assignee-avatar empty"><AppIcon name="plus" :size="10" /></span>
      <span>{{ placeholder }}</span>
      <span class="chevron"><AppIcon name="chevronDown" :size="10" /></span>
    </button>

    <!-- Место под тэги зарезервировано всегда (min-height), чтобы добавление
         первого участника не сдвигало последующие поля формы вниз скачком. -->
    <div class="selected-tags" :class="{ 'is-empty': !modelValue.length }">
      <template v-if="modelValue.length">
        <span v-for="uid in modelValue" :key="uid" class="member-chip" :class="chipClass">
          <span class="mini-avatar" :class="avatarClass">{{ byId(uid)?.name?.charAt(0) || '?' }}</span>
          {{ byId(uid)?.name || uid }}
          <button type="button" class="chip-remove" @click="remove(uid)"><AppIcon name="close" :size="10" /></button>
        </span>
      </template>
      <span v-else class="selected-tags-placeholder">{{ emptyHint }}</span>
    </div>

    <Teleport to="body">
      <div
        v-if="open"
        ref="dropdownEl"
        class="assignee-dropdown card scroll-thin"
        :style="{ top: `${dropdownPos.top}px`, left: `${dropdownPos.left}px`, width: `${dropdownPos.width}px` }"
        @click.stop
      >
        <div class="assignee-search-wrap">
          <input v-model="search" class="assignee-search-input" placeholder="Поиск пользователя..." @keyup.escape="open = false" />
        </div>
        <template v-if="available.length">
          <button v-for="u in available" :key="u.id" type="button" class="assignee-option" @click="add(u.id)">
            <span class="assignee-avatar">{{ u.name.charAt(0) }}</span>{{ u.name }}
          </button>
        </template>
        <div v-else class="assignee-no-results">Пользователи не найдены</div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.user-multiselect { position: relative; display: flex; flex-direction: column; }
.assignee-trigger {
  display: flex; align-items: center; gap: 7px; border: 1px solid var(--color-border); background: var(--color-surface);
  border-radius: 8px; padding: 6px 10px 6px 5px; font-size: 12.5px; cursor: pointer; width: 100%;
}
.assignee-trigger:hover { background: var(--color-surface-offset); }
.assignee-avatar {
  width: 22px; height: 22px; border-radius: 50%; background: var(--color-primary); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 700; flex-shrink: 0;
}
.assignee-avatar.empty { background: var(--color-surface-offset); color: var(--color-text-muted); }
.chevron { color: var(--color-text-muted); display: flex; margin-left: auto; }

/* Зарезервированное место под тэги: даже без выбранных участников блок
   занимает свою строку высотой в один ряд чипов, поэтому раскрытие/схлопывание
   списка тэгов не двигает остальную форму. */
.selected-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 8px; min-height: 26px; }
.selected-tags-placeholder { font-size: 12px; color: var(--color-text-faint); }
.member-chip { display: inline-flex; align-items: center; gap: 6px; background: #f4f0ff; color: #7c5cd6; border-radius: 20px; padding: 3px 8px 3px 4px; font-size: 12.5px; font-weight: 500; }
.editor-chip { background: #eef2ff; color: var(--color-primary-dark); }
.mini-avatar { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 50%; background: #7c5cd6; color: #fff; font-size: 10px; font-weight: 700; flex-shrink: 0; }
.mini-avatar-editor { background: var(--color-primary); }
.chip-remove { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; color: currentColor; }

.assignee-dropdown {
  position: fixed; z-index: 1000; padding: 6px 0 4px; max-height: 280px; overflow-y: auto;
  box-shadow: var(--shadow-2); background: var(--color-surface); border-radius: 10px; border: 1px solid var(--color-border);
}
.assignee-search-wrap { padding: 4px 8px 6px; }
.assignee-search-input { width: 100%; border: 1px solid var(--color-border); border-radius: 7px; padding: 5px 9px; font-size: 12.5px; outline: none; background: var(--color-surface-offset); }
.assignee-search-input:focus { border-color: var(--color-primary); background: #fff; }
.assignee-option { display: flex; align-items: center; gap: 8px; width: 100%; text-align: left; border: none; background: none; padding: 6px 12px; font-size: 12.5px; cursor: pointer; }
.assignee-option:hover { background: var(--color-surface-offset); }
.assignee-no-results { padding: 6px 12px; font-size: 12px; color: var(--color-text-muted); }
</style>
