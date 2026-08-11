<script setup>
import { computed, reactive, ref } from 'vue'
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

// --- Создание пользователя ---
const showCreateForm = ref(false)
const createError = ref('')
const creating = ref(false)
const newUser = reactive({ login: '', name: '', email: '', globalRole: 'user', password: '' })

// --- Показ временного пароля (после создания или сброса) ---
const temporaryPasswordInfo = ref(null) // { login, password }

function resetCreateForm() {
  newUser.login = ''
  newUser.name = ''
  newUser.email = ''
  newUser.globalRole = 'user'
  newUser.password = ''
  createError.value = ''
}

function openCreateForm() {
  resetCreateForm()
  showCreateForm.value = true
}

async function submitCreateUser() {
  createError.value = ''
  if (!newUser.login.trim() || !newUser.name.trim() || !newUser.email.trim()) {
    createError.value = 'Логин, имя и email обязательны'
    return
  }
  creating.value = true
  try {
    const created = await usersStore.createUser({
      login: newUser.login.trim(),
      name: newUser.name.trim(),
      email: newUser.email.trim(),
      globalRole: newUser.globalRole,
      password: newUser.password.trim() || undefined,
    })
    showCreateForm.value = false
    temporaryPasswordInfo.value = { login: created.login, password: created.temporaryPassword }
  } catch (err) {
    const detailMsg = err?.payload?.details?.map((d) => d.msg).join('; ')
    createError.value = detailMsg || err?.message || 'Не удалось создать пользователя'
  } finally {
    creating.value = false
  }
}

const resettingId = ref(null)

async function handleResetPassword(user) {
  resettingId.value = user.id
  try {
    const result = await usersStore.resetPassword(user.id)
    temporaryPasswordInfo.value = { login: user.login || user.email, password: result.temporaryPassword }
  } finally {
    resettingId.value = null
  }
}

function closePasswordModal() {
  temporaryPasswordInfo.value = null
}
</script>

<template>
  <div class="view-header users-header">
    <h2>Пользователи</h2>
    <button v-if="isAdmin" class="btn btn-sm btn-primary" @click="openCreateForm">+ Новый пользователь</button>
  </div>

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
        <span>Действия</span>
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

        <button
          class="btn btn-sm btn-ghost"
          :disabled="resettingId === u.id"
          @click="handleResetPassword(u)"
        >
          {{ resettingId === u.id ? 'Сброс...' : 'Сбросить пароль' }}
        </button>
      </div>
    </div>
  </section>

  <section v-else class="card users-section">
    <p class="hint-text">Доступ только для администраторов.</p>
  </section>

  <!-- Модалка создания пользователя -->
  <div v-if="showCreateForm" class="modal-backdrop" @click.self="showCreateForm = false">
    <div class="modal-card">
      <h3>Новый пользователь</h3>
      <label class="field">
        <span>Логин</span>
        <input v-model="newUser.login" type="text" placeholder="ivanov" />
      </label>
      <label class="field">
        <span>Имя</span>
        <input v-model="newUser.name" type="text" placeholder="Иван Иванов" />
      </label>
      <label class="field">
        <span>Email</span>
        <input v-model="newUser.email" type="email" placeholder="ivanov@example.com" />
      </label>
      <label class="field">
        <span>Роль</span>
        <select v-model="newUser.globalRole">
          <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
        </select>
      </label>
      <label class="field">
        <span>Пароль (необязательно — иначе сгенерируется)</span>
        <input v-model="newUser.password" type="text" placeholder="минимум 8 символов" />
      </label>
      <p v-if="createError" class="error-text">{{ createError }}</p>
      <div class="modal-actions">
        <button class="btn btn-sm btn-ghost" @click="showCreateForm = false">Отмена</button>
        <button class="btn btn-sm btn-primary" :disabled="creating" @click="submitCreateUser">
          {{ creating ? 'Создание...' : 'Создать' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Модалка показа временного пароля -->
  <div v-if="temporaryPasswordInfo" class="modal-backdrop" @click.self="closePasswordModal">
    <div class="modal-card">
      <h3>Временный пароль</h3>
      <p class="hint-text">
        Сохраните и передайте пароль пользователю сейчас — повторно он не будет показан.
      </p>
      <div class="password-box">
        <div><strong>Логин:</strong> {{ temporaryPasswordInfo.login }}</div>
        <div><strong>Пароль:</strong> <code>{{ temporaryPasswordInfo.password }}</code></div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-sm btn-primary" @click="closePasswordModal">Понятно</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.users-header { display: flex; align-items: center; justify-content: space-between; }
.users-section { padding: 16px 18px; }
.hint-text { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 14px; }

.users-table { display: flex; flex-direction: column; }
.users-table-head {
  display: grid; grid-template-columns: 1fr 180px 160px 160px; gap: 12px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted);
  padding: 0 8px 8px; border-bottom: 1px solid var(--color-border);
}
.user-row {
  display: grid; grid-template-columns: 1fr 180px 160px 160px; gap: 12px; align-items: center;
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

.modal-backdrop {
  position: fixed; inset: 0; background: rgba(20, 24, 34, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-card {
  background: #fff; border-radius: 10px; padding: 20px 22px; width: 360px;
  display: flex; flex-direction: column; gap: 10px;
}
.modal-card h3 { margin: 0 0 4px; font-size: 16px; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; }
.field input, .field select {
  border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 9px; font-size: 13px;
}
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 6px; }
.error-text { color: #d64545; font-size: 12px; margin: 0; }
.password-box {
  background: #f5f6fa; border-radius: 8px; padding: 10px 12px; font-size: 13px;
  display: flex; flex-direction: column; gap: 6px;
}
.password-box code { background: #eceef4; padding: 2px 6px; border-radius: 4px; }
</style>
