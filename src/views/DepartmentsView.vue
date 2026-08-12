<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useDepartmentsStore } from '../stores/departmentsStore'
import { useUsersStore } from '../stores/usersStore'
import { useIsAdmin } from '../composables/usePermissions'

const departmentsStore = useDepartmentsStore()
const usersStore = useUsersStore()
const isAdmin = useIsAdmin()

onMounted(async () => {
  await Promise.all([departmentsStore.load(), usersStore.load()])
})

// Возможные руководители -- любой пользователь с globalRole='manager'.
// Один manager может вести несколько отделов одновременно (many-to-many).
const possibleManagers = computed(() => usersStore.users.filter((u) => u.globalRole === 'manager'))

function managersOf(departmentId) {
  return usersStore.users.filter((u) => Array.isArray(u.managerDepartmentIds) && u.managerDepartmentIds.includes(departmentId))
}

// --- Создание отдела ---
const newDepartmentName = ref('')
const creating = ref(false)
const createError = ref('')

async function submitCreate() {
  createError.value = ''
  const name = newDepartmentName.value.trim()
  if (!name) {
    createError.value = 'Укажите название отдела/службы'
    return
  }
  creating.value = true
  try {
    await departmentsStore.createDepartment({ name })
    newDepartmentName.value = ''
  } catch (err) {
    createError.value = err?.message || 'Не удалось создать отдел'
  } finally {
    creating.value = false
  }
}

// --- Редактирование названия ---
const editingId = ref(null)
const editName = ref('')
const savingEdit = ref(false)

function startEdit(dep) {
  editingId.value = dep.id
  editName.value = dep.name
}

function cancelEdit() {
  editingId.value = null
  editName.value = ''
}

async function saveEdit() {
  const name = editName.value.trim()
  if (!name) return
  savingEdit.value = true
  try {
    await departmentsStore.updateDepartment(editingId.value, { name })
    cancelEdit()
  } finally {
    savingEdit.value = false
  }
}

// --- удаление отдела ---
const confirmDeleteDep = ref(null)
const deletingId = ref(null)

function askDelete(dep) {
  confirmDeleteDep.value = dep
}

async function confirmDelete() {
  const dep = confirmDeleteDep.value
  if (!dep) return
  deletingId.value = dep.id
  try {
    await departmentsStore.deleteDepartment(dep.id)
    confirmDeleteDep.value = null
  } finally {
    deletingId.value = null
  }
}

// --- управление руководителями отдела (массив userId на many-to-many связь) ---
const managingDep = ref(null)
const managerForm = reactive({ userIds: [] })
const savingManagers = ref(false)

function openManagersForm(dep) {
  managingDep.value = dep
  managerForm.userIds = managersOf(dep.id).map((u) => u.id)
}

function closeManagersForm() {
  managingDep.value = null
}

async function saveManagers() {
  savingManagers.value = true
  try {
    await departmentsStore.setManagers(managingDep.value.id, managerForm.userIds)
    await usersStore.load ? null : null
    // usersStore уже загружен, но его локальный кэш не знает о смене managerDepartmentIds
    // у других пользователей -- перезагрузим список целиком.
    usersStore.loaded = false
    await usersStore.load()
    closeManagersForm()
  } finally {
    savingManagers.value = false
  }
}
</script>

<template>
  <div class="view-header">
    <h2>Отделы и службы</h2>
  </div>

  <section v-if="isAdmin" class="card departments-section">
    <p class="hint-text">
      Справочник отделов/служб — плоский список, без вложенности/иерархии. У отдела может быть несколько
      руководителей, а один руководитель может отвечать сразу за несколько отделов. Назначить руководителя можно
      только из пользователей с ролью «Руководитель» (назначается в разделе Пользователи).
    </p>

    <form class="create-row" @submit.prevent="submitCreate">
      <input v-model="newDepartmentName" type="text" placeholder="Название отдела/службы" class="filter-input" />
      <button class="btn btn-sm btn-primary" type="submit" :disabled="creating">
        {{ creating ? 'создание...' : '+ добавить отдел' }}
      </button>
    </form>
    <p v-if="createError" class="error-text">{{ createError }}</p>

    <div class="departments-table">
      <div class="departments-table-head">
        <span>Название</span>
        <span>руководители</span>
        <span>действия</span>
      </div>
      <div v-for="dep in departmentsStore.sortedDepartments" :key="dep.id" class="department-row">
        <div class="dep-name-cell">
          <template v-if="editingId === dep.id">
            <input v-model="editName" type="text" class="filter-input" @keyup.enter="saveEdit" @keyup.esc="cancelEdit" />
            <button class="btn btn-sm btn-primary" :disabled="savingEdit" @click="saveEdit">сохранить</button>
            <button class="btn btn-sm btn-ghost" @click="cancelEdit">отмена</button>
          </template>
          <span v-else class="dep-name">{{ dep.name }}</span>
        </div>

        <div class="dep-managers-cell">
          <span v-if="managersOf(dep.id).length" class="managers-list">{{ managersOf(dep.id).map((u) => u.name).join(', ') }}</span>
          <span v-else class="hint-text no-managers">руководитель не назначен</span>
        </div>

        <div class="row-actions">
          <button class="btn btn-sm btn-ghost" @click="openManagersForm(dep)">руководители</button>
          <button v-if="editingId !== dep.id" class="btn btn-sm btn-ghost" @click="startEdit(dep)">изменить</button>
          <button class="btn btn-sm btn-danger" @click="askDelete(dep)">удалить</button>
        </div>
      </div>
      <p v-if="!departmentsStore.sortedDepartments.length" class="hint-text empty-hint">Отделы ещё не созданы.</p>
    </div>
  </section>

  <section v-else class="card departments-section">
    <p class="hint-text">Доступ только для администраторов.</p>
  </section>

  <!-- Модалка назначения руководителей -->
  <div v-if="managingDep" class="modal-backdrop" @click.self="closeManagersForm">
    <div class="modal-card">
      <h3>руководители отдела «{{ managingDep.name }}»</h3>
      <p class="hint-text">
        можно выбрать нескольких руководителей одновременно. в списке — пользователи с ролью «руководитель».
      </p>
      <select v-model="managerForm.userIds" multiple size="6" class="managers-select">
        <option v-for="u in possibleManagers" :key="u.id" :value="u.id">{{ u.name }}</option>
      </select>
      <p v-if="!possibleManagers.length" class="hint-text">
        нет пользователей с ролью «руководитель». назначьте роль в разделе Пользователи.
      </p>
      <div class="modal-actions">
        <button class="btn btn-sm btn-ghost" @click="closeManagersForm">отмена</button>
        <button class="btn btn-sm btn-primary" :disabled="savingManagers" @click="saveManagers">
          {{ savingManagers ? 'сохранение...' : 'сохранить' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Модалка удаления отдела -->
  <div v-if="confirmDeleteDep" class="modal-backdrop" @click.self="confirmDeleteDep = null">
    <div class="modal-card">
      <h3>удалить отдел?</h3>
      <p class="hint-text">
        отдел «{{ confirmDeleteDep.name }}» будет удалён. у сотрудников из этого отдела привязка к отделу сбросится,
        а у руководителей он исчезнет из списка подведомственных отделов.
      </p>
      <div class="modal-actions">
        <button class="btn btn-sm btn-ghost" @click="confirmDeleteDep = null">отмена</button>
        <button class="btn btn-sm btn-danger" :disabled="deletingId === confirmDeleteDep.id" @click="confirmDelete">
          {{ deletingId === confirmDeleteDep.id ? 'удаление...' : 'удалить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.departments-section { padding: 16px 18px; }
.hint-text { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 14px; }
.empty-hint { margin: 16px 0 0; text-align: center; }
.no-managers { margin: 0; }

.create-row { display: flex; gap: 8px; margin-bottom: 6px; }
.filter-input { flex: 1 1 280px; border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 12.5px; }
.error-text { color: #d64545; font-size: 12px; margin: 4px 0 10px; }

.departments-table { display: flex; flex-direction: column; margin-top: 12px; }
.departments-table-head {
  display: grid; grid-template-columns: 1.4fr 1.6fr 220px; gap: 10px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted);
  padding: 0 8px 8px; border-bottom: 1px solid var(--color-border);
}
.department-row {
  display: grid; grid-template-columns: 1.4fr 1.6fr 220px; gap: 10px; align-items: center;
  padding: 10px 8px; border-bottom: 1px solid var(--color-border);
}
.dep-name-cell { display: flex; align-items: center; gap: 6px; }
.dep-name { font-size: 13.5px; font-weight: 600; }
.dep-managers-cell { font-size: 12.5px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; }
.managers-list { color: var(--color-text); }
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
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 6px; }
.managers-select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px; font-size: 13px; }
</style>
