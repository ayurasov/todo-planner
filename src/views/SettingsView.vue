<script setup>
import { onMounted } from 'vue'
import { useCalendarStore } from '../stores/calendarStore'
import ViewSettingsPanel from '../components/common/ViewSettingsPanel.vue'

const calendarStore = useCalendarStore()

onMounted(() => calendarStore.refreshStatus())

async function toggleCalendar() {
  if (calendarStore.status === 'connected') await calendarStore.disconnect()
  else await calendarStore.connect({ provider: 'exchange' })
}
</script>

<template>
  <div class="view-header"><h2>Настройки</h2></div>

  <section class="card settings-section">
    <h3>Вид и отображение</h3>
    <p class="hint-text">Единая настройка отображения задач для всех экранов (список, группировка, сортировка, видимость полей).</p>
    <ViewSettingsPanel />
  </section>

  <section class="card settings-section">
    <h3>Интеграция с календарём (Exchange)</h3>
    <p class="hint-text">
      Опциональная интеграция для отображения занятости и регулярных встреч. Сейчас используется mock-провайдер;
      реальное подключение к Exchange будет добавлено отдельным этапом.
    </p>
    <div class="calendar-status">
      <span class="status-badge" :class="calendarStore.status">{{ calendarStore.status }}</span>
      <button class="btn btn-sm" @click="toggleCalendar">
        {{ calendarStore.status === 'connected' ? 'Отключить' : 'Подключить (mock)' }}
      </button>
      <button v-if="calendarStore.status === 'connected'" class="btn btn-ghost btn-sm" @click="calendarStore.resync">Ресинк</button>
    </div>
    <div v-if="calendarStore.busySlots.length" class="busy-slots">
      <div v-for="(slot, i) in calendarStore.busySlots" :key="i" class="slot-row">{{ slot.title }} — {{ slot.start }}</div>
    </div>
  </section>
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.settings-section { padding: 16px 18px; margin-bottom: 14px; }
.settings-section h3 { margin: 0 0 10px; font-size: 14px; }
.hint-text { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 10px; }
.calendar-status { display: flex; align-items: center; gap: 10px; }
.status-badge { padding: 3px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; background: #eef1f7; }
.status-badge.connected { background: #e1f5eb; color: var(--color-success); }
.busy-slots { margin-top: 10px; font-size: 12.5px; color: var(--color-text-muted); }
</style>
