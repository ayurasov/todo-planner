<script setup>
import { ref } from 'vue'
import { useUsersStore } from '../../stores/usersStore'
import QuickCreateModal from '../task/QuickCreateModal.vue'

const usersStore = useUsersStore()
const showCreate = ref(false)
const search = ref('')
</script>

<template>
  <header class="topbar">
    <input v-model="search" class="search-input" type="text" placeholder="Поиск задач..." />
    <div class="topbar-actions">
      <button class="btn btn-primary" @click="showCreate = true">+ Создать задачу</button>
      <div v-if="usersStore.currentUser" class="current-user">
        {{ usersStore.currentUser.name }}
      </div>
    </div>
  </header>
  <QuickCreateModal v-if="showCreate" @close="showCreate = false" />
</template>

<style scoped>
.topbar {
  height: 56px; flex-shrink: 0; display: flex; align-items: center; gap: 16px;
  padding: 0 24px; border-bottom: 1px solid var(--color-border); background: var(--color-surface);
}
.search-input {
  flex: 1; max-width: 360px; border: 1px solid var(--color-border); border-radius: var(--radius-sm);
  padding: 7px 12px; outline: none;
}
.search-input:focus { border-color: var(--color-primary); }
.topbar-actions { display: flex; align-items: center; gap: 14px; margin-left: auto; }
.current-user { font-size: 13px; color: var(--color-text-muted); }
</style>
