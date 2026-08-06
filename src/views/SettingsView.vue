<script setup>
import { ref, onMounted } from 'vue'
import { useListsStore } from '../stores/listsStore'
import { useUsersStore } from '../stores/usersStore'
import { useCalendarStore } from '../stores/calendarStore'
import { ListRole } from '../domain/entities/enums'
import ViewSettingsPanel from '../components/common/ViewSettingsPanel.vue'

const listsStore = useListsStore()
const usersStore = useUsersStore()
const calendarStore = useCalendarStore()

const selectedListId = ref(listsStore.lists[0]?.id || null)
const newMemberId = ref(null)
const newMemberRole = ref(ListRole.VIEWER)

onMounted(() => calendarStore.refreshStatus())

async function addMember() {
  if (!newMemberId.value) return
  await listsStore.addMember(selectedListId.value, newMemberId.value, newMemberRole.value)
}

async function toggleCalendar() {
  if (calendarStore.status === 'connected') await calendarStore.disconnect()
  else await calendarStore.connect({ provider: 'exchange' })
}

const ROLE_LABEL = { owner: 'Владелец', editor: 'Редактор', assignee: 'Исполнитель', viewer: 'Наблюдатель' }
</script>

<template>
  <div class="view-header"><h2>Настройки</h2></div>

  <section class="card settings-section">
    <h3>Вид и отображение</h3>
    <p class="hint-text">Единая настройка отображения задач для всех экранов (список, группировка, сортировка, видимость полей).</p>
    <ViewSettingsPanel />
  </section>

  <section class="card settings-section">
    <h3>Управление доступом к спискам</h3>
    <select v-model="selectedListId" class="list-select">
      <option v-for="l in listsStore.lists" :key="l.id" :value="l.id">{{ l.title }}</option>
    </select>

    <div class="members-table" v-if="selectedListId">
      <div v-for="m in listsStore.memberships[selectedListId]" :key="m.id" class="member-row">
        <span>{{ usersStore.byId(m.userId)?.name }}</span>
        <select :value="m.role" @change="listsStore.updateMemberRole(selectedListId, m.userId, $event.target.value)">
          <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
        </select>
        <button class="btn btn-ghost btn-sm btn-danger" @click="listsStore.removeMember(selectedListId, m.userId)">Убрать</button>
      </div>
    </div>

    <div class="add-member-row">
      <select v-model="newMemberId">
        <option :value="null">Выбрать пользователя</option>
        <option v-for="u in usersStore.users" :key="u.id" :value="u.id">{{ u.name }}</option>
      </select>
      <select v-model="newMemberRole">
        <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
      </select>
      <button class="btn btn-primary btn-sm" @click="addMember">Добавить</button>
    </div>
  </section>

  <section class="card settings-section">
    <h3>Интеграция с календарём (Exchange)</h3>
    <p class="hint-text">
      Опциональная интеграция для отображения занятости и регулярных встреч. В MVP используется mock-провайдер;
      реальное подключение к Exchange запланировано как отдельный этап v2.
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

  <section class="card settings-section">
    <h3>Геолокационные напоминания</h3>
    <p class="hint-text">
      Функция спроектирована как UX-абстракция (ReminderTrigger с type=location). Фактическое срабатывание
      ограничено возможностями браузера (Geolocation API) и требует явного разрешения пользователя.
    </p>
  </section>
</template>

<style scoped>
.view-header { margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.settings-section { padding: 16px 18px; margin-bottom: 14px; }
.settings-section h3 { margin: 0 0 10px; font-size: 14px; }
.hint-text { font-size: 12.5px; color: var(--color-text-muted); margin-bottom: 10px; }
.list-select { margin-bottom: 10px; border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 10px; }
.member-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--color-border); font-size: 13px; }
.member-row span:first-child { flex: 1; }
.add-member-row { display: flex; gap: 8px; margin-top: 10px; }
.add-member-row select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 10px; }
.calendar-status { display: flex; align-items: center; gap: 10px; }
.status-badge { padding: 3px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; background: #eef1f7; }
.status-badge.connected { background: #e1f5eb; color: var(--color-success); }
.busy-slots { margin-top: 10px; font-size: 12.5px; color: var(--color-text-muted); }
</style>
