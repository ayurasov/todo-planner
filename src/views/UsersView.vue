<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useUsersStore } from '../stores/usersStore'
import { useDepartmentsStore } from '../stores/departmentsStore'
import { useIsAdmin } from '../composables/usePermissions'
import { getInitials, getAvatarColor, avatarSrc } from '../utils/avatar'

const usersStore = useUsersStore()
const departmentsStore = useDepartmentsStore()
const isAdmin = useIsAdmin()

onMounted(() => {
  departmentsStore.load()
})

const ROLE_LABEL = { admin: 'Администратор', manager: 'Руководитель', user: 'Пользователь' }
const AVATAR_ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
const AVATAR_MAX_SIZE = 5 * 1024 * 1024

function departmentName(departmentId) {
  if (!departmentId) return '—'
  return departmentsStore.byId(departmentId)?.name || '—'
}

// --- Фильтрация и сортировка ---
const searchQuery = ref('')
const roleFilter = ref('all') // all | admin | manager | user
const statusFilter = ref('all') // all | active | inactive
const departmentFilter = ref('all') // all | departmentId
const showSystem = ref(true) // показывать системных в таблице (вкл. по умолчанию)
const sortBy = ref('name') // name | department | position | role | status
const sortDir = ref('asc') // asc | desc

function isSelf(user) {
  return usersStore.currentUser?.id === user.id
}

const filteredSortedUsers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let list = usersStore.users.filter((u) => {
    if (!showSystem.value && u.isSystem) return false
    if (q) {
      const hay = `${u.name} ${u.email} ${u.login || ''} ${u.position || ''} ${departmentName(u.departmentId)}`.toLowerCase()
      if (!hay.includes(q)) return false
    }
    if (roleFilter.value !== 'all' && u.globalRole !== roleFilter.value) return false
    if (statusFilter.value === 'active' && !u.isActive) return false
    if (statusFilter.value === 'inactive' && u.isActive) return false
    if (departmentFilter.value !== 'all' && u.departmentId !== departmentFilter.value) return false
    return true
  })

  const dir = sortDir.value === 'asc' ? 1 : -1
  const getKey = (u) => {
    switch (sortBy.value) {
      case 'department': return departmentName(u.departmentId)
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

// Системный флаг: разрешено менять для ЛЮБОГО пользователя включая себя.
// Это позволяет администратору самому стать системным (скрыться из списков исполнителей).
async function toggleSystem(user) {
  await usersStore.updateUser(user.id, { isSystem: !user.isSystem })
}

// --- Создание пользователя ---
const showCreateForm = ref(false)
const createError = ref('')
const creating = ref(false)
const newUser = reactive({
  login: '', name: '', email: '', globalRole: 'user', password: '', position: '', departmentId: '', managerDepartmentIds: [],
})
const createAvatarFileInputEl = ref(null)
const createAvatarFile = ref(null)
const createAvatarPreviewUrl = ref('')
const createAvatarError = ref('')

function resetCreateForm() {
  Object.assign(newUser, { login: '', name: '', email: '', globalRole: 'user', password: '', position: '', departmentId: '', managerDepartmentIds: [] })
  createError.value = ''
  clearCreateAvatarSelection()
}

function openCreateForm() {
  resetCreateForm()
  showCreateForm.value = true
}

function closeCreateForm() {
  showCreateForm.value = false
}

function validateAvatarFile(file) {
  if (!AVATAR_ALLOWED_TYPES.includes(file.type)) return 'Допустимые форматы: PNG, JPG, GIF, WEBP'
  if (file.size > AVATAR_MAX_SIZE) return 'Файл больше 5 МБ'
  return ''
}

function triggerCreateAvatarPick() {
  createAvatarError.value = ''
  createAvatarFileInputEl.value?.click()
}

function onCreateAvatarFileSelected(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  const err = validateAvatarFile(file)
  if (err) {
    createAvatarError.value = err
    return
  }
  createAvatarError.value = ''
  createAvatarFile.value = file
  if (createAvatarPreviewUrl.value) URL.revokeObjectURL(createAvatarPreviewUrl.value)
  createAvatarPreviewUrl.value = URL.createObjectURL(file)
}

function clearCreateAvatarSelection() {
  if (createAvatarPreviewUrl.value) URL.revokeObjectURL(createAvatarPreviewUrl.value)
  createAvatarFile.value = null
  createAvatarPreviewUrl.value = ''
  createAvatarError.value = ''
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
      departmentId: newUser.departmentId || null,
      managerDepartmentIds: newUser.globalRole === 'manager' ? newUser.managerDepartmentIds : undefined,
    })
    if (createAvatarFile.value) {
      try {
        await usersStore.uploadAvatar(created.id, createAvatarFile.value)
      } catch (avatarErr) {
        createAvatarError.value = avatarErr?.message || 'Пользователь создан, но фото загрузить не удалось'
      }
    }
    closeCreateForm()
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
const editForm = reactive({ name: '', email: '', position: '', departmentId: '', managerDepartmentIds: [] })
const editAvatarFileInputEl = ref(null)
const editAvatarUploading = ref(false)
const editAvatarError = ref('')

function openEditForm(user) {
  editingUser.value = user
  editForm.name = user.name || ''
  editForm.email = user.email || ''
  editForm.position = user.position || ''
  editForm.departmentId = user.departmentId || ''
  editForm.managerDepartmentIds = Array.isArray(user.managerDepartmentIds) ? [...user.managerDepartmentIds] : []
  editError.value = ''
  editAvatarError.value = ''
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
    const patch = {
      name: editForm.name.trim(),
      email: editForm.email.trim(),
      position: editForm.position.trim() || null,
      departmentId: editForm.departmentId || null,
    }
    if (editingUser.value.globalRole === 'manager') {
      patch.managerDepartmentIds = editForm.managerDepartmentIds
    }
    await usersStore.updateUser(editingUser.value.id, patch)
    closeEditForm()
  } catch (err) {
    const detailMsg = err?.payload?.details?.map((d) => d.msg).join('; ')
    editError.value = detailMsg || err?.message || 'Не удалось сохранить изменения'
  } finally {
    savingEdit.value = false
  }
}

function triggerEditAvatarPick() {
  editAvatarError.value = ''
  editAvatarFileInputEl.value?.click()
}

async function onEditAvatarFileSelected(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || !editingUser.value) return
  const err = validateAvatarFile(file)
  if (err) {
    editAvatarError.value = err
    return
  }
  editAvatarError.value = ''
  editAvatarUploading.value = true
  try {
    const updated = await usersStore.uploadAvatar(editingUser.value.id, file)
    editingUser.value = updated
  } catch (uploadErr) {
    editAvatarError.value = uploadErr?.message || 'Не удалось загрузить фото'
  } finally {
    editAvatarUploading.value = false
  }
}

async function handleRemoveEditAvatar() {
  if (!editingUser.value) return
  editAvatarUploading.value = true
  editAvatarError.value = ''
  try {
    const updated = await usersStore.deleteAvatar(editingUser.value.id)
    editingUser.value = updated
  } catch (err) {
    editAvatarError.value = err?.message || 'Не удалось удалить фото'
  } finally {
    editAvatarUploading.value = false
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

/** При ошибке загрузки img — скрыть img, показать fallback-спан рядом */
function onAvatarError(e) {
  const img = e.target
  img.style.display = 'none'
  const fallback = img.nextElementSibling
  if (fallback) fallback.style.display = 'flex'
}
</script>

<template>
  <div class="view-header users-header">
    <h2>Пользователи</h2>
    <button v-if="isAdmin" class="btn btn-sm btn-primary" @click="openCreateForm">+ Новый пользователь</button>
  </div>

  <section v-if="isAdmin" class="card users-section">
    <p class="hint-text">
      Управление ролями, активностью, должностью, отделом и фото пользователей. Роль "Руководитель" даёт
      видимость списков/задач всего отдела (можно назначить сразу несколько отделов/служб).
      <strong>Системные</strong> пользователи (например admin) не отображаются в списках исполнителей и участников.
      Изменение своей собственной роли или активности заблокировано.
      Флаг «системный» администратор может выставить в том числе для себя.
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
        <option v-for="d in departmentsStore.sortedDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
      <label class="filter-checkbox">
        <input v-model="showSystem" type="checkbox" />
        <span>Системные</span>
      </label>
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
      <div v-for="u in filteredSortedUsers" :key="u.id" class="user-row" :class="{ inactive: !u.isActive, 'is-system': u.isSystem }">
        <div class="user-cell">
          <div class="user-avatar-wrap">
            <img
              v-if="u.avatarUrl"
              :src="avatarSrc(u.avatarUrl)"
              class="user-avatar user-avatar-img"
              alt=""
              @error="onAvatarError"
            />
            <span
              class="user-avatar"
              :style="{ background: getAvatarColor(u.name), display: u.avatarUrl ? 'none' : 'flex' }"
            >{{ getInitials(u.name) }}</span>
          </div>
          <div class="user-info">
            <span class="user-name">
              {{ u.name }}
              <span v-if="isSelf(u)" class="self-badge">Вы</span>
              <span v-if="u.isSystem" class="system-badge" title="Системный пользователь — не виден в списках исполнителей">⚙️ системный</span>
            </span>
            <span class="user-email">{{ u.email }}</span>
            <span v-if="u.globalRole === 'manager' && u.managerDepartmentIds?.length" class="managed-badge">
              руковит: {{ u.managerDepartmentIds.map(departmentName).join(', ') }}
            </span>
          </div>
        </div>

        <span class="text-cell">{{ u.position || '—' }}</span>
        <span class="text-cell">{{ departmentName(u.departmentId) }}</span>

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
          <button
            class="btn btn-sm"
            :class="u.isSystem ? 'btn-warning' : 'btn-ghost'"
            :title="u.isSystem ? 'Снять системный флаг' : 'Отметить как системный'"
            @click="toggleSystem(u)"
          >
            {{ u.isSystem ? '⚙️ системный' : '• системный?' }}
          </button>
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
            удалить
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
  <div v-if="showCreateForm" class="modal-backdrop">
    <div class="modal-card">
      <h3>Новый пользователь</h3>

      <div class="avatar-field">
        <div class="avatar-field-preview">
          <img v-if="createAvatarPreviewUrl" :src="createAvatarPreviewUrl" class="avatar-preview-img" alt="" />
          <span v-else class="avatar-preview-placeholder">фото</span>
        </div>
        <div class="avatar-field-actions">
          <button type="button" class="btn btn-sm btn-ghost" @click="triggerCreateAvatarPick">Выбрать фото</button>
          <button v-if="createAvatarFile" type="button" class="btn btn-sm btn-ghost" @click="clearCreateAvatarSelection">Убрать</button>
          <input ref="createAvatarFileInputEl" type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="file-input-hidden" @change="onCreateAvatarFileSelected" />
        </div>
        <p v-if="createAvatarError" class="field-error">{{ createAvatarError }}</p>
      </div>

      <label class="field">
        <span>Логин *</span>
        <input v-model="newUser.login" type="text" autocomplete="off" />
      </label>
      <label class="field">
        <span>Имя *</span>
        <input v-model="newUser.name" type="text" />
      </label>
      <label class="field">
        <span>Email *</span>
        <input v-model="newUser.email" type="email" />
      </label>
      <label class="field">
        <span>Пароль (оставьте пустым — будет сгенерирован)</span>
        <input v-model="newUser.password" type="password" autocomplete="new-password" />
      </label>
      <label class="field">
        <span>Должность</span>
        <input v-model="newUser.position" type="text" />
      </label>
      <label class="field">
        <span>Отдел</span>
        <select v-model="newUser.departmentId">
          <option value="">— не выбран —</option>
          <option v-for="d in departmentsStore.sortedDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </label>
      <label class="field">
        <span>Роль</span>
        <select v-model="newUser.globalRole">
          <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
        </select>
      </label>
      <div v-if="newUser.globalRole === 'manager'" class="field">
        <span>Отделы в управлении</span>
        <div class="checkbox-list">
          <label v-for="d in departmentsStore.sortedDepartments" :key="d.id" class="checkbox-item">
            <input v-model="newUser.managerDepartmentIds" type="checkbox" :value="d.id" />
            {{ d.name }}
          </label>
        </div>
      </div>

      <p v-if="createError" class="field-error">{{ createError }}</p>
      <div class="modal-actions">
        <button class="btn btn-ghost btn-sm" @click="closeCreateForm">Отмена</button>
        <button class="btn btn-primary btn-sm" :disabled="creating" @click="submitCreateUser">
          {{ creating ? 'Создание...' : 'Создать' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Модалка редактирования -->
  <div v-if="editingUser" class="modal-backdrop">
    <div class="modal-card">
      <h3>Редактировать пользователя</h3>

      <div class="avatar-field">
        <div class="avatar-field-preview">
          <img
            v-if="editingUser.avatarUrl"
            :src="avatarSrc(editingUser.avatarUrl)"
            class="avatar-preview-img"
            alt=""
            @error="(e) => { e.target.style.display='none' }"
          />
          <span v-if="!editingUser.avatarUrl" class="avatar-preview-placeholder">фото</span>
        </div>
        <div class="avatar-field-actions">
          <button type="button" class="btn btn-sm btn-ghost" :disabled="editAvatarUploading" @click="triggerEditAvatarPick">
            {{ editAvatarUploading ? 'Загрузка...' : 'Изменить фото' }}
          </button>
          <button v-if="editingUser.avatarUrl" type="button" class="btn btn-sm btn-ghost" :disabled="editAvatarUploading" @click="handleRemoveEditAvatar">Удалить фото</button>
          <input ref="editAvatarFileInputEl" type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="file-input-hidden" @change="onEditAvatarFileSelected" />
        </div>
        <p v-if="editAvatarError" class="field-error">{{ editAvatarError }}</p>
      </div>

      <label class="field">
        <span>Имя *</span>
        <input v-model="editForm.name" type="text" />
      </label>
      <label class="field">
        <span>Email *</span>
        <input v-model="editForm.email" type="email" />
      </label>
      <label class="field">
        <span>Должность</span>
        <input v-model="editForm.position" type="text" />
      </label>
      <label class="field">
        <span>Отдел</span>
        <select v-model="editForm.departmentId">
          <option value="">— не выбран —</option>
          <option v-for="d in departmentsStore.sortedDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </label>
      <div v-if="editingUser.globalRole === 'manager'" class="field">
        <span>Отделы в управлении</span>
        <div class="checkbox-list">
          <label v-for="d in departmentsStore.sortedDepartments" :key="d.id" class="checkbox-item">
            <input v-model="editForm.managerDepartmentIds" type="checkbox" :value="d.id" />
            {{ d.name }}
          </label>
        </div>
      </div>

      <p v-if="editError" class="field-error">{{ editError }}</p>
      <div class="modal-actions">
        <button class="btn btn-ghost btn-sm" @click="closeEditForm">Отмена</button>
        <button class="btn btn-primary btn-sm" :disabled="savingEdit" @click="submitEditUser">
          {{ savingEdit ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Подтверждение удаления -->
  <div v-if="confirmDeleteUser" class="modal-backdrop">
    <div class="modal-card modal-card-sm">
      <h3>Удалить пользователя?</h3>
      <p>{{ confirmDeleteUser.name }} ({{ confirmDeleteUser.email }}) будет удалён без возможности восстановления.</p>
      <div class="modal-actions">
        <button class="btn btn-ghost btn-sm" @click="confirmDeleteUser = null">Отмена</button>
        <button class="btn btn-danger btn-sm" :disabled="deletingId === confirmDeleteUser.id" @click="confirmDelete">
          {{ deletingId === confirmDeleteUser.id ? 'Удаление...' : 'Удалить' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Модалка с временным паролем -->
  <div v-if="temporaryPasswordInfo" class="modal-backdrop">
    <div class="modal-card modal-card-sm">
      <h3>Временный пароль</h3>
      <p>Передайте пользователю:</p>
      <p><strong>Логин:</strong> {{ temporaryPasswordInfo.login }}</p>
      <p><strong>Пароль:</strong> <code>{{ temporaryPasswordInfo.password }}</code></p>
      <div class="modal-actions">
        <button class="btn btn-primary btn-sm" @click="closePasswordModal">Закрыть</button>
      </div>
    </div>
  </div>
</template>
