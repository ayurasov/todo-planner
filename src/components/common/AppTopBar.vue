<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUsersStore } from '../../stores/usersStore'
import { useTasksStore } from '../../stores/tasksStore'
import { useListsStore } from '../../stores/listsStore'
import { useUiStore } from '../../stores/uiStore'
import { useNotificationsStore } from '../../stores/notificationsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import QuickCreateModal from '../task/QuickCreateModal.vue'
import NotificationsPanel from '../notifications/NotificationsPanel.vue'
import { useClickOutside } from '../../composables/useClickOutside'

const usersStore = useUsersStore()
const tasksStore = useTasksStore()
const listsStore = useListsStore()
const uiStore = useUiStore()
const notificationsStore = useNotificationsStore()
const meetingsStore = useMeetingsStore()
const route = useRoute()

const search = ref('')
const searchFocused = ref(false)
const searchWrapEl = ref(null)
const notifOpen = ref(false)

useClickOutside(searchWrapEl, () => { searchFocused.value = false })

const searchResults = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return []
  return tasksStore.tasks
    .filter((t) => t.title.toLowerCase().includes(q))
    .slice(0, 8)
})

function pickResult(task) {
  uiStore.openTask(task.id)
  search.value = ''
  searchFocused.value = false
}

/**
 * Контекст для QuickCreateModal, зависящий от текущего маршрута.
 * - list-view: задача создаётся в открытый список (listId)
 * - meeting-detail: задача создаётся привязанной к открытой встрече (meetingId),
 *   а также подтягивает listId встречи, если он задан в meetingsStore, чтобы
 *   задача сразу попадала в правильный список, а не только в контекст встречи
 */
function contextForCreate() {
  if (route.name === 'list-view' && route.params.id) return { listId: route.params.id }
  if (route.name === 'meeting-detail' && route.params.id) {
    const meeting = meetingsStore.byId ? meetingsStore.byId(route.params.id) : null
    return { meetingId: route.params.id, listId: meeting?.listId || null }
  }
  return {}
}

function openCreate() {
  uiStore.openQuickCreate(contextForCreate())
}
</script>

<template>
  <header class="topbar">
    <div ref="searchWrapEl" class="search-wrap">
      <span class="search-icon">🔍</span>
      <input
        v-model="search" class="search-input" type="text" placeholder="Поиск задач..."
        @focus="searchFocused = true"
      />
      <button v-if="search" class="search-clear" @click="search = ''">✕</button>

      <div v-if="searchFocused && search" class="search-dropdown card scroll-thin">
        <button v-for="t in searchResults" :key="t.id" class="search-result" @click="pickResult(t)">
          <span class="result-title">{{ t.title }}</span>
          <span class="result-meta">{{ listsStore.byId(t.listId)?.title }}</span>
        </button>
        <div v-if="!searchResults.length" class="search-empty">Ничего не найдено по «{{ search }}»</div>
      </div>
    </div>

    <div class="topbar-actions">
      <button class="btn btn-primary" @click="openCreate">+ Создать задачу</button>

      <div class="notif-wrap">
        <button class="icon-btn" title="Уведомления" @click="notifOpen = !notifOpen">
          🔔
          <span v-if="notificationsStore.unreadCount" class="notif-dot">{{ notificationsStore.unreadCount }}</span>
        </button>
        <NotificationsPanel v-if="notifOpen" @close="notifOpen = false" />
      </div>

      <div v-if="usersStore.currentUser" class="current-user">
        {{ usersStore.currentUser.name }}
      </div>
    </div>
  </header>
  <QuickCreateModal v-if="uiStore.quickCreateContext" :context="uiStore.quickCreateContext" @close="uiStore.closeQuickCreate()" />
</template>

<style scoped>
.topbar {
  height: 56px; flex-shrink: 0; display: flex; align-items: center; gap: 16px;
  padding: 0 24px; border-bottom: 1px solid var(--color-border); background: var(--color-surface);
}
.search-wrap { position: relative; flex: 1; max-width: 380px; }
.search-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); font-size: 12px; color: var(--color-text-muted); }
.search-input {
  width: 100%; border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  padding: 7px 30px 7px 32px; outline: none;
}
.search-input:focus { border-color: var(--color-primary); }
.search-clear { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); border: none; background: none; cursor: pointer; color: var(--color-text-muted); font-size: 11px; }
.search-dropdown {
  position: absolute; top: calc(100% + 6px); left: 0; width: 100%; max-height: 320px; overflow-y: auto;
  padding: 6px; z-index: 50; box-shadow: var(--shadow-2);
}
.search-result { display: flex; flex-direction: column; gap: 1px; width: 100%; text-align: left; border: none; background: none; padding: 7px 10px; border-radius: 8px; cursor: pointer; }
.search-result:hover { background: #f1f3f9; }
.result-title { font-size: 13px; font-weight: 500; }
.result-meta { font-size: 11px; color: var(--color-text-muted); }
.search-empty { padding: 14px; text-align: center; font-size: 12.5px; color: var(--color-text-muted); }
.topbar-actions { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.icon-btn {
  position: relative; border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 8px;
  width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 15px;
}
.icon-btn:hover { background: #eef1f7; }
.notif-wrap { position: relative; }
.notif-dot {
  position: absolute; top: -4px; right: -4px; background: var(--color-danger); color: #fff; font-size: 10px; font-weight: 700;
  border-radius: 10px; min-width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; padding: 0 3px;
}
.current-user { font-size: 13px; color: var(--color-text-muted); }
</style>
