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
 * Фильтр по сроку (dueDatePreset) и фильтр по дате создания (createdDatePreset) —
 * два независимых измерения, которые могут быть активны одновременно —
 * все фильтры комбинируются через AND (см. matches()).
 */
const DEFAULT_FILTERS = {
  status: 'all', // all | not_done | done
  assigneeIds: [], // пусто = все исполнители
  dateRange: { from: null, to: null }, // ISO-строки или null — диапазон по сроку (dueDate)
  // 'overdue' | 'no_due' | 'today' | 'tomorrow' | 'week' | 'month' | null (кастомный диапазон).
  // 'overdue' и 'no_due' — особые случаи, не сводящиеся к диапазону дат —
  // они проверяются отдельно в matches().
  dueDatePreset: null,
  createdDateRange: { from: null, to: null }, // диапазон по дате создания (createdAt)
  createdDatePreset: null, // 'today' | 'yesterday' | 'week' | 'month' | null
}

const MS_DAY = 24 * 60 * 60 * 1000

function startOfDay(d) {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x
}

function computeDueRange(preset) {
  const startOfToday = startOfDay(new Date())
  if (preset === 'today') {
    const end = new Date(startOfToday.getTime() + MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  if (preset === 'tomorrow') {
    const start = new Date(startOfToday.getTime() + MS_DAY)
    const end = new Date(start.getTime() + MS_DAY - 1)
    return { from: start.toISOString(), to: end.toISOString() }
  }
  if (preset === 'week') {
    const end = new Date(startOfToday.getTime() + 7 * MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  if (preset === 'month') {
    const end = new Date(startOfToday.getTime() + 30 * MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  // 'overdue' и 'no_due' не имеют диапазона — логика в matches().
  return { from: null, to: null }
}

function computeCreatedRange(preset) {
  const startOfToday = startOfDay(new Date())
  if (preset === 'today') {
    const end = new Date(startOfToday.getTime() + MS_DAY - 1)
    return { from: startOfToday.toISOString(), to: end.toISOString() }
  }
  if (preset === 'yesterday') {
    const start = new Date(startOfToday.getTime() - MS_DAY)
    const end = new Date(startOfToday.getTime() - 1)
    return { from: start.toISOString(), to: end.toISOString() }
  }
  if (preset === 'week') {
    const start = new Date(startOfToday.getTime() - 6 * MS_DAY)
    const end = new Date(startOfToday.getTime() + MS_DAY - 1)
    return { from: start.toISOString(), to: end.toISOString() }
  }
  if (preset === 'month') {
    const start = new Date(startOfToday.getTime() - 29 * MS_DAY)
    const end = new Date(startOfToday.getTime() + MS_DAY - 1)
    return { from: start.toISOString(), to: end.toISOString() }
  }
  return { from: null, to: null }
}

export const useFiltersStore = defineStore('quickFilters', {
  state: () => ({ ...structuredClone(DEFAULT_FILTERS), ...filtersStorage.load(DEFAULT_FILTERS) }),

  getters: {
    isActive: (state) =>
      state.status !== 'all' ||
      state.assigneeIds.length > 0 ||
      !!state.dueDatePreset ||
      !!state.dateRange.from ||
      !!state.dateRange.to ||
      !!state.createdDatePreset ||
      !!state.createdDateRange.from ||
      !!state.createdDateRange.to,

    activeCount: (state) => {
      let count = 0
      if (state.status !== 'all') count += 1
      if (state.assigneeIds.length) count += 1
      if (state.dueDatePreset || state.dateRange.from || state.dateRange.to) count += 1
      if (state.createdDatePreset || state.createdDateRange.from || state.createdDateRange.to) count += 1
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

    setDueDatePreset(preset) {
      this.dueDatePreset = preset
      this.dateRange = computeDueRange(preset)
      this._persist()
    },

    setCustomDateRange(from, to) {
      this.dueDatePreset = null
      this.dateRange = { from, to }
      this._persist()
    },

    setCreatedDatePreset(preset) {
      this.createdDatePreset = preset
      this.createdDateRange = computeCreatedRange(preset)
      this._persist()
    },

    resetCreatedDate() {
      this.createdDatePreset = null
      this.createdDateRange = { from: null, to: null }
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

      if (this.dueDatePreset === 'overdue') {
        if (!task.dueDate) return false
        if (new Date(task.dueDate) >= new Date()) return false
      } else if (this.dueDatePreset === 'no_due') {
        if (task.dueDate) return false
      } else if (this.dateRange.from || this.dateRange.to) {
        if (!task.dueDate) return false
        const due = new Date(task.dueDate)
        if (this.dateRange.from && due < new Date(this.dateRange.from)) return false
        if (this.dateRange.to && due > new Date(this.dateRange.to)) return false
      }

      if (this.createdDateRange.from || this.createdDateRange.to) {
        if (!task.createdAt) return false
        const created = new Date(task.createdAt)
        if (this.createdDateRange.from && created < new Date(this.createdDateRange.from)) return false
        if (this.createdDateRange.to && created > new Date(this.createdDateRange.to)) return false
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
