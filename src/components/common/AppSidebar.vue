<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useViewStore } from '../../stores/viewStore'
import { useUiStore } from '../../stores/uiStore'
import { useListsStore } from '../../stores/listsStore'
import { useMeetingsStore } from '../../stores/meetingsStore'
import { useIsAdmin } from '../../composables/usePermissions'
import { useDragReorder } from '../../composables/useDragReorder'
import AppIcon from './AppIcon.vue'

const viewStore = useViewStore()
const uiStore = useUiStore()
const listsStore = useListsStore()
const meetingsStore = useMeetingsStore()
const isAdmin = useIsAdmin()
const route = useRoute()

// Подменю со списками/встречами открыто по умолчанию, если пользователь уже находится
// на странице конкретного списка/встречи (прямой переход по URL / обновление страницы) —
// иначе после захода внутрь сайдбар выглядел бы так, будто раздел «потерялся».
const listsExpanded = ref(route.name === 'list-view')
const meetingsExpanded = ref(route.name === 'meeting-detail')

onMounted(async () => {
  if (!listsStore.loaded) await listsStore.load()
  if (!meetingsStore.loaded) await meetingsStore.load()
})

function toggleLists() {
  // В свёрнутом сайдбаре подменю не показываем — просто уходим в раздел
  // управления списками, иначе иконки без текста было бы невозможно читать.
  if (uiStore.sidebarCollapsed) return
  listsExpanded.value = !listsExpanded.value
}

function toggleMeetings() {
  if (uiStore.sidebarCollapsed) return
  meetingsExpanded.value = !meetingsExpanded.value
}

// Используется общая логика drag-n-drop с живым предпросмотром (useDragReorder) — та же,
// что и на страницах управления списками/встречами, чтобы сортировка в меню
// была синхронизирована с порядком на страницах.
const listsDrag = useDragReorder(
  () => listsStore.activeLists,
  (orderedIds) => listsStore.reorderLists(orderedIds),
)
const meetingsDrag = useDragReorder(
  () => meetingsStore.activeMeetings,
  (orderedIds) => meetingsStore.reorderMeetings(orderedIds),
)
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

      <div class="nav-item-group">
        <button
          class="nav-item nav-item-btn nav-item-expandable"
          :class="{ 'router-link-active': route.name === 'meetings' || route.name === 'meeting-detail' }"
          :title="uiStore.sidebarCollapsed ? 'Встречи' : ''"
          @click="toggleMeetings"
        >
          <router-link to="/meetings" class="nav-item-icon-link" @click.stop><AppIcon name="calendar" :size="15" /></router-link>
          <span v-if="!uiStore.sidebarCollapsed" class="nav-item-label">Встречи</span>
          <AppIcon
            v-if="!uiStore.sidebarCollapsed"
            :name="meetingsExpanded ? 'chevronDown' : 'chevronRight'"
            :size="12"
            class="expand-caret"
          />
        </button>

        <TransitionGroup
          v-if="meetingsExpanded && !uiStore.sidebarCollapsed"
          tag="div" name="fade" class="nav-submenu"
          @dragleave.self="meetingsDrag.dragOverEnd" @dragover.prevent @drop="meetingsDrag.endDrag"
        >
          <router-link
            v-for="m in meetingsDrag.displayItems.value" :key="m.id"
            :to="`/meetings/${m.id}`" class="nav-item nav-subitem fade-move"
            :class="{ dragging: meetingsDrag.draggingId.value === m.id }"
            draggable="true"
            @dragstart="meetingsDrag.startDrag(m.id)"
            @dragenter.prevent="meetingsDrag.dragOver(m.id)"
            @dragover.prevent
            @dragend="meetingsDrag.cancelDrag"
            @drop.stop="meetingsDrag.endDrag"
          >
            <span class="list-dot" :style="{ background: m.color || '#4f7cff' }" />
            <span class="nav-item-label">{{ m.title }}</span>
          </router-link>
          <div v-if="!meetingsDrag.displayItems.value.length" class="nav-submenu-empty">Встреч пока нет</div>
          <router-link to="/meetings" class="nav-item nav-subitem nav-manage-item">
            <AppIcon name="list" :size="13" /><span class="nav-item-label">Все встречи</span>
          </router-link>
        </TransitionGroup>
      </div>

      <div class="nav-item-group">
        <button
          class="nav-item nav-item-btn nav-item-expandable"
          :class="{ 'router-link-active': route.name === 'lists-manager' || route.name === 'list-view' }"
          :title="uiStore.sidebarCollapsed ? 'Списки' : ''"
          @click="toggleLists"
        >
          <AppIcon name="folder" :size="15" />
          <span v-if="!uiStore.sidebarCollapsed" class="nav-item-label">Списки</span>
          <AppIcon
            v-if="!uiStore.sidebarCollapsed"
            :name="listsExpanded ? 'chevronDown' : 'chevronRight'"
            :size="12"
            class="expand-caret"
          />
        </button>

        <TransitionGroup
          v-if="listsExpanded && !uiStore.sidebarCollapsed"
          tag="div" name="fade" class="nav-submenu"
          @dragleave.self="listsDrag.dragOverEnd" @dragover.prevent @drop="listsDrag.endDrag"
        >
          <router-link
            v-for="list in listsDrag.displayItems.value" :key="list.id"
            :to="`/lists/${list.id}`" class="nav-item nav-subitem fade-move"
            :class="{ dragging: listsDrag.draggingId.value === list.id }"
            draggable="true"
            @dragstart="listsDrag.startDrag(list.id)"
            @dragenter.prevent="listsDrag.dragOver(list.id)"
            @dragover.prevent
            @dragend="listsDrag.cancelDrag"
            @drop.stop="listsDrag.endDrag"
          >
            <span class="list-dot" :style="{ background: list.color }" />
            <span class="nav-item-label">{{ list.title }}</span>
          </router-link>
          <div v-if="!listsDrag.displayItems.value.length" class="nav-submenu-empty">Списков пока нет</div>
          <router-link to="/lists-manager" class="nav-item nav-subitem nav-manage-item">
            <AppIcon name="settings" :size="13" /><span class="nav-item-label">Управление списками</span>
          </router-link>
        </TransitionGroup>
      </div>

      <router-link to="/history" class="nav-item" :title="uiStore.sidebarCollapsed ? 'История' : ''">
        <AppIcon name="history" :size="15" /><span v-if="!uiStore.sidebarCollapsed">История</span>
      </router-link>
    </nav>

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
.nav-item-icon-link { display: flex; color: inherit; }
.list-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nav-item-btn { cursor: pointer; }

.nav-item-group { display: flex; flex-direction: column; }
.nav-item-expandable { justify-content: flex-start; }
.nav-item-label { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.expand-caret { flex-shrink: 0; color: var(--color-text-muted); }
.nav-submenu { display: flex; flex-direction: column; gap: 1px; padding-left: 14px; margin-top: 1px; margin-bottom: 2px; min-height: 4px; }
.nav-subitem { font-size: 12.5px; padding: 6px 10px; cursor: grab; }
.nav-subitem.dragging { opacity: 0.35; }
.nav-submenu-empty { font-size: 11.5px; color: var(--color-text-muted); padding: 5px 10px 5px 24px; }
.nav-manage-item { color: var(--color-text-muted); border-top: 1px solid var(--color-border); margin-top: 3px; padding-top: 7px; cursor: pointer; }

.sidebar-bottom {
  margin-top: auto; padding-top: 10px; border-top: 1px solid var(--color-border);
  display: flex; flex-direction: column; gap: 2px;
}
</style>
