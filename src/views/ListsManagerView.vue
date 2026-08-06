<script setup>
import { ref, computed } from 'vue'
import { useListsStore } from '../stores/listsStore'
import { useUsersStore } from '../stores/usersStore'
import { useTasksStore } from '../stores/tasksStore'
import { ListRole } from '../domain/entities/enums'
import ListSettingsModal from '../components/common/ListSettingsModal.vue'

const listsStore = useListsStore()
const usersStore = useUsersStore()
const tasksStore = useTasksStore()

const showCreate = ref(false)
const editingList = ref(null)
const newListTitle = ref('')
const newListColor = ref('#4f7cff')
const memberPickerListId = ref(null)
const memberPickerUserId = ref(null)
const memberPickerRole = ref(ListRole.VIEWER)

const ROLE_LABEL = { owner: 'Владелец', editor: 'Редактор', assignee: 'Исполнитель', viewer: 'Наблюдатель' }
const ROLE_COLOR = { owner: '#e5484d', editor: '#4f7cff', assignee: '#1e9e4d', viewer: '#9aa3b2' }

const rows = computed(() => listsStore.lists.map((list) => ({
  list,
  members: listsStore.memberships[list.id] || [],
  taskCount: tasksStore.tasks.filter((t) => t.listId === list.id).length,
})))

async function createList() {
  if (!newListTitle.value.trim()) return
  await listsStore.createList({ title: newListTitle.value.trim(), color: newListColor.value })
  newListTitle.value = ''
  showCreate.value = false
}

function openMemberPicker(listId) {
  memberPickerListId.value = memberPickerListId.value === listId ? null : listId
  memberPickerUserId.value = null
  memberPickerRole.value = ListRole.VIEWER
}

async function addMember() {
  if (!memberPickerUserId.value) return
  await listsStore.addMember(memberPickerListId.value, memberPickerUserId.value, memberPickerRole.value)
  memberPickerListId.value = null
}

function availableUsers(listId) {
  const memberIds = new Set((listsStore.memberships[listId] || []).map((m) => m.userId))
  return usersStore.users.filter((u) => !memberIds.has(u.id))
}
</script>

<template>
  <div class="view-header">
    <div>
      <h2>Управление списками</h2>
      <p class="subtitle">Единая страница для создания списков, настройки доступа и параметров — вместо разрозненных настроек по каждому списку.</p>
    </div>
    <button class="btn btn-primary" @click="showCreate = !showCreate">+ Новый список</button>
  </div>

  <div v-if="showCreate" class="card create-form">
    <input v-model="newListTitle" placeholder="Название списка" @keyup.enter="createList" />
    <input v-model="newListColor" type="color" />
    <button class="btn btn-primary btn-sm" @click="createList">Создать</button>
  </div>

  <div class="lists-grid">
    <div v-for="row in rows" :key="row.list.id" class="card list-card">
      <div class="list-card-head">
        <span class="list-icon-badge" :style="{ background: row.list.color + '22', color: row.list.color }">
          {{ row.list.settings?.icon || '📋' }}
        </span>
        <div class="list-card-title">
          <strong>{{ row.list.title }}</strong>
          <span class="list-card-meta">{{ row.taskCount }} задач · {{ row.members.length }} участников</span>
        </div>
        <button class="btn btn-ghost btn-sm" @click="editingList = row.list">⚙️ Настроить</button>
      </div>

      <p v-if="row.list.description" class="list-card-desc">{{ row.list.description }}</p>

      <div v-if="row.list.settings?.recurringMeeting?.enabled" class="meeting-badge">
        📞 {{ row.list.settings.recurringMeeting.title || 'Регулярная встреча' }}
        <a v-if="row.list.settings.recurringMeeting.link" :href="row.list.settings.recurringMeeting.link" target="_blank" class="meeting-link">Ссылка</a>
      </div>

      <div class="members-section">
        <div class="members-row">
          <span v-for="m in row.members" :key="m.id" class="member-chip" :style="{ borderColor: ROLE_COLOR[m.role] }">
            <span class="mini-avatar">{{ usersStore.byId(m.userId)?.name?.charAt(0) || '?' }}</span>
            {{ usersStore.byId(m.userId)?.name || m.userId }}
            <select
              class="role-select" :value="m.role"
              :style="{ color: ROLE_COLOR[m.role] }"
              @change="listsStore.updateMemberRole(row.list.id, m.userId, $event.target.value)"
            >
              <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
            </select>
            <button class="chip-remove" @click="listsStore.removeMember(row.list.id, m.userId)">✕</button>
          </span>
          <button class="btn btn-ghost btn-sm add-member-btn" @click="openMemberPicker(row.list.id)">+ Участник</button>
        </div>

        <div v-if="memberPickerListId === row.list.id" class="member-picker">
          <select v-model="memberPickerUserId">
            <option :value="null" disabled>Выберите пользователя</option>
            <option v-for="u in availableUsers(row.list.id)" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
          <select v-model="memberPickerRole">
            <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="addMember">Добавить</button>
        </div>
      </div>
    </div>
  </div>

  <ListSettingsModal v-if="editingList" :list="editingList" @close="editingList = null" />
</template>

<style scoped>
.view-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 20px; }
.view-header h2 { margin: 0 0 4px; font-size: 19px; }
.subtitle { margin: 0; font-size: 12.5px; color: var(--color-text-muted); max-width: 480px; }
.create-form { padding: 14px; display: flex; gap: 8px; margin-bottom: 16px; align-items: center; }
.create-form input[type="text"], .create-form input:not([type]) { border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; flex: 1; }
.lists-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }
.list-card { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.list-card-head { display: flex; align-items: flex-start; gap: 10px; }
.list-icon-badge { width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.list-card-title { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.list-card-meta { font-size: 11.5px; color: var(--color-text-muted); }
.list-card-desc { margin: 0; font-size: 12.5px; color: var(--color-text-muted); }
.meeting-badge { font-size: 12px; background: #eef2ff; color: var(--color-primary-dark); border-radius: 8px; padding: 6px 10px; display: flex; align-items: center; gap: 8px; }
.meeting-link { color: var(--color-primary); font-weight: 600; text-decoration: none; }
.members-section { border-top: 1px solid var(--color-border); padding-top: 10px; }
.members-row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.member-chip {
  display: flex; align-items: center; gap: 5px; border: 1px solid var(--color-border); border-radius: 16px;
  padding: 3px 6px 3px 3px; font-size: 11.5px;
}
.mini-avatar { width: 18px; height: 18px; border-radius: 50%; background: var(--color-primary); color: #fff; font-size: 9px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.role-select { border: none; background: none; font-size: 10.5px; font-weight: 600; cursor: pointer; }
.chip-remove { border: none; background: none; cursor: pointer; color: var(--color-text-muted); font-size: 10px; padding: 0 2px; }
.add-member-btn { border-radius: 16px; }
.member-picker { display: flex; gap: 6px; margin-top: 8px; }
.member-picker select { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12px; }
</style>
