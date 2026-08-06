<script setup>
import { useListsStore } from '../../stores/listsStore'
import { useViewStore } from '../../stores/viewStore'

const listsStore = useListsStore()
const viewStore = useViewStore()
</script>

<template>
  <aside class="sidebar scroll-thin">
    <div class="sidebar-logo">📋 Планировщик</div>
    <nav class="sidebar-nav">
      <router-link to="/my-tasks" class="nav-item">🟢 Мои задачи</router-link>
      <router-link to="/team-tasks" class="nav-item">👥 Задачи команды</router-link>
      <router-link to="/meetings" class="nav-item">📅 Встречи</router-link>
      <router-link to="/recurring" class="nav-item">🔁 Повторяющиеся</router-link>
      <router-link to="/history" class="nav-item">🕘 История</router-link>
    </nav>

    <div class="sidebar-section">
      <div class="sidebar-section-title">
        Списки
        <router-link to="/lists-manager" class="manage-link" title="Управление списками">⚙️</router-link>
      </div>
      <router-link
        v-for="list in listsStore.lists"
        :key="list.id"
        :to="`/lists/${list.id}`"
        class="nav-item nav-item-list"
      >
        <span class="list-dot" :style="{ background: list.color }" />
        {{ list.title }}
      </router-link>
    </div>

    <div v-if="viewStore.savedViews.length" class="sidebar-section">
      <div class="sidebar-section-title">Сохранённые представления</div>
      <button v-for="v in viewStore.savedViews" :key="v.id" class="nav-item nav-item-btn" @click="viewStore.applyView(v)">
        ⭐ {{ v.name }}
      </button>
    </div>

    <router-link to="/settings" class="nav-item nav-item-bottom">⚙️ Настройки</router-link>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 232px; background: var(--color-surface); border-right: 1px solid var(--color-border);
  display: flex; flex-direction: column; padding: 16px 10px; overflow-y: auto;
}
.sidebar-logo { font-weight: 700; font-size: 15px; padding: 4px 10px 16px; }
.sidebar-nav { display: flex; flex-direction: column; gap: 2px; margin-bottom: 12px; }
.sidebar-section { margin-top: 10px; }
.sidebar-section-title { font-size: 11px; color: var(--color-text-muted); padding: 4px 10px; text-transform: uppercase; letter-spacing: 0.04em; display: flex; align-items: center; justify-content: space-between; }
.manage-link { text-decoration: none; font-size: 12px; opacity: 0.7; }
.manage-link:hover { opacity: 1; }
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; border-radius: var(--radius-sm); font-size: 13px;
  color: var(--color-text); text-decoration: none; border: none; background: none;
  text-align: left; width: 100%;
}
.nav-item:hover { background: #eef1f7; }
.nav-item.router-link-active { background: #e6ecff; color: var(--color-primary-dark); font-weight: 600; }
.list-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nav-item-bottom { margin-top: auto; }
.nav-item-btn { cursor: pointer; }
</style>
