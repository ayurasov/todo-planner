<script setup>
import { useListsStore } from '../../stores/listsStore'
import { useViewStore } from '../../stores/viewStore'
import { useUiStore } from '../../stores/uiStore'
import { useIsAdmin } from '../../composables/usePermissions'
import AppIcon from './AppIcon.vue'

const listsStore = useListsStore()
const viewStore = useViewStore()
const uiStore = useUiStore()
const isAdmin = useIsAdmin()
</script>

<template>
  <aside class="sidebar scroll-thin" :class="{ collapsed: uiStore.sidebarCollapsed }">
    <div class="sidebar-top">
      <div class="sidebar-logo">
        <AppIcon name="checklist" :size="18" />
        <span v-if="!uiStore.sidebarCollapsed">Планировщик</span>
      </div>
      <button class="collapse-btn" :title="uiStore.sidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'" @click="uiStore.toggleSidebar()">
        <AppIcon :name="uiStore.sidebarCollapsed ? 'chevronRight' : 'chevronLeft'" :size="14" />
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/my-tasks" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Мои задачи' : ''">
        <AppIcon name="home" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Мои задачи</span>
      </router-link>
      <router-link to="/team-tasks" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Задачи команды' : ''">
        <AppIcon name="team" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Задачи команды</span>
      </router-link>
      <router-link to="/meetings" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Встречи' : ''">
        <AppIcon name="calendar" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Встречи</span>
      </router-link>
      <router-link to="/lists-manager" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Списки' : ''">
        <AppIcon name="folder" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Списки</span>
      </router-link>
      <router-link to="/recurring" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Повторяющиеся' : ''">
        <AppIcon name="repeat" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Повторяющиеся</span>
      </router-link>
      <router-link to="/history" class="nav-item" :title="uiStore.sidebarCollapsed ? 'История' : ''">
        <AppIcon name="history" :size="15" /><span v-if="!uiStore.sidebarCollapsed">История</span>
      </router-link>
    </nav>

    <div class="sidebar-section">
      <div v-if="!uiStore.sidebarCollapsed" class="sidebar-section-title">
        Мои списки
        <router-link to="/lists-manager" class="manage-link" title="Управление списками"><AppIcon name="settings" :size="12" /></router-link>
      </div>
      <router-link
        v-for="list in listsStore.lists"
        :key="list.id"
        :to="`/lists/${list.id}`"
        class="nav-item nav-item-list"
        :title="uiStore.sidebarCollapsed ? list.title : ''"
      >
        <span class="list-dot" :style="{ background: list.color }" />
        <span v-if="!uiStore.sidebarCollapsed">{{ list.title }}</span>
      </router-link>
    </div>

    <div v-if="viewStore.savedViews.length" class="sidebar-section">
      <div v-if="!uiStore.sidebarCollapsed" class="sidebar-section-title">Сохранённые представления</div>
      <button
        v-for="v in viewStore.savedViews" :key="v.id" class="nav-item nav-item-btn"
        :title="uiStore.sidebarCollapsed ? v.name : ''"
        @click="viewStore.applyView(v)"
      >
        <AppIcon name="star" :size="15" /><span v-if="!uiStore.sidebarCollapsed">{{ v.name }}</span>
      </button>
    </div>

    <div class="sidebar-bottom">
      <router-link v-if="isAdmin" to="/settings/users" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Пользователи' : ''">
        <AppIcon name="shield" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Пользователи</span>
      </router-link>
      <router-link to="/settings" class="nav-item" :title="uiStore.sidebarCollapsed ? 'Настройки' : ''">
        <AppIcon name="settings" :size="15" /><span v-if="!uiStore.sidebarCollapsed">Настройки</span>
      </router-link>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 232px; background: var(--color-surface); border-right: 1px solid var(--color-border);
  display: flex; flex-direction: column; padding: 16px 10px; overflow-y: auto; overflow-x: hidden;
  transition: width 0.18s ease; flex-shrink: 0;
}
.sidebar.collapsed { width: 60px; padding: 16px 8px; }
.sidebar-top { display: flex; align-items: center; justify-content: space-between; padding: 4px 6px 16px; gap: 6px; }
.sidebar.collapsed .sidebar-top { flex-direction: column; gap: 10px; }
.sidebar-logo { font-weight: 700; font-size: 15px; display: flex; align-items: center; gap: 8px; white-space: nowrap; overflow: hidden; }
.collapse-btn {
  border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 7px; width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--color-text-muted); flex-shrink: 0;
}
.collapse-btn:hover { background: #eef1f7; color: var(--color-text); }
.sidebar-nav { display: flex; flex-direction: column; gap: 2px; margin-bottom: 12px; }
.sidebar-section { margin-top: 10px; }
.sidebar-section-title { font-size: 11px; color: var(--color-text-muted); padding: 4px 10px; text-transform: uppercase; letter-spacing: 0.04em; display: flex; align-items: center; justify-content: space-between; white-space: nowrap; }
.manage-link { text-decoration: none; opacity: 0.7; display: flex; align-items: center; }
.manage-link:hover { opacity: 1; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 10px; border-radius: var(--radius-sm); font-size: 13px;
  color: var(--color-text); text-decoration: none; border: none; background: none;
  text-align: left; width: 100%; white-space: nowrap; overflow: hidden;
}
.sidebar.collapsed .nav-item { justify-content: center; padding: 8px; }
.nav-item:hover { background: #eef1f7; }
.nav-item.router-link-active { background: #e6ecff; color: var(--color-primary-dark); font-weight: 600; }
.list-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nav-item-btn { cursor: pointer; }
.sidebar-bottom {
  margin-top: auto; padding-top: 10px; border-top: 1px solid var(--color-border);
  display: flex; flex-direction: column; gap: 2px;
}
</style>
