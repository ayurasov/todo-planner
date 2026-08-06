import { defineStore } from 'pinia'
import { preferencesStorage } from '../repositories/storage/preferencesStorage'
import { DensityMode, GroupByMode, SortField, ColorCodeMode } from '../domain/entities/enums'

/**
 * Персональные настройки отображения — best practice из корпоративной практики
 * ведения ежедневных листов (аналог "Customize" в Asana/ClickUp/Todoist):
 * плотность строк, группировка, сортировка, цветовая маркировка, видимые поля,
 * показывать/скрывать выполненные и комментарии.
 */
const DEFAULT_PREFS = {
  density: DensityMode.COMFORTABLE,
  groupBy: GroupByMode.NONE,
  sortField: SortField.SCORE,
  sortDir: 'desc',
  colorCode: ColorCodeMode.PRIORITY,
  showSubtaskCount: true,
  showChecklistProgress: true,
  showCommentsCount: true,
  showTags: true,
  showAssigneeAvatar: true,
  showDueDate: true,
  showCompletedDate: true,
  showLastUpdatedDate: true,
  showScoreDebug: false,
  showWatchers: false,
  showListBadgeInMyTasks: true,
  compactAvatars: false,
  wrapLongTitles: true,
  highlightOverdue: true,
  weekStartsOn: 'monday',
  timeFormat: '24h',
  showSubtasksStandalone: false,
}

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({ ...preferencesStorage.load(DEFAULT_PREFS) }),
  actions: {
    set(key, value) {
      this[key] = value
      this._persist()
    },
    toggle(key) {
      this[key] = !this[key]
      this._persist()
    },
    resetToDefaults() {
      Object.assign(this, DEFAULT_PREFS)
      this._persist()
    },
    _persist() {
      preferencesStorage.save({ ...this.$state })
    },
  },
})
