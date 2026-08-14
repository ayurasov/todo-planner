<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
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
const roleFilter = ref('all')
const statusFilter = ref('all')
const departmentFilter = ref('all')
const showSystem = ref(true)
const sortBy = ref('name')
const sortDir = ref('asc')

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

async function toggleSystem(user) {
  await usersStore.updateUser(user.id, { isSystem: !user.isSystem })
}

// --- Мультиселект отделов (для руководителя) ---
function useDeptMultiselect(deptIdsRef, allDepts) {
  const open = ref(false)
  const search = ref('')
  const inputEl = ref(null)

  const filteredDepts = computed(() => {
    const q = search.value.trim().toLowerCase()
    return allDepts.value.filter((d) => !q || d.name.toLowerCase().includes(q))
  })

  function toggle(id) {
    const idx = deptIdsRef.value.indexOf(id)
    if (idx === -1) deptIdsRef.value.push(id)
    else deptIdsRef.value.splice(idx, 1)
  }

  function removeTag(id) {
    const idx = deptIdsRef.value.indexOf(id)
    if (idx !== -1) deptIdsRef.value.splice(idx, 1)
  }

  function openMenu() {
    open.value = true
    search.value = ''
    nextTick(() => inputEl.value?.focus())
  }

  function closeMenu() {
    open.value = false
  }

  const selectedDepts = computed(() =>
    deptIdsRef.value
      .map((id) => allDepts.value.find((d) => d.id === id))
      .filter(Boolean),
  )

  return { open, search, inputEl, filteredDepts, selectedDepts, toggle, removeTag, openMenu, closeMenu }
}

const allDepts = computed(() => departmentsStore.sortedDepartments)

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

const createDeptIdsRef = ref([])
const createMulti = useDeptMultiselect(createDeptIdsRef, allDepts)

function resetCreateForm() {
  Object.assign(newUser, { login: '', name: '', email: '', globalRole: 'user', password: '', position: '', departmentId: '', managerDepartmentIds: [] })
  createDeptIdsRef.value = []
  createError.value = ''
  clearCreateAvatarSelection()
}

function openCreateForm() {
  resetCreateForm()
  showCreateForm.value = true
}

function closeCreateForm() {
  showCreateForm.value = false
  createMulti.closeMenu()
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
  if (err) { createAvatarError.value = err; return }
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
      managerDepartmentIds: newUser.globalRole === 'manager' ? [...createDeptIdsRef.value] : undefined,
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

const editDeptIdsRef = ref([])
const editMulti = useDeptMultiselect(editDeptIdsRef, allDepts)

function openEditForm(user) {
  editingUser.value = user
  editForm.name = user.name || ''
  editForm.email = user.email || ''
  editForm.position = user.position || ''
  editForm.departmentId = user.departmentId || ''
  editDeptIdsRef.value = Array.isArray(user.managerDepartmentIds) ? [...user.managerDepartmentIds] : []
  editError.value = ''
  editAvatarError.value = ''
  editMulti.closeMenu()
}

function closeEditForm() {
  editingUser.value = null
  editMulti.closeMenu()
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
      // Всегда передаём managerDepartmentIds: если пользователь руководитель — передаём список,
      // иначе — пустой массив (чтобы сбросить если роль была сменена)
      managerDepartmentIds: editingUser.value.globalRole === 'manager' ? [...editDeptIdsRef.value] : [],
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
  if (err) { editAvatarError.value = err; return }
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
      <div class="modal-header">
        <h3>Новый пользователь</h3>
      </div>
      <!-- Скрольтится только содержимое — допозволяя дропдауну вылезать поверх -->
      <div class="modal-body">
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

        <!-- Мультиселект отделов для руководителя (форма создания) -->
        <div v-if="newUser.globalRole === 'manager'" class="field">
          <span class="field-label">Отделы в управлении</span>
          <div class="dept-multiselect" :class="{ 'dept-multiselect--open': createMulti.open.value }">
            <div class="dept-multiselect__control" @click="createMulti.openMenu()">
              <span v-for="d in createMulti.selectedDepts.value" :key="d.id" class="dept-tag">
                {{ d.name }}
                <button type="button" class="dept-tag__remove" @click.stop="createMulti.removeTag(d.id)">×</button>
              </span>
              <span v-if="!createMulti.selectedDepts.value.length" class="dept-multiselect__placeholder">Выберите отделы...</span>
              <span class="dept-multiselect__chevron">▾</span>
            </div>
            <div v-if="createMulti.open.value" class="dept-multiselect__dropdown">
              <div class="dept-multiselect__search-wrap">
                <input
                  :ref="(el) => (createMulti.inputEl.value = el)"
                  v-model="createMulti.search.value"
                  class="dept-multiselect__search"
                  placeholder="Поиск отдела..."
                  @keyup.escape="createMulti.closeMenu()"
                />
              </div>
              <template v-if="createMulti.filteredDepts.value.length">
                <button
                  v-for="d in createMulti.filteredDepts.value"
                  :key="d.id"
                  type="button"
                  class="dept-multiselect__option"
                  :class="{ 'dept-multiselect__option--selected': createDeptIdsRef.includes(d.id) }"
                  @click="createMulti.toggle(d.id)"
                >
                  <span class="dept-multiselect__option-check">{{ createDeptIdsRef.includes(d.id) ? '✓' : '' }}</span>
                  {{ d.name }}
                </button>
              </template>
              <div v-else class="dept-multiselect__empty">Отделы не найдены</div>
            </div>
          </div>
        </div>

        <p v-if="createError" class="field-error">{{ createError }}</p>
      </div>
      <div class="modal-footer">
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
      <div class="modal-header">
        <h3>Редактировать пользователя</h3>
      </div>
      <div class="modal-body">
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

        <!-- Мультиселект отделов для руководителя (форма редактирования) -->
        <div v-if="editingUser.globalRole === 'manager'" class="field">
          <span class="field-label">Отделы в управлении</span>
          <div class="dept-multiselect" :class="{ 'dept-multiselect--open': editMulti.open.value }">
            <div class="dept-multiselect__control" @click="editMulti.openMenu()">
              <span v-for="d in editMulti.selectedDepts.value" :key="d.id" class="dept-tag">
                {{ d.name }}
                <button type="button" class="dept-tag__remove" @click.stop="editMulti.removeTag(d.id)">×</button>
              </span>
              <span v-if="!editMulti.selectedDepts.value.length" class="dept-multiselect__placeholder">Выберите отделы...</span>
              <span class="dept-multiselect__chevron">▾</span>
            </div>
            <div v-if="editMulti.open.value" class="dept-multiselect__dropdown">
              <div class="dept-multiselect__search-wrap">
                <input
                  :ref="(el) => (editMulti.inputEl.value = el)"
                  v-model="editMulti.search.value"
                  class="dept-multiselect__search"
                  placeholder="Поиск отдела..."
                  @keyup.escape="editMulti.closeMenu()"
                />
              </div>
              <template v-if="editMulti.filteredDepts.value.length">
                <button
                  v-for="d in editMulti.filteredDepts.value"
                  :key="d.id"
                  type="button"
                  class="dept-multiselect__option"
                  :class="{ 'dept-multiselect__option--selected': editDeptIdsRef.includes(d.id) }"
                  @click="editMulti.toggle(d.id)"
                >
                  <span class="dept-multiselect__option-check">{{ editDeptIdsRef.includes(d.id) ? '✓' : '' }}</span>
                  {{ d.name }}
                </button>
              </template>
              <div v-else class="dept-multiselect__empty">Отделы не найдены</div>
            </div>
          </div>
        </div>

        <p v-if="editError" class="field-error">{{ editError }}</p>
      </div>
      <div class="modal-footer">
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
      <div class="modal-header"><h3>Удалить пользователя?</h3></div>
      <div class="modal-body">
        <p>{{ confirmDeleteUser.name }} ({{ confirmDeleteUser.email }}) будет удалён без возможности восстановления.</p>
      </div>
      <div class="modal-footer">
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
      <div class="modal-header"><h3>Временный пароль</h3></div>
      <div class="modal-body">
        <p>Передайте пользователю:</p>
        <p><strong>Логин:</strong> {{ temporaryPasswordInfo.login }}</p>
        <p><strong>Пароль:</strong> <code>{{ temporaryPasswordInfo.password }}</code></p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary btn-sm" @click="closePasswordModal">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.users-header { display: flex; align-items: center; justify-content: space-between; }
.users-section { padding: 16px 18px; }
.hint-text { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 14px; }
.empty-hint { margin: 16px 0 0; text-align: center; }
.file-input-hidden { display: none; }

/* ── Filters ── */
.filters-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.filter-input {
  flex: 1 1 220px; border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 12.5px;
}
.filter-select {
  border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 9px; font-size: 12.5px;
}
.filter-checkbox { display: flex; align-items: center; gap: 5px; font-size: 12.5px; cursor: pointer; user-select: none; }
.filter-checkbox input { cursor: pointer; }

/* ── Table ── */
.users-table { display: flex; flex-direction: column; }
.users-table-head {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 150px 140px 260px;
  gap: 10px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted);
  padding: 0 8px 8px; border-bottom: 1px solid var(--color-border);
}
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--color-text); }
.user-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 150px 140px 260px;
  gap: 10px;
  align-items: center;
  padding: 10px 8px;
  border-bottom: 1px solid var(--color-border);
}
.user-row.inactive { opacity: 0.55; }
.user-row.is-system { background: #f8f6ff; }

/* ── User cell ── */
.user-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.text-cell { font-size: 12.5px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; }
.user-avatar-wrap { position: relative; flex-shrink: 0; }
.user-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: #b7bfd1; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.user-avatar-img { object-fit: cover; }
.user-info { display: flex; flex-direction: column; min-width: 0; }
.user-name { font-size: 13.5px; font-weight: 600; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.self-badge {
  font-size: 10px; font-weight: 700; background: #eef1f7; color: var(--color-text-muted);
  padding: 1px 6px; border-radius: 10px;
}
.system-badge {
  font-size: 10px; font-weight: 600; background: #ede9fe; color: #6d28d9;
  padding: 1px 6px; border-radius: 10px; cursor: default;
}
.user-email { font-size: 12px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; }
.managed-badge { font-size: 11px; color: #4f7cff; overflow: hidden; text-overflow: ellipsis; }

/* ── Row controls ── */
.role-select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 9px; font-size: 12.5px; }
.role-select:disabled { opacity: 0.6; cursor: not-allowed; }
.status-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.row-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-warning { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
.btn-warning:hover:not(:disabled) { background: #fde68a; }

/* ── Modals ──
   modal-card — БЕЗ overflow, чтобы absolute-дропдаун вылезал поверх границ.
   Скролл внутри modal-body.
*/
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(20, 24, 34, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-card {
  background: #fff; border-radius: 10px;
  width: 520px; max-width: calc(100vw - 32px);
  display: flex; flex-direction: column;
  max-height: 90vh;
  /* overflow: hidden — не auto! чтобы dropdown не обрезался */
  overflow: hidden;
}
.modal-card-sm { width: 340px; }
.modal-header {
  padding: 18px 22px 0;
  flex-shrink: 0;
}
.modal-header h3 { margin: 0 0 12px; font-size: 16px; }
.modal-body {
  padding: 0 22px 4px;
  overflow-y: auto;     /* скролл внутри — не мешает absolute dropdown */
  display: flex; flex-direction: column; gap: 10px;
  /* overflow-x visible чтобы dropdown мог вылезти за край при необходимости */
  overflow-x: visible;
}
.modal-footer {
  padding: 10px 22px 18px;
  flex-shrink: 0;
  display: flex; justify-content: flex-end; gap: 8px;
  border-top: 1px solid var(--color-border);
}

.field { display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; }
.field input, .field select {
  border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 9px; font-size: 13px;
}
.field-label { display: block; font-size: 13px; font-weight: 500; color: var(--color-text-muted); margin-bottom: 4px; }
.avatar-field { display: flex; align-items: center; gap: 12px; }
.avatar-field-preview {
  width: 56px; height: 56px; border-radius: 50%; overflow: hidden;
  background: #eef1f7; display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--color-text-muted); flex-shrink: 0;
}
.avatar-preview-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-preview-placeholder { font-size: 11px; color: var(--color-text-muted); }
.avatar-field-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.field-error { color: #d64545; font-size: 12px; margin: 0; }

/* ── Dept multiselect ── */
.dept-multiselect { position: relative; }

.dept-multiselect__control {
  display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
  min-height: 36px; border: 1px solid var(--color-border);
  border-radius: 8px; padding: 4px 8px;
  cursor: pointer; background: var(--color-surface, #fff);
  transition: border-color 0.12s; user-select: none;
}
.dept-multiselect--open .dept-multiselect__control,
.dept-multiselect__control:hover { border-color: var(--color-primary); }

.dept-multiselect__placeholder { font-size: 13px; color: var(--color-text-muted); flex: 1; }
.dept-multiselect__chevron { margin-left: auto; font-size: 11px; color: var(--color-text-muted); flex-shrink: 0; }

.dept-tag {
  display: inline-flex; align-items: center; gap: 4px;
  background: #eef2ff; color: var(--color-primary, #4f7cff);
  border-radius: 6px; padding: 2px 6px 2px 8px;
  font-size: 12px; font-weight: 500; line-height: 1.4; white-space: nowrap;
}
.dept-tag__remove {
  background: none; border: none; cursor: pointer;
  font-size: 14px; line-height: 1; color: var(--color-primary, #4f7cff);
  opacity: 0.7; padding: 0 2px; display: flex; align-items: center;
}
.dept-tag__remove:hover { opacity: 1; }

/* dropdown вылезает поверх благодаря position:fixed + z-index */
.dept-multiselect__dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  z-index: 200;
  background: var(--color-surface, #fff); border: 1px solid var(--color-border);
  border-radius: 10px; box-shadow: 0 8px 24px rgba(20, 24, 38, 0.14);
  max-height: 220px; overflow-y: auto; padding: 6px 0 4px;
}
.dept-multiselect__search-wrap { padding: 4px 8px 6px; }
.dept-multiselect__search {
  width: 100%; border: 1px solid var(--color-border);
  border-radius: 7px; padding: 5px 9px; font-size: 13px;
  outline: none; background: #f6f7fb;
}
.dept-multiselect__search:focus { border-color: var(--color-primary); background: #fff; }

.dept-multiselect__option {
  display: flex; align-items: center; gap: 8px;
  width: 100%; text-align: left; border: none; background: none;
  padding: 7px 12px; font-size: 13px; cursor: pointer; color: var(--color-text);
}
.dept-multiselect__option:hover { background: #f1f3f9; }
.dept-multiselect__option--selected { background: #eef2ff; font-weight: 600; }
.dept-multiselect__option-check { width: 16px; font-size: 13px; color: var(--color-primary, #4f7cff); flex-shrink: 0; }
.dept-multiselect__empty { padding: 8px 12px; font-size: 12px; color: var(--color-text-muted); }
</style>
