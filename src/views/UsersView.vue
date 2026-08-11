<script setup>
import { computed, reactive, ref } from 'vue'
import { useUsersStore } from '../stores/usersStore'
import { useIsAdmin } from '../composables/usePermissions'

const usersStore = useUsersStore()
const isAdmin = useIsAdmin()

const ROLE_LABEL = { admin: 'Администратор', user: 'Пользователь' }

// --- Фильтрация и сортировка ---
const searchQuery = ref('')
const roleFilter = ref('all') // all | admin | user
const statusFilter = ref('all') // all | active | inactive
const departmentFilter = ref('all')
const sortBy = ref('name') // name | department | position | role | status
const sortDir = ref('asc') // asc | desc

const departments = computed(() => {
  const set = new Set(usersStore.users.map((u) => u.department).filter(Boolean))
  return [...set].sort((a, b) => a.localeCompare(b, 'ru'))
})

function isSelf(user) {
  return usersStore.currentUser?.id === user.id
}

const filteredSortedUsers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let list = usersStore.users.filter((u) => {
    if (q) {
      const hay = `${u.name} ${u.email} ${u.login || ''} ${u.position || ''} ${u.department || ''}`.toLowerCase()
      if (!hay.includes(q)) return false
    }
    if (roleFilter.value !== 'all' && u.globalRole !== roleFilter.value) return false
    if (statusFilter.value === 'active' && !u.isActive) return false
    if (statusFilter.value === 'inactive' && u.isActive) return false
    if (departmentFilter.value !== 'all' && u.department !== departmentFilter.value) return false
    return true
  })

  const dir = sortDir.value === 'asc' ? 1 : -1
  const getKey = (u) => {
    switch (sortBy.value) {
      case 'department': return u.department || ''
      case 'position': return u.position || ''
      case 'role': return u.globalRole || ''
      case 'status': return u.isActive ? '1' : '0'
      default: return u.name || ''
    }
  }
  list = [...list].sort((a, b) => getKey(a).localeCompare(getKey(b), 'ru') * dir)
  return list
})

function toggleSort(field) {
  if (sortBy.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortDir.value = 'asc'
  }
}

async function setRole(user, globalRole) {
  if (isSelf(user)) return
  await usersStore.updateUser(user.id, { globalRole })
}

async function toggleActive(user) {
  if (isSelf(user)) return
  await usersStore.updateUser(user.id, { isActive: !user.isActive })
}

// --- Создание пользователя ---
const showCreateForm = ref(false)
const createError = ref('')
const creating = ref(false)
const newUser = reactive({
  login: '', name: '', email: '', globalRole: 'user', password: '', position: '', department: '',
})

function resetCreateForm() {
  Object.assign(newUser, { login: '', name: '', email: '', globalRole: 'user', password: '', position: '', department: '' })
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
      position: newUser.position.trim() || undefined,
      department: newUser.department.trim() || undefined,
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

// --- Редактирование пользователя ---
const editingUser = ref(null)
const editError = ref('')
const savingEdit = ref(false)
const editForm = reactive({ name: '', email: '', position: '', department: '' })

function openEditForm(user) {
  editingUser.value = user
  editForm.name = user.name || ''
  editForm.email = user.email || ''
  editForm.position = user.position || ''
  editForm.department = user.department || ''
  editError.value = ''
}

function closeEditForm() {
  editingUser.value = null
}

async function submitEditUser() {
  editError.value = ''
  if (!editForm.name.trim() || !editForm.email.trim()) {
    editError.value = 'Имя и email обязательны'
    return
  }
  savingEdit.value = true
  try {
    await usersStore.updateUser(editingUser.value.id, {
      name: editForm.name.trim(),
      email: editForm.email.trim(),
      position: editForm.position.trim() || null,
      department: editForm.department.trim() || null,
    })
    closeEditForm()
  } catch (err) {
    const detailMsg = err?.payload?.details?.map((d) => d.msg).join('; ')
    editError.value = detailMsg || err?.message || 'Не удалось сохранить изменения'
  } finally {
    savingEdit.value = false
  }
}

// --- Удаление пользователя ---
const deletingId = ref(null)
const confirmDeleteUser = ref(null)

function askDelete(user) {
  confirmDeleteUser.value = user
}

async function confirmDelete() {
  const user = confirmDeleteUser.value
  if (!user) return
  deletingId.value = user.id
  try {
    await usersStore.deleteUser(user.id)
    confirmDeleteUser.value = null
  } finally {
    deletingId.value = null
  }
}

// --- Сброс пароля ---
const resettingId = ref(null)
const temporaryPasswordInfo = ref(null)

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
      Управление ролями, активностью, должностью и отделом пользователей. Изменение своей собственной
      роли или активности заблокировано — это защищает от случайной потери прав администратора.
    </p>

    <div class="filters-bar">
      <input v-model="searchQuery" type="text" class="filter-input" placeholder="Поиск по имени, email, логину..." />
      <select v-model="roleFilter" class="filter-select">
        <option value="all">Все роли</option>
        <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
      </select>
      <select v-model="statusFilter" class="filter-select">
        <option value="all">Все статусы</option>
        <option value="active">Активен</option>
        <option value="inactive">Деактивирован</option>
      </select>
      <select v-model="departmentFilter" class="filter-select">
        <option value="all">Все отделы</option>
        <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
      </select>
    </div>

    <div class="users-table">
      <div class="users-table-head">
        <span class="sortable" @click="toggleSort('name')">Пользователь <span v-if="sortBy === 'name'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
        <span class="sortable" @click="toggleSort('position')">Должность <span v-if="sortBy === 'position'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
        <span class="sortable" @click="toggleSort('department')">Отдел <span v-if="sortBy === 'department'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
        <span class="sortable" @click="toggleSort('role')">Роль <span v-if="sortBy === 'role'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
        <span class="sortable" @click="toggleSort('status')">Статус <span v-if="sortBy === 'status'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span></span>
        <span>Действия</span>
      </div>
      <div v-for="u in filteredSortedUsers" :key="u.id" class="user-row" :class="{ inactive: !u.isActive }">
        <div class="user-cell">
          <span class="user-avatar">{{ u.name.charAt(0) }}</span>
          <div class="user-info">
            <span class="user-name">{{ u.name }}<span v-if="isSelf(u)" class="self-badge">Вы</span></span>
            <span class="user-email">{{ u.email }}</span>
          </div>
        </div>

        <span class="text-cell">{{ u.position || '—' }}</span>
        <span class="text-cell">{{ u.department || '—' }}</span>

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

        <div class="row-actions">
          <button class="btn btn-sm btn-ghost" @click="openEditForm(u)">Изменить</button>
          <button
            class="btn btn-sm btn-ghost"
            :disabled="resettingId === u.id"
            @click="handleResetPassword(u)"
          >
            {{ resettingId === u.id ? 'Сброс...' : 'Пароль' }}
          </button>
          <button
            class="btn btn-sm btn-danger"
            :disabled="isSelf(u)"
            :title="isSelf(u) ? 'Нельзя удалить самого себя' : ''"
            @click="askDelete(u)"
          >
            Удалить
          </button>
        </div>
      </div>
      <p v-if="filteredSortedUsers.length === 0" class="hint-text empty-hint">Нет пользователей, соответствующих фильтрам.</p>
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
        <span>Должность</span>
        <input v-model="newUser.position" type="text" placeholder="Менеджер проектов" />
      </label>
      <label class="field">
        <span>Отдел</span>
        <input v-model="newUser.department" type="text" placeholder="Продажи" />
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

  <!-- Модалка редактирования пользователя -->
  <div v-if="editingUser" class="modal-backdrop" @click.self="closeEditForm">
    <div class="modal-card">
      <h3>Изменить пользователя</h3>
      <label class="field">
        <span>Имя</span>
        <input v-model="editForm.name" type="text" />
      </label>
      <label class="field">
        <span>Email</span>
        <input v-model="editForm.email" type="email" />
      </label>
      <label class="field">
        <span>Должность</span>
        <input v-model="editForm.position" type="text" placeholder="Менеджер проектов" />
      </label>
      <label class="field">
        <span>Отдел</span>
        <input v-model="editForm.department" type="text" placeholder="Продажи" />
      </label>
      <p v-if="editError" class="error-text">{{ editError }}</p>
      <div class="modal-actions">
        <button class="btn btn-sm btn-ghost" @click="closeEditForm">Отмена</button>
        <button class="btn btn-sm btn-primary" :disabled="savingEdit" @click="submitEditUser">
          {{ savingEdit ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Модалка подтверждения удаления -->
  <div v-if="confirmDeleteUser" class="modal-backdrop" @click.self="confirmDeleteUser = null">
    <div class="modal-card">
      <h3>Удалить пользователя?</h3>
      <p class="hint-text">
        Пользователь «{{ confirmDeleteUser.name }}» будет удалён без возможности восстановления.
        Его задачи, комментарии и участие в списках будут переприсвоены/обезличены согласно правилам системы.
      </p>
      <div class="modal-actions">
        <button class="btn btn-sm btn-ghost" @click="confirmDeleteUser = null">Отмена</button>
        <button class="btn btn-sm btn-danger" :disabled="deletingId === confirmDeleteUser.id" @click="confirmDelete">
          {{ deletingId === confirmDeleteUser.id ? 'Удаление...' : 'Удалить' }}
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
.empty-hint { margin: 16px 0 0; text-align: center; }

.filters-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.filter-input {
  flex: 1 1 220px; border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 12.5px;
}
.filter-select {
  border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 9px; font-size: 12.5px;
}

.users-table { display: flex; flex-direction: column; }
.users-table-head {
  display: grid; grid-template-columns: 1.4fr 1fr 1fr 150px 140px 220px; gap: 10px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted);
  padding: 0 8px 8px; border-bottom: 1px solid var(--color-border);
}
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--color-text); }
.user-row {
  display: grid; grid-template-columns: 1.4fr 1fr 1fr 150px 140px 220px; gap: 10px; align-items: center;
  padding: 10px 8px; border-bottom: 1px solid var(--color-border);
}
.user-row.inactive { opacity: 0.55; }
.user-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.text-cell { font-size: 12.5px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; }
.user-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: #b7bfd1; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.user-info { display: flex; flex-direction: column; min-width: 0; }
.user-name { font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.self-badge {
  font-size: 10px; font-weight: 700; background: #eef1f7; color: var(--color-text-muted);
  padding: 1px 6px; border-radius: 10px;
}
.user-email { font-size: 12px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; }
.role-select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 9px; font-size: 12.5px; }
.role-select:disabled { opacity: 0.6; cursor: not-allowed; }
.status-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.row-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.modal-backdrop {
  position: fixed; inset: 0; background: rgba(20, 24, 34, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-card {
  background: #fff; border-radius: 10px; padding: 20px 22px; width: 380px;
  display: flex; flex-direction: column; gap: 10px; max-height: 90vh; overflow-y: auto;
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
