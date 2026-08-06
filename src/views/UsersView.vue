<script setup>
import { computed } from 'vue'
import { useUsersStore } from '../stores/usersStore'
import { useIsAdmin } from '../composables/usePermissions'

const usersStore = useUsersStore()
const isAdmin = useIsAdmin()

const sortedUsers = computed(() =>
  [...usersStore.users].sort((a, b) => a.name.localeCompare(b.name, 'ru')),
)

function isSelf(user) {
  return usersStore.currentUser?.id === user.id
}

async function setRole(user, globalRole) {
  if (isSelf(user)) return
  await usersStore.updateUser(user.id, { globalRole })
}

async function toggleActive(user) {
  if (isSelf(user)) return
  await usersStore.updateUser(user.id, { isActive: !user.isActive })
}

const ROLE_LABEL = { admin: 'Администратор', user: 'Пользователь' }
</script>

<template>
  <div class="view-header"><h2>Пользователи</h2></div>

  <section v-if="isAdmin" class="card users-section">
    <p class="hint-text">
      Управление ролями и активностью пользователей. Изменение своей собственной роли
      или активности заблокировано — это защищает от случайной потери прав администратора.
    </p>

    <div class="users-table">
      <div class="users-table-head">
        <span>Пользователь</span>
        <span>Роль</span>
        <span>Статус</span>
      </div>
      <div v-for="u in sortedUsers" :key="u.id" class="user-row" :class="{ inactive: !u.isActive }">
        <div class="user-cell">
          <span class="user-avatar">{{ u.name.charAt(0) }}</span>
          <div class="user-info">
            <span class="user-name">{{ u.name }}<span v-if="isSelf(u)" class="self-badge">Вы</span></span>
            <span class="user-email">{{ u.email }}</span>
          </div>
        </div>

        <select
          class="role-select"
          :value="u.globalRole"
          :disabled="isSelf(u)"
          :title="isSelf(u) ? 'Нельзя изменить собственную роль' : ''"
          @change="setRole(u, $event.target.value)"
        >
          <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
        </select>

        <button
          class="btn btn-sm status-btn"
          :class="u.isActive ? 'btn-ghost' : 'btn-danger'"
          :disabled="isSelf(u)"
          :title="isSelf(u) ? 'Нельзя деактивировать самого себя' : ''"
          @click="toggleActive(u)"
        >
          {{ u.isActive ? 'Активен' : 'Деактивирован' }}
        </button>
      </div>
    </div>
  </section>

  <section v-else class="card users-section">
    <p class="hint-text">Доступ только для администраторов.</p>
  </section>
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.users-section { padding: 16px 18px; }
.hint-text { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 14px; }

.users-table { display: flex; flex-direction: column; }
.users-table-head {
  display: grid; grid-template-columns: 1fr 180px 160px; gap: 12px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted);
  padding: 0 8px 8px; border-bottom: 1px solid var(--color-border);
}
.user-row {
  display: grid; grid-template-columns: 1fr 180px 160px; gap: 12px; align-items: center;
  padding: 10px 8px; border-bottom: 1px solid var(--color-border);
}
.user-row.inactive { opacity: 0.55; }
.user-cell { display: flex; align-items: center; gap: 10px; }
.user-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: #b7bfd1; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.user-info { display: flex; flex-direction: column; }
.user-name { font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.self-badge {
  font-size: 10px; font-weight: 700; background: #eef1f7; color: var(--color-text-muted);
  padding: 1px 6px; border-radius: 10px;
}
.user-email { font-size: 12px; color: var(--color-text-muted); }
.role-select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 9px; font-size: 12.5px; }
.role-select:disabled { opacity: 0.6; cursor: not-allowed; }
.status-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
