<script setup>
import { useNotificationsStore } from '../../stores/notificationsStore'
import { NOTIFICATION_LABEL } from '../../domain/entities/enums'
import AppIcon from '../common/AppIcon.vue'

const emit = defineEmits(['close'])
const notificationsStore = useNotificationsStore()

const TYPE_GROUPS = [
  { title: 'Задачи и назначения', types: ['assigned', 'status_changed', 'rescheduled', 'subtask_completed'] },
  { title: 'Сроки', types: ['due_soon', 'overdue'] },
  { title: 'Общение', types: ['comment', 'mention'] },
  { title: 'Списки', types: ['list_invite'] },
]

function setThreshold(e) {
  notificationsStore.saveSettings({ dueSoonThresholdHours: Number(e.target.value) })
}
</script>

<template>
  <div class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Настройки уведомлений</h3>
        <button class="btn btn-ghost btn-sm" @click="emit('close')"><AppIcon name="close" :size="13" /></button>
      </div>

      <div class="modal-body">
        <div class="section">
          <div class="section-title">Каналы доставки</div>
          <label class="checkbox-row">
            <input type="checkbox" :checked="notificationsStore.settings.channels.in_app" @change="notificationsStore.toggleChannel('in_app')" />
            В приложении (колокольчик)
          </label>
          <label class="checkbox-row">
            <input type="checkbox" :checked="notificationsStore.settings.channels.email" @change="notificationsStore.toggleChannel('email')" />
            E-mail (заглушка, реализуется в v2)
          </label>
        </div>

        <div class="section">
          <div class="section-title">Режим доставки</div>
          <div class="segmented">
            <button
              :class="{ active: notificationsStore.settings.digestMode === 'instant' }"
              @click="notificationsStore.saveSettings({ digestMode: 'instant' })"
            >Мгновенно</button>
            <button
              :class="{ active: notificationsStore.settings.digestMode === 'daily_digest' }"
              @click="notificationsStore.saveSettings({ digestMode: 'daily_digest' })"
            >Дневной дайджест</button>
          </div>
          <p class="hint-text">Дневной дайджест группирует уведомления и показывает их одной сводкой (снижает шум при высокой активности команды).</p>
        </div>

        <div class="section">
          <div class="section-title">Порог "срок приближается"</div>
          <select :value="notificationsStore.settings.dueSoonThresholdHours" @change="setThreshold">
            <option :value="1">За 1 час</option>
            <option :value="4">За 4 часа</option>
            <option :value="24">За 24 часа</option>
            <option :value="48">За 48 часов</option>
            <option :value="168">За неделю</option>
          </select>
        </div>

        <div class="section">
          <div class="section-title">Тихие часы</div>
          <label class="checkbox-row">
            <input type="checkbox" :checked="notificationsStore.settings.quietHoursEnabled" @change="notificationsStore.saveSettings({ quietHoursEnabled: !notificationsStore.settings.quietHoursEnabled })" />
            Не уведомлять громко в указанный период
          </label>
          <div v-if="notificationsStore.settings.quietHoursEnabled" class="quiet-hours-row">
            <input type="time" :value="notificationsStore.settings.quietHoursStart" @change="notificationsStore.saveSettings({ quietHoursStart: $event.target.value })" />
            <span>—</span>
            <input type="time" :value="notificationsStore.settings.quietHoursEnd" @change="notificationsStore.saveSettings({ quietHoursEnd: $event.target.value })" />
          </div>
        </div>

        <div v-for="group in TYPE_GROUPS" :key="group.title" class="section">
          <div class="section-title">{{ group.title }}</div>
          <label v-for="t in group.types" :key="t" class="checkbox-row">
            <input type="checkbox" :checked="notificationsStore.settings.types[t]" @change="notificationsStore.toggleType(t)" />
            {{ NOTIFICATION_LABEL[t] }}
          </label>
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn btn-primary" @click="emit('close')">Готово</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex; align-items: center; justify-content: center; z-index: 150; }
.modal { width: 440px; max-height: 85vh; padding: 0; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 10px; }
.modal-header h3 { margin: 0; font-size: 15px; }
.modal-body { padding: 4px 18px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.section { display: flex; flex-direction: column; gap: 6px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border); }
.section:last-child { border-bottom: none; }
.section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted); font-weight: 700; }
.checkbox-row { display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; }
.hint-text { font-size: 11.5px; color: var(--color-text-muted); line-height: 1.5; margin: 2px 0 0; }
select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 9px; font-size: 13px; max-width: 220px; }
.segmented { display: flex; gap: 4px; max-width: 280px; }
.segmented button { flex: 1; border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 6px; padding: 6px 8px; font-size: 12px; cursor: pointer; }
.segmented button.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.quiet-hours-row { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.quiet-hours-row input { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--color-border); }
</style>
