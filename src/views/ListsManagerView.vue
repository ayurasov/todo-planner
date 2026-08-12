<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useListsStore } from '../stores/listsStore'
import { useUsersStore } from '../stores/usersStore'
import { useTasksStore } from '../stores/tasksStore'
import { ListRole } from '../domain/entities/enums'
import { useDragReorder } from '../composables/useDragReorder'
import ListSettingsModal from '../components/common/ListSettingsModal.vue'
import AppIcon from '../components/common/AppIcon.vue'
import ConfirmModal from '../components/common/ConfirmModal.vue'

const router = useRouter()
const listsStore = useListsStore()
const usersStore = useUsersStore()
const tasksStore = useTasksStore()

const showCreate = ref(false)
const editingList = ref(null)
const memberPickerListId = ref(null)
const memberPickerUserId = ref(null)
const memberPickerRole = ref(ListRole.VIEWER)
const showArchived = ref(false)

// Раньше удаление списка подтверждалось нативным window.confirm() — единственное
// оставшееся такое место в приложении. listPendingRemoval хранит сам список,
// чтобы модалка могла показать его название и количество задач при подтверждении.
const listPendingRemoval = ref(null)

const ROLE_LABEL = { owner: 'Владелец', editor: 'Редактор', assignee: 'Исполнитель', viewer: 'Наблюдатель' }
const ROLE_COLOR = { owner: '#e5484d', editor: '#4f7cff', assignee: '#1e9e4d', viewer: '#9aa3b2' }

// Пустая заготовка списка для ListSettingsModal в режиме создания — та же
// форма, что используется для редактирования, чтобы не поддерживать два
// разных UI для создания и настройки списка (см. запрос пользователя).
const blankList = computed(() => ({ title: '', description: '', color: '#4f7cff', settings: {} }))

const visibleLists = computed(() => (showArchived.value ? listsStore.archivedLists : listsStore.activeLists))

// Единая логика drag-n-drop с живым предпросмотром (см. useDragReorder) —
// при перетаскивании соседние карточки сразу раздвигаются на новое место,
// а не только после отпускания мыши, и есть зона для сброса в конец списка.
const { draggingId, displayItems, startDrag, dragOver, dragOverEnd, endDrag, cancelDrag } = useDragReorder(
  visibleLists,
  (orderedIds) => listsStore.reorderLists(orderedIds),
)

const rows = computed(() => displayItems.value.map((list) => ({
  list,
  members: listsStore.memberships[list.id] || [],
  taskCount: tasksStore.tasks.filter((t) => t.listId === list.id).length,
})))

const listPendingRemovalTaskCount = computed(() => {
  if (!listPendingRemoval.value) return 0
  return tasksStore.tasks.filter((t) => t.listId === listPendingRemoval.value.id).length
})

const listPendingRemovalMessage = computed(() => {
  if (!listPendingRemoval.value) return ''
  const count = listPendingRemovalTaskCount.value
  return count
    ? `Удалить список «${listPendingRemoval.value.title}»? ${count} задач(и) останутся, но потеряют привязку к нему.`
    : `Удалить список «${listPendingRemoval.value.title}»?`
})

async function handleCreate(payload) {
  await listsStore.createList(payload)
  showCreate.value = false
}

// Раньше удалить список было вообще нельзя: MockListRepository.remove() существовал,
// но listsStore не имел соответствующего action и, главное, в UI вообще не было
// кнопки удаления. Задачи удаляемого списка отвязываются (listId = null),
// по аналогии с удалением встречи в MeetingDetailView.vue, а не удаляются вместе со списком.
function requestRemoveList(list) {
  listPendingRemoval.value = list
}

function cancelRemoveList() {
  listPendingRemoval.value = null
}

async function confirmRemoveList() {
  const list = listPendingRemoval.value
  if (!list) return
  for (const t of tasksStore.tasks.filter((x) => x.listId === list.id)) {
    await tasksStore.updateTaskField(t.id, 'listId', null)
  }
  await listsStore.removeList(list.id)
  listPendingRemoval.value = null
}

function openList(listId) {
  router.push(`/lists/${listId}`)
}

function openMemberPicker(listId) {
  memberPickerListId.value = memberPickerListId.value === listId ? null : listId
  memberPickerUserId.value = null
  memberPickerRole.value = ListRole.VIEWER
}

async function addMember() {
  // Раньше при отсутствии выбранного пользователя запрос всё равно уходил в
  // repository с userId = null, который пытался найти несуществующего
  // пользователя и «зависал»/падал в бесконечный reactive-цикл обновления —
  // это и была «ошибочная заявка», из-за которой страница подвисала.
  // Явная проверка + try/finally гарантируют, что picker закрывается
  // в любом случае и страница не зависает даже при ошибке репозитория.
  if (!memberPickerUserId.value || !memberPickerListId.value) return
  try {
    await listsStore.addMember(memberPickerListId.value, memberPickerUserId.value, memberPickerRole.value)
  } finally {
    memberPickerListId.value = null
  }
}

function availableUsers(listId) {
  const memberIds = new Set((listsStore.memberships[listId] || []).map((m) => m.userId))
  return usersStore.users.filter((u) => !memberIds.has(u.id))
}
</script>

<template>
  <div class="view-header">
    <div>
      <h2>Управление списками</h2>
      <p class="subtitle">Единая страница для создания списков, настройки доступа и параметров — вместо разрозненных настроек по каждому списку.</p>
    </div>
    <div class="header-actions">
      <button class="btn btn-ghost btn-sm" :class="{ active: showArchived }" @click="showArchived = !showArchived">
        <AppIcon name="folder" :size="13" /> {{ showArchived ? 'К активным' : 'Архив' }}
      </button>
      <button v-if="!showArchived" class="btn btn-primary btn-sm" @click="showCreate = true"><AppIcon name="plus" :size="13" /> Новый список</button>
    </div>
  </div>

  <p v-if="!rows.length" class="empty-state">{{ showArchived ? 'В архиве пока пусто.' : 'Списков пока нет — создайте первый.' }}</p>

  <TransitionGroup tag="div" name="fade" class="lists-grid" @dragleave.self="dragOverEnd" @dragover.prevent @drop="endDrag">
    <div
      v-for="row in rows" :key="row.list.id" class="card list-card fade-move"
      :class="{ dragging: draggingId === row.list.id }"
      draggable="true"
      @dragstart="startDrag(row.list.id)"
      @dragenter.prevent="dragOver(row.list.id)"
      @dragover.prevent
      @dragend="cancelDrag"
      @drop.stop="endDrag"
    >
      <div class="list-card-head">
        <span class="drag-handle" title="Перетащить для сортировки"><AppIcon name="menu" :size="14" /></span>
        <button class="list-icon-badge list-icon-badge-btn" :style="{ background: row.list.color + '22', color: row.list.color }" title="Открыть список" @click="openList(row.list.id)">
          <AppIcon :name="row.list.settings?.icon || 'folder'" :size="16" />
        </button>
        <div class="list-card-title">
          <button class="list-title-btn" title="Открыть список" @click="openList(row.list.id)">{{ row.list.title }}</button>
          <span class="list-card-meta">{{ row.taskCount }} задач · {{ row.members.length }} участников</span>
        </div>
        <div class="list-card-head-actions">
          <button class="btn btn-ghost btn-icon btn-sm" title="Открыть список" @click="openList(row.list.id)"><AppIcon name="chevronRight" :size="14" /></button>
          <button class="btn btn-ghost btn-icon btn-sm" title="Настроить" @click="editingList = row.list"><AppIcon name="settings" :size="14" /></button>
          <button
            class="btn btn-ghost btn-icon btn-sm" :title="row.list.archived ? 'Вернуть из архива' : 'Архивировать список'"
            @click="row.list.archived ? listsStore.unarchiveList(row.list.id) : listsStore.archiveList(row.list.id)"
          ><AppIcon :name="row.list.archived ? 'undo' : 'copy'" :size="14" /></button>
          <button class="btn btn-ghost btn-icon btn-sm btn-danger-ghost" title="Удалить список" @click="requestRemoveList(row.list)"><AppIcon name="trash" :size="14" /></button>
        </div>
      </div>

      <p v-if="row.list.description" class="list-card-desc">{{ row.list.description }}</p>

      <div v-if="row.list.settings?.recurringMeeting?.enabled" class="meeting-badge">
        <AppIcon name="calendar" :size="13" /> {{ row.list.settings.recurringMeeting.title || 'Регулярная встреча' }}
        <a v-if="row.list.settings.recurringMeeting.link" :href="row.list.settings.recurringMeeting.link" target="_blank" class="meeting-link" @click.stop>Ссылка</a>
      </div>

      <div class="members-section">
        <div class="members-row">
          <span v-for="m in row.members" :key="m.id" class="member-chip" :style="{ borderColor: ROLE_COLOR[m.role] }">
            <span class="mini-avatar">{{ usersStore.byId(m.userId)?.name?.charAt(0) || '?' }}</span>
            {{ usersStore.byId(m.userId)?.name || m.userId }}
            <select
              class="role-select" :value="m.role"
              :style="{ color: ROLE_COLOR[m.role] }"
              @change="listsStore.updateMemberRole(row.list.id, m.userId, $event.target.value)"
            >
              <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
            </select>
            <button class="chip-remove" @click="listsStore.removeMember(row.list.id, m.userId)"><AppIcon name="close" :size="10" /></button>
          </span>
          <button class="btn btn-ghost btn-sm add-member-btn" @click="openMemberPicker(row.list.id)"><AppIcon name="plus" :size="12" /> Участник</button>
        </div>

        <div v-if="memberPickerListId === row.list.id" class="member-picker">
          <select v-model="memberPickerUserId">
            <option :value="null" disabled>Выберите пользователя</option>
            <option v-for="u in availableUsers(row.list.id)" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
          <select v-model="memberPickerRole">
            <option v-for="(label, role) in ROLE_LABEL" :key="role" :value="role">{{ label }}</option>
          </select>
          <button class="btn btn-primary btn-sm" :disabled="!memberPickerUserId" @click="addMember">Добавить</button>
        </div>
      </div>
    </div>
  </TransitionGroup>

  <ListSettingsModal v-if="editingList" :list="editingList" @close="editingList = null" />
  <ListSettingsModal v-if="showCreate" :list="blankList" create-mode @close="showCreate = false" @create="handleCreate" />

  <ConfirmModal
    v-if="listPendingRemoval"
    title="Удалить список?"
    :message="listPendingRemovalMessage"
    confirm-text="Удалить"
    @confirm="confirmRemoveList"
    @cancel="cancelRemoveList"
  />
</template>

<style scoped>
.view-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 20px; }
.view-header h2 { margin: 0 0 4px; font-size: 19px; }
.subtitle { margin: 0; font-size: 12.5px; color: var(--color-text-muted); max-width: 480px; }
.header-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.header-actions .active { background: #eef2ff; border-color: #cfd8ff; color: var(--color-primary-dark); }
.empty-state { color: var(--color-text-muted); font-size: 13px; text-align: center; padding: 40px 0; }
.lists-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; min-height: 40px; }
.list-card { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.list-card.dragging { opacity: 0.35; }
.list-card-head { display: flex; align-items: flex-start; gap: 10px; min-width: 0; }
.drag-handle { color: var(--color-text-muted); cursor: grab; padding-top: 8px; flex-shrink: 0; }
.list-icon-badge { width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.list-icon-badge-btn { border: none; cursor: pointer; padding: 0; }
.list-icon-badge-btn:hover { filter: brightness(0.95); }
.list-card-title { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.list-title-btn { border: none; background: none; padding: 0; text-align: left; font-weight: 700; font-size: 14px; cursor: pointer; color: var(--color-text); }
.list-title-btn:hover { color: var(--color-primary); text-decoration: underline; }
.list-card-meta { font-size: 11.5px; color: var(--color-text-muted); }
.list-card-desc { margin: 0; font-size: 12.5px; color: var(--color-text-muted); }
.list-card-head-actions { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.btn-danger-ghost { color: var(--color-danger); }
.btn-danger-ghost:hover { background: #fdeceb; }
.meeting-badge { font-size: 12px; background: #eef2ff; color: var(--color-primary-dark); border-radius: 8px; padding: 6px 10px; display: flex; align-items: center; gap: 8px; }
.meeting-link { color: var(--color-primary); font-weight: 600; text-decoration: none; }
.members-section { border-top: 1px solid var(--color-border); padding-top: 10px; min-width: 0; }
.members-row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.member-chip {
  display: flex; align-items: center; gap: 5px; border: 1px solid var(--color-border); border-radius: 16px;
  padding: 3px 6px 3px 3px; font-size: 11.5px; max-width: 100%;
}
.mini-avatar { width: 18px; height: 18px; border-radius: 50%; background: var(--color-primary); color: #fff; font-size: 9px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.role-select { border: none; background: none; font-size: 10.5px; font-weight: 600; cursor: pointer; max-width: 90px; }
.chip-remove { border: none; background: none; cursor: pointer; color: var(--color-text-muted); padding: 0 2px; display: flex; align-items: center; flex-shrink: 0; }
.add-member-btn { border-radius: 16px; }

/* .member-picker переносит содержимое на новую строку внутри карточки
 * (flex-wrap + min-width:0 на select), а не вылезает за её правый край,
 * как это было раньше на узких карточках грида. */
.member-picker { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; max-width: 100%; }
.member-picker select { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12px; min-width: 0; flex: 1 1 120px; max-width: 100%; }
.member-picker .btn { flex-shrink: 0; }
</style>
