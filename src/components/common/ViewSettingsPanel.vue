<script setup>
import { usePreferencesStore } from '../../stores/preferencesStore'
import { DensityMode, GroupByMode, SortField, ColorCodeMode, GROUP_LABEL, SORT_LABEL, DENSITY_LABEL, COLOR_CODE_LABEL } from '../../domain/entities/enums'

const prefs = usePreferencesStore()

function toggleSortDir() {
  prefs.set('sortDir', prefs.sortDir === 'asc' ? 'desc' : 'asc')
}
</script>

<template>
  <div class="settings-block">
    <div class="settings-group">
      <label class="settings-label">Плотность строк</label>
      <div class="segmented">
        <button v-for="d in Object.values(DensityMode)" :key="d" :class="{ active: prefs.density === d }" @click="prefs.set('density', d)">
          {{ DENSITY_LABEL[d] }}
        </button>
      </div>
    </div>

    <div class="settings-group">
      <label class="settings-label">Группировка по умолчанию</label>
      <select :value="prefs.groupBy" @change="prefs.set('groupBy', $event.target.value)">
        <option v-for="g in Object.values(GroupByMode)" :key="g" :value="g">{{ GROUP_LABEL[g] }}</option>
      </select>
    </div>

    <div class="settings-group">
      <label class="settings-label">Сортировка по умолчанию</label>
      <div class="sort-row">
        <select :value="prefs.sortField" @change="prefs.set('sortField', $event.target.value)">
          <option v-for="s in Object.values(SortField)" :key="s" :value="s">{{ SORT_LABEL[s] }}</option>
        </select>
        <button class="btn btn-ghost btn-sm" @click="toggleSortDir">{{ prefs.sortDir === 'asc' ? '↑ Возр.' : '↓ Убыв.' }}</button>
      </div>
    </div>

    <div class="settings-group">
      <label class="settings-label">Цветовая маркировка строк</label>
      <select :value="prefs.colorCode" @change="prefs.set('colorCode', $event.target.value)">
        <option v-for="c in Object.values(ColorCodeMode)" :key="c" :value="c">{{ COLOR_CODE_LABEL[c] }}</option>
      </select>
    </div>

    <div class="settings-group">
      <label class="settings-label">Видимость полей в списке</label>
      <div class="checkbox-grid">
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showDueDate" @change="prefs.toggle('showDueDate')" /> Крайний срок</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showCompletedDate" @change="prefs.toggle('showCompletedDate')" /> Дата выполнения</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showLastUpdatedDate" @change="prefs.toggle('showLastUpdatedDate')" /> Последнее изменение</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showCreatedDate" @change="prefs.toggle('showCreatedDate')" /> Дата создания</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showTags" @change="prefs.toggle('showTags')" /> Теги</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showSubtaskCount" @change="prefs.toggle('showSubtaskCount')" /> Счётчик подзадач</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showChecklistProgress" @change="prefs.toggle('showChecklistProgress')" /> Прогресс чек-листа</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showCommentsCount" @change="prefs.toggle('showCommentsCount')" /> Счётчик комментариев</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showWatchers" @change="prefs.toggle('showWatchers')" /> Наблюдатели</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showAssigneeAvatar" @change="prefs.toggle('showAssigneeAvatar')" /> Аватар исполнителя</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.detailedAssigneeView" @change="prefs.toggle('detailedAssigneeView')" /> Детальный вид исполнителя (иконка + имя)</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.showListBadgeInMyTasks" @change="prefs.toggle('showListBadgeInMyTasks')" /> Метка списка</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.highlightOverdue" @change="prefs.toggle('highlightOverdue')" /> Подсвечивать просроченные</label>
        <label class="checkbox-row"><input type="checkbox" :checked="prefs.wrapLongTitles" @change="prefs.toggle('wrapLongTitles')" /> Полный текст заголовков</label>
      </div>
    </div>

    <div class="settings-group">
      <label class="settings-label">Подзадачи</label>
      <label class="checkbox-row">
        <input type="checkbox" :checked="prefs.showSubtasksStandalone" @change="prefs.toggle('showSubtasksStandalone')" />
        Показывать подзадачи как отдельные задачи в общих списках
      </label>
      <p class="settings-hint">
        По умолчанию подзадачи отображаются только внутри дерева родительской задачи.
        Если включить эту настройку, подзадачи дополнительно появятся как самостоятельные строки
        в "Мои задачи" / "Задачи команды" / списках. Для конкретной подзадачи это поведение можно
        переопределить индивидуально через её контекстное меню или детальную панель ("Показывать отдельно").
      </p>
    </div>

    <div class="settings-group">
      <label class="settings-label">Прочее</label>
      <div class="mini-row">
        <span>Начало недели</span>
        <select :value="prefs.weekStartsOn" @change="prefs.set('weekStartsOn', $event.target.value)">
          <option value="monday">Понедельник</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>
      <div class="mini-row">
        <span>Формат времени</span>
        <select :value="prefs.timeFormat" @change="prefs.set('timeFormat', $event.target.value)">
          <option value="24h">24ч</option>
          <option value="12h">12ч (AM/PM)</option>
        </select>
      </div>
    </div>

    <button class="btn btn-ghost btn-sm reset-btn" @click="prefs.resetToDefaults">Сбросить к значениям по умолчанию</button>
  </div>
</template>

<style scoped>
.settings-block { display: flex; flex-direction: column; gap: 14px; }
.settings-group { display: flex; flex-direction: column; gap: 6px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border); }
.settings-group:last-of-type { border-bottom: none; padding-bottom: 0; }
.settings-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-muted); }
.settings-group select { border: 1px solid var(--color-border); border-radius: 6px; padding: 6px 9px; font-size: 13px; max-width: 260px; }
.segmented { display: flex; gap: 4px; max-width: 320px; }
.segmented button { flex: 1; border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 6px; padding: 6px 4px; font-size: 12px; cursor: pointer; }
.segmented button.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.sort-row { display: flex; gap: 6px; }
.checkbox-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px 16px; }
.checkbox-row { display: flex; align-items: center; gap: 7px; font-size: 13px; cursor: pointer; }
.mini-row { display: flex; align-items: center; justify-content: space-between; max-width: 260px; font-size: 13px; padding: 3px 0; }
.settings-hint { font-size: 11.5px; color: var(--color-text-muted); line-height: 1.5; margin: 2px 0 0; }
.reset-btn { align-self: flex-start; }
</style>
