<script setup>
import { computed, reactive, ref } from 'vue'
import { useUsersStore } from '../../stores/usersStore'
import { useDepartmentsStore } from '../../stores/departmentsStore'
import { getInitials, getAvatarColor } from '../../utils/avatar'
import AppIcon from './AppIcon.vue'

const emit = defineEmits(['close'])
const usersStore = useUsersStore()
const departmentsStore = useDepartmentsStore()

const ROLE_LABEL = { admin: 'Администратор', manager: 'Руководитель', user: 'Пользователь' }

const user = computed(() => usersStore.currentUser)

function departmentName(departmentId) {
  if (!departmentId) return '—'
  return departmentsStore.byId?.(departmentId)?.name || '—'
}

const managedDepartments = computed(() => {
  const ids = user.value?.managerDepartmentIds || user.value?.managedDepartmentIds || []
  return ids.map(departmentName).join(', ')
})

// --- Загрузка своей фотографии ---
const fileInputEl = ref(null)
const uploading = ref(false)
const uploadError = ref('')

function triggerFilePicker() {
  uploadError.value = ''
  fileInputEl.value?.click()
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  const allowed = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
  if (!allowed.includes(file.type)) {
    uploadError.value = 'Допустимые форматы: PNG, JPG, GIF, WEBP'
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    uploadError.value = 'Файл больше 5 МБ'
    return
  }

  uploading.value = true
  uploadError.value = ''
  try {
    await usersStore.uploadAvatar(user.value.id, file)
  } catch (err) {
    uploadError.value = err?.message || 'Не удалось загрузить фото'
  } finally {
    uploading.value = false
  }
}

async function removeAvatar() {
  uploading.value = true
  uploadError.value = ''
  try {
    await usersStore.deleteAvatar(user.value.id)
  } catch (err) {
    uploadError.value = err?.message || 'Не удалось удалить фото'
  } finally {
    uploading.value = false
  }
}

// --- Смена пароля ---
const showPasswordForm = ref(false)
const passwordForm = reactive({ currentPassword: '', newPassword: '', confirmPassword: '' })
const passwordError = ref('')
const passwordSuccess = ref('')
const changingPassword = ref(false)

function togglePasswordForm() {
  showPasswordForm.value = !showPasswordForm.value
  passwordError.value = ''
  passwordSuccess.value = ''
  Object.assign(passwordForm, { currentPassword: '', newPassword: '', confirmPassword: '' })
}

async function submitPasswordChange() {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (!passwordForm.currentPassword || !passwordForm.newPassword) {
    passwordError.value = 'Заполните все поля'
    return
  }
  if (passwordForm.newPassword.length < 8) {
    passwordError.value = 'Новый пароль должен быть не короче 8 символов'
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordError.value = 'Пароли не совпадают'
    return
  }

  changingPassword.value = true
  try {
    await usersStore.changePassword({
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword,
    })
    passwordSuccess.value = 'Пароль успешно изменён'
    Object.assign(passwordForm, { currentPassword: '', newPassword: '', confirmPassword: '' })
    showPasswordForm.value = false
  } catch (err) {
    const detailMsg = err?.payload?.details?.map((d) => d.msg).join('; ')
    passwordError.value = detailMsg || err?.message || 'Не удалось сменить пароль'
  } finally {
    changingPassword.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Профиль</h3>
        <button class="btn btn-ghost btn-icon btn-sm" @click="emit('close')"><AppIcon name="close" :size="13" /></button>
      </div>

      <div v-if="user" class="modal-body">
        <div class="profile-hero">
          <div class="avatar-wrap">
            <img v-if="user.avatarUrl" :src="user.avatarUrl" class="avatar-img" alt="" />
            <span v-else class="avatar-fallback" :style="{ background: getAvatarColor(user.name) }">
              {{ getInitials(user.name) }}
            </span>
            <button class="avatar-edit-btn" title="Изменить фото" :disabled="uploading" @click="triggerFilePicker">
              <AppIcon name="edit" :size="12" />
            </button>
            <input ref="fileInputEl" type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="file-input-hidden" @change="onFileSelected" />
          </div>
          <div class="profile-heading">
            <div class="profile-name">{{ user.name }}</div>
            <div class="profile-role-badge">{{ ROLE_LABEL[user.globalRole] || user.globalRole }}</div>
          </div>
        </div>

        <div class="avatar-actions">
          <button class="btn btn-sm btn-ghost" :disabled="uploading" @click="triggerFilePicker">
            {{ uploading ? 'Загрузка...' : 'Загрузить фото' }}
          </button>
          <button v-if="user.avatarUrl" class="btn btn-sm btn-ghost" :disabled="uploading" @click="removeAvatar">Удалить фото</button>
        </div>
        <p v-if="uploadError" class="error-text">{{ uploadError }}</p>

        <div class="section-title">Информация</div>
        <div class="info-grid">
          <div class="info-row"><span class="info-label">Email</span><span class="info-value">{{ user.email }}</span></div>
          <div class="info-row"><span class="info-label">Логин</span><span class="info-value">{{ user.login || '—' }}</span></div>
          <div class="info-row"><span class="info-label">Должность</span><span class="info-value">{{ user.position || '—' }}</span></div>
          <div class="info-row"><span class="info-label">Отдел/служба</span><span class="info-value">{{ departmentName(user.departmentId) }}</span></div>
          <div v-if="user.globalRole === 'manager' && managedDepartments" class="info-row">
            <span class="info-label">Руководит</span><span class="info-value">{{ managedDepartments }}</span>
          </div>
        </div>

        <div class="section-title password-title">
          <span>Пароль</span>
          <button class="btn btn-sm btn-ghost" @click="togglePasswordForm">
            {{ showPasswordForm ? 'Отмена' : 'Сменить пароль' }}
          </button>
        </div>

        <div v-if="showPasswordForm" class="password-form">
          <label class="field">
            <span>Текущий пароль</span>
            <input v-model="passwordForm.currentPassword" type="password" autocomplete="current-password" />
          </label>
          <label class="field">
            <span>Новый пароль</span>
            <input v-model="passwordForm.newPassword" type="password" autocomplete="new-password" placeholder="минимум 8 символов" />
          </label>
          <label class="field">
            <span>Повторите новый пароль</span>
            <input v-model="passwordForm.confirmPassword" type="password" autocomplete="new-password" @keyup.enter="submitPasswordChange" />
          </label>
          <p v-if="passwordError" class="error-text">{{ passwordError }}</p>
          <div class="password-form-actions">
            <button class="btn btn-sm btn-primary" :disabled="changingPassword" @click="submitPasswordChange">
              {{ changingPassword ? 'Сохранение...' : 'Сохранить новый пароль' }}
            </button>
          </div>
        </div>
        <p v-if="passwordSuccess" class="success-text">{{ passwordSuccess }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { width: 420px; max-height: 85vh; padding: 0; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 10px; }
.modal-header h3 { margin: 0; font-size: 15px; }
.modal-body { padding: 4px 18px 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }

.profile-hero { display: flex; align-items: center; gap: 14px; padding: 6px 0 4px; }
.avatar-wrap { position: relative; width: 64px; height: 64px; flex-shrink: 0; }
.avatar-img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; display: block; }
.avatar-fallback {
  width: 64px; height: 64px; border-radius: 50%; color: #fff; display: flex; align-items: center;
  justify-content: center; font-size: 22px; font-weight: 700;
}
.avatar-edit-btn {
  position: absolute; bottom: -2px; right: -2px; width: 24px; height: 24px; border-radius: 50%;
  background: var(--color-primary); color: #fff; border: 2px solid #fff; display: flex; align-items: center;
  justify-content: center; cursor: pointer;
}
.avatar-edit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.file-input-hidden { display: none; }
.profile-heading { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.profile-name { font-size: 17px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; }
.profile-role-badge {
  font-size: 11px; font-weight: 700; background: #eaf0ff; color: var(--color-primary); padding: 2px 9px;
  border-radius: 10px; width: fit-content;
}
.avatar-actions { display: flex; gap: 8px; }

.section-title {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted);
  margin-top: 8px; border-top: 1px solid var(--color-border); padding-top: 10px;
  display: flex; align-items: center; justify-content: space-between;
}
.password-title { text-transform: uppercase; }
.info-grid { display: flex; flex-direction: column; gap: 6px; }
.info-row { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; }
.info-label { color: var(--color-text-muted); }
.info-value { font-weight: 600; text-align: right; overflow: hidden; text-overflow: ellipsis; }

.password-form { display: flex; flex-direction: column; gap: 10px; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; }
.field input { border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 9px; font-size: 13px; }
.password-form-actions { display: flex; justify-content: flex-end; }
.error-text { color: #d64545; font-size: 12px; margin: 0; }
.success-text { color: var(--color-success); font-size: 12px; margin: 0; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
