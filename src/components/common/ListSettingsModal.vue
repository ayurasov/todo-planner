<script setup>
import { reactive, ref, nextTick } from 'vue'
import { useListsStore } from '../../stores/listsStore'
import { useClickOutside } from '../../composables/useClickOutside'
import { GroupByMode, SortField, GROUP_LABEL, SORT_LABEL, WEEKDAY_LABEL, MEETING_FREQ_LABEL } from '../../domain/entities/enums'
import AppIcon from './AppIcon.vue'
import RichTextEditor from './RichTextEditor.vue'

const props = defineProps({
  list: { type: Object, required: true },
  createMode: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'create'])
const listsStore = useListsStore()

// Набор иконок для списка построен на тех же именах из AppIcon.vue,
// которые используются во всём остальном приложении — раньше тут
// были emoji, которые выглядели старомодно и не совпадали со
// стилем AppIcon, используемым для отображения значка списка в карточках
// (ListsManagerView.vue). Выбор иконки теперь действительно меняет вид значка
// на карточке списка, а не только его цвет.
const ICON_OPTIONS = [
  'folder', 'list', 'checklist', 'calendar', 'pin', 'flag', 'star', 'bell',
  'tag', 'team', 'message', 'link', 'shield', 'repeat', 'eye', 'settings',
]

const form = reactive({
  title: props.list.title || '',
  description: props.list.description || '',
  color: props.list.color || '#4f7cff',
  icon: props.list.settings?.icon || 'folder',
  allowComments: true,
  allowGuestViewers: false,
  defaultGroupBy: GroupByMode.NONE,
  defaultSortField: SortField.SCORE,
  showCompletedByDefault: false,
  autoArchiveDoneAfterDays: 0,
  requireDueDateOnCreate: false,
  allowedViews: ['list', 'tree', 'grouped'],
  ...props.list.settings,
  recurringMeeting: {
    enabled: false,
    title: '',
    description: '',
    link: '',
    dayOfWeek: 'monday',
    time: '10:00',
    frequency: 'weekly',
    ...(props.list.settings?.recurringMeeting || {}),
  },
})

const iconPickerOpen = ref(false)
const iconTriggerEl = ref(null)
const iconGridEl = ref(null)
const iconGridPos = ref({ top: 0, left: 0 })
useClickOutside(iconGridEl, () => { iconPickerOpen.value = false }, iconTriggerEl)

function toggleIconPicker() {
  if (iconPickerOpen.value) {
    iconPickerOpen.value = false
    return
  }
  nextTick(() => {
    const rect = iconTriggerEl.value.getBoundingClientRect()
    const margin = 8
    const gridW = 200
    let left = Math.min(rect.left, window.innerWidth - gridW - margin)
    let top = rect.bottom + 4
    if (top + 200 > window.innerHeight - margin) top = Math.max(margin, rect.top - 200 - 4)
    iconGridPos.value = { top, left }
    iconPickerOpen.value = true
  })
}

function pickIcon(icon) {
  form.icon = icon
  iconPickerOpen.value = false
}

function buildSettingsPatch() {
  return {
    allowComments: form.allowComments,
    allowGuestViewers: form.allowGuestViewers,
    defaultGroupBy: form.defaultGroupBy,
    defaultSortField: form.defaultSortField,
    showCompletedByDefault: form.showCompletedByDefault,
    autoArchiveDoneAfterDays: form.autoArchiveDoneAfterDays,
    requireDueDateOnCreate: form.requireDueDateOnCreate,
    allowedViews: form.allowedViews,
    icon: form.icon,
    recurringMeeting: { ...form.recurringMeeting },
  }
}

async function save() {
  if (!form.title.trim()) return
  if (props.createMode) {
    emit('create', { title: form.title.trim(), description: form.description, color: form.color, settings: buildSettingsPatch() })
  } else {
    await listsStore.updateList(props.list.id, {
      title: form.title,
      description: form.description,
      color: form.color,
      settings: buildSettingsPatch(),
    })
    emit('close')
  }
}

function toggleView(view) {
  const idx = form.allowedViews.indexOf(view)
  if (idx === -1) form.allowedViews.push(view)
  else if (form.allowedViews.length > 1) form.allowedViews.splice(idx, 1)
}
</script>

<template>
  <!-- Клик по overlay (вне окна) не должен закрывать модалку создания/редактирования
       списка — чтобы случайный клик рядом с окном не стирал введённые данные.
       Закрытие — только кнопками "Отмена"/крестик в шагалке. -->
  <div class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>{{ createMode ? 'Новый список' : 'Настройки списка' }}</h3>
        <button class="btn btn-ghost btn-icon btn-sm" @click="emit('close')"><AppIcon name="close" :size="13" /></button>
      </div>

      <div class="modal-body">
        <div class="field-group">
          <label>Название</label>
          <input v-model="form.title" placeholder="Название списка" @keyup.enter="save" />
        </div>
        <div class="field-group">
          <label>Описание</label>
          <RichTextEditor v-model="form.description" placeholder="Описание списка..." />
        </div>
        <div class="field-row">
          <div class="field-group">
            <label>Цвет</label>
            <input v-model="form.color" type="color" />
          </div>
          <div class="field-group icon-picker-group">
            <label>Иконка</label>
            <button ref="iconTriggerEl" type="button" class="icon-trigger" @click="toggleIconPicker">
              <span class="icon-preview" :style="{ background: form.color + '22', color: form.color }"><AppIcon :name="form.icon" :size="15" /></span>
              <AppIcon name="chevronDown" :size="11" />
            </button>
          </div>
        </div>

        <div class="section-title">Совместный доступ и инструментарий</div>
        <label class="checkbox-row"><input type="checkbox" v-model="form.allowComments" /> Разрешить комментарии в этом списке</label>
        <label class="checkbox-row"><input type="checkbox" v-model="form.allowGuestViewers" /> Разрешить приглашённых наблюдателей извне команды</label>
        <label class="checkbox-row"><input type="checkbox" v-model="form.requireDueDateOnCreate" /> Требовать срок при создании задачи</label>
        <label class="checkbox-row"><input type="checkbox" v-model="form.showCompletedByDefault" /> Показывать выполненные по умолчанию</label>

        <div class="field-group">
          <label>Автоархивация выполненных (дней)</label>
          <input v-model.number="form.autoArchiveDoneAfterDays" type="number" min="0" />
        </div>

        <div class="section-title">Регулярная встреча / звонок</div>
        <p class="hint-text">Опишите регулярный созвон, привязанный к этому списку.</p>
        <label class="checkbox-row"><input type="checkbox" v-model="form.recurringMeeting.enabled" /> В этом списке есть регулярная встреча</label>
        <template v-if="form.recurringMeeting.enabled">
          <div class="field-group">
            <label>Название встречи</label>
            <input v-model="form.recurringMeeting.title" placeholder="Например: Еженедельный синк по проекту" />
          </div>
          <div class="field-group">
            <label>Описание</label>
            <RichTextEditor v-model="form.recurringMeeting.description" placeholder="Повестка, участники, формат..." />
          </div>
          <div class="field-group">
            <label>Ссылка на звонок</label>
            <input v-model="form.recurringMeeting.link" placeholder="https://meet.example.com/..." />
          </div>
          <div class="field-row">
            <div class="field-group">
              <label>День недели</label>
              <select v-model="form.recurringMeeting.dayOfWeek">
                <option v-for="(label, day) in WEEKDAY_LABEL" :key="day" :value="day">{{ label }}</option>
              </select>
            </div>
            <div class="field-group">
              <label>Время</label>
              <input v-model="form.recurringMeeting.time" type="time" />
            </div>
          </div>
          <div class="field-group">
            <label>Периодичность</label>
            <select v-model="form.recurringMeeting.frequency">
              <option v-for="(label, freq) in MEETING_FREQ_LABEL" :key="freq" :value="freq">{{ label }}</option>
            </select>
          </div>
        </template>
      </div>

      <div class="modal-actions">
        <button class="btn btn-ghost" @click="emit('close')">Отмена</button>
        <button class="btn btn-primary" :disabled="!form.title.trim()" @click="save">{{ createMode ? 'Создать' : 'Сохранить' }}</button>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div
      v-if="iconPickerOpen" ref="iconGridEl" class="icon-grid card"
      :style="{ top: `${iconGridPos.top}px`, left: `${iconGridPos.left}px` }"
      @click.stop
    >
      <button
        v-for="opt in ICON_OPTIONS" :key="opt" type="button" class="icon-option"
        :class="{ active: opt === form.icon }" @click="pickIcon(opt)"
      ><AppIcon :name="opt" :size="16" /></button>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { width: 640px; max-height: 85vh; padding: 0; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 10px; }
.modal-header h3 { margin: 0; font-size: 15px; }
.modal-body { padding: 4px 18px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.field-group { display: flex; flex-direction: column; gap: 4px; position: relative; }
.field-group label { font-size: 11.5px; color: var(--color-text-muted); }
.field-group input, .field-group select, .field-group textarea { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 8px; }
.field-row { display: flex; gap: 12px; }
.icon-picker-group { min-width: 90px; }
.icon-trigger {
  display: flex; align-items: center; gap: 6px; border: 1px solid var(--color-border); background: var(--color-surface);
  border-radius: 6px; padding: 5px 10px; cursor: pointer; color: var(--color-text-muted);
}
.icon-trigger:hover { background: #eef1f7; }
.icon-preview {
  width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted); margin-top: 8px; border-top: 1px solid var(--color-border); padding-top: 10px; }
.checkbox-row { display: flex; align-items: center; gap: 7px; font-size: 13px; }
.views-toggles { display: flex; gap: 14px; }
.hint-text { font-size: 11.5px; color: var(--color-text-muted); line-height: 1.5; margin: 0; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--color-border); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>

<style>
/* Глобальный стиль, т.к. элемент телепортируется в body и выходит из-под scoped.
 * Раньше сетка иконок была position:absolute внутри .field-group, который
 * лежит внутри .modal-body с overflow-y: auto — поэтому при открытии
 * выпадающего списка он обрезался и смещался при скролле — это и была
 * та «baga при раскрытии». Teleport + position: fixed решает это окончательно. */
.icon-grid {
  position: fixed; z-index: 500; padding: 8px;
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; width: 200px; box-shadow: var(--shadow-2);
}
.icon-grid .icon-option {
  border: 1px solid transparent; background: none; border-radius: 6px; padding: 8px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--color-text);
}
.icon-grid .icon-option:hover { background: #eef1f7; }
.icon-grid .icon-option.active { border-color: var(--color-primary); background: #eaf0ff; color: var(--color-primary); }
</style>
