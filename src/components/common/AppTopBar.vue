<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUsersStore } from '../../stores/usersStore'
import { useTasksStore } from '../../stores/tasksStore'
import { useListsStore } from '../../stores/listsStore'
import { useUiStore } from '../../stores/uiStore'
import { useNotificationsStore } from '../../stores/notificationsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { PRIORITY_LABEL } from '../../domain/entities/enums'
import { relativeDay, isOverdue } from '../../utils/formatters'
import { getInitials, getAvatarColor } from '../../utils/avatar'
import QuickCreateModal from '../task/QuickCreateModal.vue'
import NotificationsPanel from '../notifications/NotificationsPanel.vue'
import ProfileModal from './ProfileModal.vue'
import AppIcon from './AppIcon.vue'
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

const STATUS_LABEL = { open: 'Не начато', in_progress: 'В работе', done: 'Выполнено', cancelled: 'Отменено' }

useClickOutside(searchWrapEl, () => { searchFocused.value = false })

const searchResults = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return []
  return tasksStore.tasks
    .filter((t) => t.title.toLowerCase().includes(q))
    .slice(0, 12)
    .map((t) => ({
      task: t,
      list: listsStore.byId(t.listId),
      assignee: usersStore.byId(t.assigneeId),
      overdue: isOverdue(t.dueDate, t.status),
    }))
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
    const meeting = meetingsStore.meetingById(route.params.id)
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
      <span class="search-icon"><AppIcon name="search" :size="14" /></span>
      <input
        v-model="search" class="search-input" type="text" placeholder="Поиск задач..."
        @focus="searchFocused = true"
      />
      <button v-if="search" class="search-clear" @click="search = ''"><AppIcon name="close" :size="12" /></button>

      <div v-if="searchFocused && search" class="search-dropdown card scroll-thin">
        <button v-for="r in searchResults" :key="r.task.id" class="search-result" @click="pickResult(r.task)">
          <div class="result-top">
            <span class="result-title">{{ r.task.title }}</span>
            <span class="result-status" :class="`status-${r.task.status}`">{{ STATUS_LABEL[r.task.status] }}</span>
          </div>
          <div class="result-meta">
            <span v-if="r.list" class="result-list" :style="{ color: r.list.color }">{{ r.list.title }}</span>
            <span class="badge" :class="`badge-${r.task.priority}`">{{ PRIORITY_LABEL[r.task.priority] }}</span>
            <span v-if="r.task.dueDate" class="result-due" :class="{ overdue: r.overdue }">
              <AppIcon name="calendar" :size="11" />{{ relativeDay(r.task.dueDate) }}
            </span>
            <span v-if="r.assignee" class="result-assignee">
              <span class="result-avatar" :style="{ background: getAvatarColor(r.assignee.name) }">{{ getInitials(r.assignee.name) }}</span>
              {{ r.assignee.name }}
            </span>
          </div>
        </button>
        <div v-if="!searchResults.length" class="search-empty">Ничего не найдено по «{{ search }}»</div>
      </div>
    </div>

    <div class="topbar-actions">
      <button class="btn btn-primary" @click="openCreate"><AppIcon name="plus" :size="14" /> Создать задачу</button>

      <div class="notif-wrap">
        <button class="icon-btn" title="Уведомления" @click="notifOpen = !notifOpen">
          <AppIcon name="bell" :size="16" />
          <span v-if="notificationsStore.unreadCount" class="notif-dot">{{ notificationsStore.unreadCount }}</span>
        </button>
        <NotificationsPanel v-if="notifOpen" @close="notifOpen = false" />
      </div>

      <button v-if="usersStore.currentUser" class="current-user" title="Открыть профиль" @click="uiStore.openProfile()">
        <img v-if="usersStore.currentUser.avatarUrl" :src="usersStore.currentUser.avatarUrl" class="current-user-avatar" alt="" />
        <span v-else class="current-user-avatar current-user-avatar-fallback" :style="{ background: getAvatarColor(usersStore.currentUser.name) }">
          {{ getInitials(usersStore.currentUser.name) }}
        </span>
        <span class="current-user-name">{{ usersStore.currentUser.name }}</span>
      </button>
    </div>
  </header>
  <QuickCreateModal v-if="uiStore.quickCreateContext" :context="uiStore.quickCreateContext" @close="uiStore.closeQuickCreate()" />
  <ProfileModal v-if="uiStore.profileModalOpen" @close="uiStore.closeProfile()" />
</template>

<style scoped>
.topbar {
  height: 56px; flex-shrink: 0; display: flex; align-items: center; gap: 16px;
  padding: 0 24px; border-bottom: 1px solid var(--color-border); background: var(--color-surface);
}
.search-wrap { position: relative; flex: 1; max-width: 640px; }
.search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--color-text-muted); display: flex; }
.search-input {
  width: 100%; border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  padding: 7px 30px 7px 32px; outline: none;
}
.search-input:focus { border-color: var(--color-primary); }
.search-clear { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); border: none; background: none; cursor: pointer; color: var(--color-text-muted); display: flex; }
.search-dropdown {
  position: absolute; top: calc(100% + 6px); left: 0; width: 100%; max-height: 420px; overflow-y: auto;
  padding: 6px; z-index: 50; box-shadow: var(--shadow-2);
}
.search-result { display: flex; flex-direction: column; gap: 5px; width: 100%; text-align: left; border: none; background: none; padding: 9px 12px; border-radius: 8px; cursor: pointer; border-bottom: 1px solid var(--color-border); }
.search-result:last-child { border-bottom: none; }
.search-result:hover { background: #f1f3f9; }
.result-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.result-title { font-size: 13.5px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-status { font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 10px; background: #eef1f7; color: var(--color-text-muted); flex-shrink: 0; }
.result-status.status-in_progress { background: #eaf0ff; color: #4f7cff; }
.result-status.status-done { background: #e4f6ea; color: #1e9e4d; }
.result-status.status-cancelled { background: #f1f2f5; color: #9aa3b2; }
.result-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 11.5px; color: var(--color-text-muted); }
.result-list { font-weight: 600; }
.result-due { display: flex; align-items: center; gap: 4px; }
.result-due.overdue { color: var(--color-danger); font-weight: 600; }
.result-assignee { display: flex; align-items: center; gap: 5px; }
.result-avatar { width: 16px; height: 16px; border-radius: 50%; color: #fff; font-size: 8px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.search-empty { padding: 14px; font-size: 12.5px; color: var(--color-text-muted); text-align: center; }
.topbar-actions { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.icon-btn { border: none; background: none; cursor: pointer; position: relative; color: var(--color-text-muted); padding: 4px; display: flex; align-items: center; }
.icon-btn:hover { color: var(--color-text); }
.notif-wrap { position: relative; }
.notif-dot {
  position: absolute; top: -3px; right: -3px; background: var(--color-danger); color: #fff; font-size: 9px;
  font-weight: 700; border-radius: 8px; padding: 1px 4px; min-width: 14px; text-align: center;
}
.current-user {
  display: flex; align-items: center; gap: 8px; border: none; background: none; cursor: pointer;
  padding: 4px 8px 4px 4px; border-radius: 20px; transition: background 0.15s;
}
.current-user:hover { background: #f1f3f9; }
.current-user-avatar { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; display: block; flex-shrink: 0; }
.current-user-avatar-fallback { color: #fff; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.current-user-name { font-size: 13px; font-weight: 600; color: var(--color-text); }
</style>
