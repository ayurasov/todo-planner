<script setup>
import { reactive, watch } from 'vue'
import { useListsStore } from '../../stores/listsStore'
import { GroupByMode, SortField, GROUP_LABEL, SORT_LABEL, WEEKDAY_LABEL, MEETING_FREQ_LABEL } from '../../domain/entities/enums'
import AppIcon from './AppIcon.vue'

const props = defineProps({ list: { type: Object, required: true } })
const emit = defineEmits(['close'])
const listsStore = useListsStore()

const form = reactive({
  title: props.list.title,
  description: props.list.description,
  color: props.list.color,
  icon: props.list.settings?.icon || '📋',
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

async function save() {
  await listsStore.updateList(props.list.id, {
    title: form.title,
    description: form.description,
    color: form.color,
    settings: {
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
    },
  })
  emit('close')
}

function toggleView(view) {
  const idx = form.allowedViews.indexOf(view)
  if (idx === -1) form.allowedViews.push(view)
  else if (form.allowedViews.length > 1) form.allowedViews.splice(idx, 1)
}
</script>

<template>
  <div class="modal-overlay">
    <div class="modal card scroll-thin">
      <div class="modal-header">
        <h3>Настройки списка</h3>
        <button class="btn btn-ghost btn-sm" @click="emit('close')"><AppIcon name="close" :size="13" /></button>
      </div>

      <div class="modal-body">
        <div class="field-group">
          <label>Название</label>
          <input v-model="form.title" />
        </div>
        <div class="field-group">
          <label>Описание</label>
          <textarea v-model="form.description" rows="2" />
        </div>
        <div class="field-row">
          <div class="field-group">
            <label>Цвет</label>
            <input v-model="form.color" type="color" />
          </div>
          <div class="field-group">
            <label>Иконка</label>
            <input v-model="form.icon" maxlength="2" class="icon-input" />
          </div>
        </div>

        <div class="section-title">Совместный доступ и инструментарий</div>
        <label class="checkbox-row"><input type="checkbox" v-model="form.allowComments" /> Разрешить комментарии в этом списке</label>
        <label class="checkbox-row"><input type="checkbox" v-model="form.allowGuestViewers" /> Разрешить приглашённых наблюдателей извне команды</label>
        <label class="checkbox-row"><input type="checkbox" v-model="form.requireDueDateOnCreate" /> Требовать срок при создании задачи</label>
        <label class="checkbox-row"><input type="checkbox" v-model="form.showCompletedByDefault" /> Показывать выполненные по умолчанию</label>

        <div class="section-title">Поведение по умолчанию</div>
        <div class="field-group">
          <label>Группировка по умолчанию</label>
          <select v-model="form.defaultGroupBy">
            <option v-for="g in Object.values(GroupByMode)" :key="g" :value="g">{{ GROUP_LABEL[g] }}</option>
          </select>
        </div>
        <div class="field-group">
          <label>Сортировка по умолчанию</label>
          <select v-model="form.defaultSortField">
            <option v-for="s in Object.values(SortField)" :key="s" :value="s">{{ SORT_LABEL[s] }}</option>
          </select>
        </div>
        <div class="field-group">
          <label>Автоархивация выполненных (дней)</label>
          <input v-model.number="form.autoArchiveDoneAfterDays" type="number" min="0" />
        </div>

        <div class="section-title">Доступные представления</div>
        <div class="views-toggles">
          <label v-for="v in ['list', 'tree', 'grouped']" :key="v" class="checkbox-row">
            <input type="checkbox" :checked="form.allowedViews.includes(v)" @change="toggleView(v)" />
            {{ v === 'list' ? 'Плоский список' : v === 'tree' ? 'Дерево' : 'Группировка' }}
          </label>
        </div>

        <div class="section-title">Регулярная встреча / звонок</div>
        <p class="hint-text">Опишите регулярный созвон, привязанный к этому списку — вместо абстрактного "шаблона повторения" укажите понятные параметры звонка.</p>
        <label class="checkbox-row"><input type="checkbox" v-model="form.recurringMeeting.enabled" /> В этом списке есть регулярная встреча</label>
        <template v-if="form.recurringMeeting.enabled">
          <div class="field-group">
            <label>Название встречи</label>
            <input v-model="form.recurringMeeting.title" placeholder="Например: Еженедельный синк по проекту" />
          </div>
          <div class="field-group">
            <label>Описание</label>
            <textarea v-model="form.recurringMeeting.description" rows="2" placeholder="Повестка, участники, формат..." />
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
        <button class="btn btn-primary" @click="save">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(20,25,40,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { width: 460px; max-height: 85vh; padding: 0; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 10px; }
.modal-header h3 { margin: 0; font-size: 15px; }
.modal-body { padding: 4px 18px 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.field-group { display: flex; flex-direction: column; gap: 4px; }
.field-group label { font-size: 11.5px; color: var(--color-text-muted); }
.field-group input, .field-group select, .field-group textarea { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 8px; }
.field-row { display: flex; gap: 12px; }
.icon-input { width: 60px; text-align: center; }
.section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted); margin-top: 8px; border-top: 1px solid var(--color-border); padding-top: 10px; }
.checkbox-row { display: flex; align-items: center; gap: 7px; font-size: 13px; }
.views-toggles { display: flex; gap: 14px; }
.hint-text { font-size: 11.5px; color: var(--color-text-muted); line-height: 1.5; margin: 0; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--color-border); }
</style>
