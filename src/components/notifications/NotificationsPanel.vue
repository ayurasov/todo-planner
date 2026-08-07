<script setup>
import { ref } from 'vue'
import { useClickOutside } from '../../composables/useClickOutside'
import { useNotificationsStore } from '../../stores/notificationsStore'
import { useUiStore } from '../../stores/uiStore'
import { NOTIFICATION_LABEL } from '../../domain/entities/enums'
import { formatDateTime } from '../../utils/formatters'
import NotificationSettingsModal from './NotificationSettingsModal.vue'
import AppIcon from '../common/AppIcon.vue'

const emit = defineEmits(['close'])
const notificationsStore = useNotificationsStore()
const uiStore = useUiStore()
const panelEl = ref(null)
const showSettings = ref(false)

useClickOutside(panelEl, () => { if (!showSettings.value) emit('close') })

const TYPE_ICON = {
  assigned: 'team', due_soon: 'alarm', overdue: 'warning', comment: 'message', mention: 'tag',
  status_changed: 'repeat', rescheduled: 'calendar', subtask_completed: 'check', list_invite: 'mail',
}

function openNotification(n) {
  notificationsStore.markRead(n.id)
  if (n.taskId) uiStore.openTask(n.taskId)
  emit('close')
}
</script>

<template>
  <div ref="panelEl" class="notif-panel card" @click.stop>
    <div class="notif-header">
      <span class="notif-title">Уведомления</span>
      <div class="notif-actions">
        <button class="btn btn-ghost btn-sm" @click="notificationsStore.markAllRead()">Прочитать все</button>
        <button class="icon-btn-sm" title="Настройки уведомлений" @click="showSettings = true"><AppIcon name="settings" :size="14" /></button>
      </div>
    </div>

    <div class="notif-list scroll-thin">
      <button
        v-for="n in notificationsStore.sorted" :key="n.id"
        class="notif-item" :class="{ unread: !n.read }"
        @click="openNotification(n)"
      >
        <span class="notif-icon"><AppIcon :name="TYPE_ICON[n.type] || 'bell'" :size="15" /></span>
        <div class="notif-body">
          <span class="notif-item-title">{{ n.title }}</span>
          <span v-if="n.body" class="notif-item-body">{{ n.body }}</span>
          <span class="notif-item-meta">{{ NOTIFICATION_LABEL[n.type] }} · {{ formatDateTime(n.createdAt) }}</span>
        </div>
        <span v-if="!n.read" class="unread-dot" />
      </button>
      <div v-if="!notificationsStore.sorted.length" class="notif-empty">Нет уведомлений</div>
    </div>

    <NotificationSettingsModal v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<style scoped>
.notif-panel {
  position: absolute; top: calc(100% + 8px); right: 0; width: 360px; max-height: 460px;
  display: flex; flex-direction: column; z-index: 60; padding: 0; box-shadow: var(--shadow-2);
}
.notif-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid var(--color-border); }
.notif-title { font-size: 13.5px; font-weight: 700; }
.notif-actions { display: flex; align-items: center; gap: 4px; }
.icon-btn-sm { border: none; background: none; cursor: pointer; padding: 4px; border-radius: 6px; display: flex; align-items: center; color: var(--color-text-muted); }
.icon-btn-sm:hover { background: #eef1f7; color: var(--color-text); }
.notif-list { overflow-y: auto; max-height: 380px; padding: 4px; }
.notif-item {
  display: flex; align-items: flex-start; gap: 10px; width: 100%; text-align: left; border: none; background: none;
  padding: 10px 10px; border-radius: 10px; cursor: pointer; position: relative;
}
.notif-item:hover { background: #f1f3f9; }
.notif-item.unread { background: #f7f9ff; }
.notif-icon { margin-top: 1px; color: var(--color-text-muted); display: flex; }
.notif-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.notif-item-title { font-size: 13px; font-weight: 500; }
.notif-item-body { font-size: 12px; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notif-item-meta { font-size: 10.5px; color: var(--color-text-muted); }
.unread-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-primary); margin-top: 5px; flex-shrink: 0; }
.notif-empty { padding: 30px; text-align: center; color: var(--color-text-muted); font-size: 12.5px; }
</style>
