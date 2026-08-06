import { defineStore } from 'pinia'
import { LocalStorageAdapter } from '../repositories/storage/LocalStorageAdapter'

const filtersStorage = new LocalStorageAdapter('quick-filters')

/**
 * Панель быстрых фильтров (раздел 3.6 ТЗ TaskBubbler) — сознательно вынесена
 * в отдельный стор, а не смешана с preferencesStore, так как preferences
 * управляет представлением/оформлением списка (плотность, группировка,
 * сортировка), а quick-фильтры — это выборка данных, которая должна
 * работать одинаково в разных представлениях (My Tasks, Team Tasks) и не
 * зависеть от personal display preferences конкретного экрана.
 *
 * Все фильтры комбинируются через AND (см. matches()).
 */
const DEFAULT_FILTERS = {
  status: 'all', // all | not_done | done
  assigneeIds: [], // пусто = все исполнители
  dateRange: { from: null, to: null }, // ISO-строки или null
  datePreset: null, // 'today' | 'week' | 'month' | null (кастомный диапазон)
}

const MS_DAY = 24 * 60 * 60 * 1000

function computePresetRange(preset) {
  const now = new Date()
  const startOfToday = new Date(now)
  startOfToday.setHours(0, 0, 0, 0)
  if (preset === 'today') {
    const end = new Date(startOfToday.getTime() + MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  if (preset === 'week') {
    const end = new Date(startOfToday.getTime() + 7 * MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  if (preset === 'month') {
    const end = new Date(startOfToday.getTime() + 30 * MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  return { from: null, to: null }
}

export const useFiltersStore = defineStore('quickFilters', {
  state: () => ({ ...filtersStorage.load(DEFAULT_FILTERS) }),

  getters: {
    isActive: (state) =>
      state.status !== 'all' ||
      state.assigneeIds.length > 0 ||
      !!state.dateRange.from ||
      !!state.dateRange.to,

    activeCount: (state) => {
      let count = 0
      if (state.status !== 'all') count += 1
      if (state.assigneeIds.length) count += 1
      if (state.dateRange.from || state.dateRange.to) count += 1
      return count
    },
  },

  actions: {
    setStatus(status) {
      this.status = status
      this._persist()
    },

    toggleAssignee(userId) {
      const idx = this.assigneeIds.indexOf(userId)
      if (idx === -1) this.assigneeIds.push(userId)
      else this.assigneeIds.splice(idx, 1)
      this._persist()
    },

    setDatePreset(preset) {
      this.datePreset = preset
      this.dateRange = computePresetRange(preset)
      this._persist()
    },

    setCustomDateRange(from, to) {
      this.datePreset = null
      this.dateRange = { from, to }
      this._persist()
    },

    resetAll() {
      Object.assign(this, structuredClone(DEFAULT_FILTERS))
      this._persist()
    },

    /**
     * Единая точка применения фильтра — используется во всех представлениях
     * (My Tasks, Team Tasks), чтобы поведение было идентичным и предсказуемым.
     * Все условия объединяются через AND.
     */
    matches(task) {
      if (this.status === 'not_done' && (task.status === 'done' || task.status === 'cancelled')) return false
      if (this.status === 'done' && task.status !== 'done' && task.status !== 'cancelled') return false

      if (this.assigneeIds.length && !this.assigneeIds.includes(task.assigneeId)) return false

      if (this.dateRange.from || this.dateRange.to) {
        if (!task.dueDate) return false
        const due = new Date(task.dueDate)
        if (this.dateRange.from && due < new Date(this.dateRange.from)) return false
        if (this.dateRange.to && due > new Date(this.dateRange.to)) return false
      }

      return true
    },

    apply(tasks) {
      return tasks.filter((t) => this.matches(t))
    },

    _persist() {
      filtersStorage.save({ ...this.$state })
    },
  },
})
