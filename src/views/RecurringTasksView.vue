<script setup>
import { ref } from 'vue'
import { useRecurrenceStore } from '../stores/recurrenceStore'
import { useListsStore } from '../stores/listsStore'
import { RecurrenceType, RecurrenceFreq } from '../domain/entities/enums'

const recurrenceStore = useRecurrenceStore()
const listsStore = useListsStore()

const showCreate = ref(false)
const form = ref({ listId: listsStore.lists[0]?.id, titleTemplate: '', type: RecurrenceType.FIXED_SCHEDULE, freq: RecurrenceFreq.WEEKLY })

async function createTemplate() {
  if (!form.value.titleTemplate.trim()) return
  await recurrenceStore.createTemplate({
    listId: form.value.listId, titleTemplate: form.value.titleTemplate,
    type: form.value.type, rule: { freq: form.value.freq, interval: 1 },
  })
  form.value.titleTemplate = ''
  showCreate.value = false
}

const TYPE_LABEL = { fixed_schedule: 'По календарной дате', completion_based: 'По завершению' }
const FREQ_LABEL = { daily: 'Ежедневно', weekly: 'Еженедельно', monthly: 'Ежемесячно', custom: 'Пользовательское' }
</script>

<template>
  <div class="view-header">
    <h2>Повторяющиеся задачи</h2>
    <button class="btn btn-primary" @click="showCreate = !showCreate">+ Новый шаблон</button>
  </div>

  <div v-if="showCreate" class="card create-form">
    <input v-model="form.titleTemplate" placeholder="Название шаблона" />
    <select v-model="form.listId"><option v-for="l in listsStore.lists" :key="l.id" :value="l.id">{{ l.title }}</option></select>
    <select v-model="form.type">
      <option :value="'fixed_schedule'">По календарной дате</option>
      <option :value="'completion_based'">По завершению</option>
    </select>
    <select v-model="form.freq">
      <option :value="'daily'">Ежедневно</option>
      <option :value="'weekly'">Еженедельно</option>
      <option :value="'monthly'">Ежемесячно</option>
    </select>
    <button class="btn btn-primary btn-sm" @click="createTemplate">Создать</button>
  </div>

  <div class="template-list card">
    <div v-for="t in recurrenceStore.templates" :key="t.id" class="template-row">
      <div class="template-main">
        <strong>{{ t.titleTemplate }}</strong>
        <span class="template-meta">{{ TYPE_LABEL[t.type] }} · {{ FREQ_LABEL[t.rule?.freq] }}</span>
      </div>
      <button class="btn btn-ghost btn-sm btn-danger" @click="recurrenceStore.removeTemplate(t.id)">Удалить</button>
    </div>
    <div v-if="!recurrenceStore.templates.length" class="empty-state">Нет активных шаблонов повторения</div>
  </div>
</template>

<style scoped>
.view-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.view-header h2 { margin: 0; font-size: 19px; }
.create-form { padding: 14px; display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.create-form input, .create-form select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 10px; }
.template-list { padding: 4px; }
.template-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid var(--color-border); }
.template-main { display: flex; flex-direction: column; gap: 2px; }
.template-meta { font-size: 12px; color: var(--color-text-muted); }
.empty-state { padding: 30px; text-align: center; color: var(--color-text-muted); font-size: 13px; }
</style>
