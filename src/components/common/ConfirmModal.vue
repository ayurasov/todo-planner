<script setup>
// Универсальное модальное окно подтверждения — заменяет браузерный
// window.confirm(), который выглядит инородно и не вписывается в дизайн
// приложения. Используется, например, для подтверждения удаления задачи
// в TaskContextMenu.vue.
defineProps({
  title: { type: String, default: 'Подтвердите действие' },
  message: { type: String, required: true },
  confirmText: { type: String, default: 'Удалить' },
  cancelText: { type: String, default: 'Отмена' },
  danger: { type: Boolean, default: true },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <Teleport to="body">
    <div class="confirm-overlay" @click.self="emit('cancel')">
      <div class="confirm-modal card">
        <h3 class="confirm-title">{{ title }}</h3>
        <p class="confirm-message">{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn btn-ghost" @click="emit('cancel')">{{ cancelText }}</button>
          <button class="btn" :class="danger ? 'btn-danger' : 'btn-primary'" @click="emit('confirm')">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed; inset: 0; background: rgba(20,25,40,0.4); display: flex;
  align-items: center; justify-content: center; z-index: 300;
}
.confirm-modal { width: 340px; padding: 20px 20px 16px; }
.confirm-title { margin: 0 0 8px; font-size: 15px; }
.confirm-message { margin: 0 0 16px; font-size: 13px; color: var(--color-text-muted); line-height: 1.5; }
.confirm-actions { display: flex; justify-content: flex-end; gap: 8px; }
.btn-danger { background: var(--color-danger); color: #fff; border: 1px solid var(--color-danger); }
.btn-danger:hover { background: #d33f44; }
</style>
