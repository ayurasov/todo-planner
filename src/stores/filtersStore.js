import { defineStore } from 'pinia'
import { LocalStorageAdapter } from '../repositories/storage/LocalStorageAdapter'

const filtersStorage = new LocalStorageAdapter('quick-filters')
const DEFAULT_FILTERS = {
  status: 'all', assigneeIds: [], searchText: '',
  dateRange: { from: null, to: null }, dueDatePreset: null,
  createdDateRange: { from: null, to: null }, createdDatePreset: null,
}
const MS_DAY = 24 * 60 * 60 * 1000
function startOfDay(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); return x }
function computeDueRange(preset) {
  const start = startOfDay(new Date())
  if (preset === 'today') return { from: start.toISOString(), to: new Date(start.getTime() + MS_DAY - 1).toISOString() }
  if (preset === 'tomorrow') { const d = new Date(start.getTime() + MS_DAY); return { from: d.toISOString(), to: new Date(d.getTime() + MS_DAY - 1).toISOString() } }
  if (preset === 'week') return { from: start.toISOString(), to: new Date(start.getTime() + 7 * MS_DAY - 1).toISOString() }
  if (preset === 'month') return { from: start.toISOString(), to: new Date(start.getTime() + 30 * MS_DAY - 1).toISOString() }
  return { from: null, to: null }
}
function computeCreatedRange(preset) {
  const today = startOfDay(new Date())
  if (preset === 'today') return { from: today.toISOString(), to: new Date(today.getTime() + MS_DAY - 1).toISOString() }
  if (preset === 'yesterday') return { from: new Date(today.getTime() - MS_DAY).toISOString(), to: new Date(today.getTime() - 1).toISOString() }
  if (preset === 'week') return { from: new Date(today.getTime() - 6 * MS_DAY).toISOString(), to: new Date(today.getTime() + MS_DAY - 1).toISOString() }
  if (preset === 'month') return { from: new Date(today.getTime() - 29 * MS_DAY).toISOString(), to: new Date(today.getTime() + MS_DAY - 1).toISOString() }
  return { from: null, to: null }
}
export const useFiltersStore = defineStore('quickFilters', {
  state: () => ({ ...structuredClone(DEFAULT_FILTERS), ...filtersStorage.load(DEFAULT_FILTERS) }),
  getters: {
    isActive: (state) => state.status !== 'all' || state.assigneeIds.length > 0 || !!state.searchText || !!state.dueDatePreset || !!state.dateRange.from || !!state.dateRange.to || !!state.createdDatePreset || !!state.createdDateRange.from || !!state.createdDateRange.to,
    activeCount: (state) => (state.status !== 'all' ? 1 : 0) + (state.assigneeIds.length ? 1 : 0) + (state.searchText ? 1 : 0) + (state.dueDatePreset || state.dateRange.from || state.dateRange.to ? 1 : 0) + (state.createdDatePreset || state.createdDateRange.from || state.createdDateRange.to ? 1 : 0),
  },
  actions: {
    setStatus(status) { this.status = status; this._persist() },
    toggleAssignee(id) { const i = this.assigneeIds.indexOf(id); if (i === -1) this.assigneeIds.push(id); else this.assigneeIds.splice(i, 1); this._persist() },
    setSearchText(value) { this.searchText = value; this._persist() },
    setDueDatePreset(preset) { this.dueDatePreset = preset; this.dateRange = computeDueRange(preset); this._persist() },
    setCustomDateRange(from, to) { this.dueDatePreset = null; this.dateRange = { from, to }; this._persist() },
    setCreatedDatePreset(preset) { this.createdDatePreset = preset; this.createdDateRange = computeCreatedRange(preset); this._persist() },
    resetCreatedDate() { this.createdDatePreset = null; this.createdDateRange = { from: null, to: null }; this._persist() },
    resetAll() { Object.assign(this, structuredClone(DEFAULT_FILTERS)); this._persist() },
    matches(task) {
      if (this.status === 'not_done' && (task.status === 'done' || task.status === 'cancelled')) return false
      if (this.status === 'done' && task.status !== 'done' && task.status !== 'cancelled') return false
      if (this.assigneeIds.length && !this.assigneeIds.includes(task.assigneeId)) return false
      if (this.searchText && ![task.title, task.occurrenceTitle, task.meetingTitle].filter(Boolean).join(' ').toLocaleLowerCase().includes(this.searchText.toLocaleLowerCase())) return false
      if (this.dueDatePreset === 'overdue' && (!task.dueDate || new Date(task.dueDate) >= new Date())) return false
      if (this.dueDatePreset === 'no_due' && task.dueDate) return false
      if (!['overdue', 'no_due'].includes(this.dueDatePreset) && (this.dateRange.from || this.dateRange.to)) { if (!task.dueDate) return false; const d = new Date(task.dueDate); if (this.dateRange.from && d < new Date(this.dateRange.from)) return false; if (this.dateRange.to && d > new Date(this.dateRange.to)) return false }
      if (this.createdDateRange.from || this.createdDateRange.to) { if (!task.createdAt) return false; const d = new Date(task.createdAt); if (this.createdDateRange.from && d < new Date(this.createdDateRange.from)) return false; if (this.createdDateRange.to && d > new Date(this.createdDateRange.to)) return false }
      return true
    },
    apply(tasks) { return tasks.filter((task) => this.matches(task)) },
    _persist() { filtersStorage.save({ ...this.$state }) },
  },
})
