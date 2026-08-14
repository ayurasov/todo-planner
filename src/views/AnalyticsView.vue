<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useTasksStore } from '../stores/tasksStore'
import { useHistoryStore } from '../stores/historyStore'
import { useUsersStore } from '../stores/usersStore'
import { useListsStore } from '../stores/listsStore'
import { useMeetingsStore } from '../stores/meetingsStore'
import AppIcon from '../components/common/AppIcon.vue'
import SearchMultiSelect from '../components/common/SearchMultiSelect.vue'
import { DATE_RANGE_PRESETS, DEFAULT_DATE_RANGE_PRESET, presetToRange } from '../utils/dateRangePresets'
import {
  buildOverviewStats, buildTimeline, buildPerAssigneeStats, buildUserDetail, filterTasksAndHistory,
} from '../domain/analytics/taskAnalytics'

const tasksStore = useTasksStore()
const historyStore = useHistoryStore()
const usersStore = useUsersStore()
const listsStore = useListsStore()
const meetingsStore = useMeetingsStore()

const timelineEl = ref(null)
const bucketsEl = ref(null)
const userTimelineEl = ref(null)
let timelineChart = null
let bucketsChart = null
let userTimelineChart = null

// ResizeObserver-ы: инициализируем ECharts ровно тогда, когда контейнер
// впервые получает ненулевой размер. setTimeout(0) не надёжен — рендер
// браузера может произойти позже, и init получает offsetWidth=0.
let roTimeline = null
let roBuckets = null
let roUserTimeline = null

function initWhenVisible(elRef, getter, setter, renderFn) {
  const el = elRef.value
  if (!el) return
  if (el.offsetWidth > 0) {
    setter(echarts.init(el))
    renderFn()
    return
  }
  const ro = new ResizeObserver(() => {
    if (el.offsetWidth > 0) {
      ro.disconnect()
      setter(echarts.init(el))
      renderFn()
    }
  })
  ro.observe(el)
  return ro
}

const selectedUserId = ref(null)

const datePreset = ref(DEFAULT_DATE_RANGE_PRESET)
const customFrom = ref('')
const customTo = ref('')
const filterListIds = ref([])
const filterMeetingIds = ref([])
const assigneeSearch = ref('')
const assigneeSort = ref({ field: 'name', dir: 'asc' })

onMounted(async () => {
  if (!tasksStore.loaded) await tasksStore.load()
  if (!usersStore.loaded) await usersStore.load()
  if (!listsStore.loaded) await listsStore.load()
  if (!meetingsStore.loaded) await meetingsStore.load()
  await historyStore.loadGlobalLog(tasksStore.tasks.map((t) => t.id))
  selectedUserId.value = usersStore.currentUser?.id || null
  const initialRange = presetToRange(DEFAULT_DATE_RANGE_PRESET)
  if (initialRange) { customFrom.value = initialRange.from; customTo.value = initialRange.to }

  await nextTick()

  roTimeline = initWhenVisible(timelineEl, () => timelineChart, (c) => { timelineChart = c }, renderTimeline)
  roBuckets = initWhenVisible(bucketsEl, () => bucketsChart, (c) => { bucketsChart = c }, renderBuckets)
  // userTimelineEl рендерится под v-if="userDetail" — инициализируем лениво в watch(userDetail)

  window.addEventListener('resize', resizeAll)
})

onBeforeUnmount(() => {
  roTimeline?.disconnect()
  roBuckets?.disconnect()
  roUserTimeline?.disconnect()
  window.removeEventListener('resize', resizeAll)
  timelineChart?.dispose()
  bucketsChart?.dispose()
  userTimelineChart?.dispose()
})

function resizeAll() {
  timelineChart?.resize(); bucketsChart?.resize(); userTimelineChart?.resize()
}

function setPreset(preset) {
  datePreset.value = preset
  const range = presetToRange(preset)
  if (range) { customFrom.value = range.from; customTo.value = range.to }
}

function onCustomDateChange() {
  datePreset.value = 'custom'
}

const hasActiveFilters = computed(() => (
  datePreset.value !== DEFAULT_DATE_RANGE_PRESET || filterListIds.value.length || filterMeetingIds.value.length
))

function resetFilters() {
  setPreset(DEFAULT_DATE_RANGE_PRESET)
  filterListIds.value = []
  filterMeetingIds.value = []
}

const listOptions = computed(() => listsStore.lists.map((l) => ({ id: l.id, label: l.title })))
const meetingOptions = computed(() => meetingsStore.meetings.map((m) => ({ id: m.id, label: m.title })))

const filtered = computed(() => filterTasksAndHistory(tasksStore.tasks, historyStore.globalLog, {
  dateFrom: customFrom.value || null,
  dateTo: customTo.value || null,
  listIds: filterListIds.value,
  meetingIds: filterMeetingIds.value,
}))

const overview = computed(() => buildOverviewStats(filtered.value.tasks, filtered.value.history))

const createdTimeline = computed(() => buildTimeline(filtered.value.tasks, 'createdAt'))
const completedTimeline = computed(() => buildTimeline(filtered.value.tasks.filter((t) => t.status === 'done'), 'completedAt'))

const perAssigneeRaw = computed(() => buildPerAssigneeStats(filtered.value.tasks, filtered.value.history, usersStore.users, usersStore.currentUser?.id))

const ASSIGNEE_SORT_FIELDS = [
  { value: 'name', label: 'Имя' },
  { value: 'created', label: 'Создал' },
  { value: 'assigned', label: 'Назначено' },
  { value: 'completed', label: 'Завершено' },
  { value: 'onTimeRate', label: '% в срок' },
  { value: 'open', label: 'В работе' },
  { value: 'rescheduled', label: 'Переносы' },
]

function setAssigneeSort(field) {
  if (assigneeSort.value.field === field) {
    assigneeSort.value = { field, dir: assigneeSort.value.dir === 'asc' ? 'desc' : 'asc' }
  } else {
    assigneeSort.value = { field, dir: field === 'name' ? 'asc' : 'desc' }
  }
}

const perAssignee = computed(() => {
  const currentId = usersStore.currentUser?.id
  const self = perAssigneeRaw.value.find((r) => r.userId === currentId)
  let rest = perAssigneeRaw.value.filter((r) => r.userId !== currentId)

  const q = assigneeSearch.value.trim().toLowerCase()
  if (q) rest = rest.filter((r) => (userName(r.userId) || '').toLowerCase().includes(q))

  const { field, dir } = assigneeSort.value
  const mul = dir === 'asc' ? 1 : -1
  rest = [...rest].sort((a, b) => {
    if (field === 'name') return mul * (userName(a.userId) || '').localeCompare(userName(b.userId) || '')
    return mul * ((a[field] ?? 0) - (b[field] ?? 0))
  })

  return self ? [self, ...rest] : rest
})

const userOptions = computed(() => usersStore.users)
const userDetail = computed(() => (selectedUserId.value ? buildUserDetail(selectedUserId.value, filtered.value.tasks, filtered.value.history) : null))
const isSelf = computed(() => selectedUserId.value === usersStore.currentUser?.id)

const BUCKET_LABEL = { early: 'Заранее', on_time: 'В срок', late: 'С опозданием', no_due: 'Без срока' }
const BUCKET_COLOR = { early: '#1e9e4d', on_time: '#4f7cff', late: '#e5484d', no_due: '#9aa3b2' }

function renderTimeline() {
  if (!timelineChart) return
  const allDays = [...new Set([...createdTimeline.value.days, ...completedTimeline.value.days])].sort()
  const createdMap = Object.fromEntries(createdTimeline.value.days.map((d, i) => [d, createdTimeline.value.counts[i]]))
  const completedMap = Object.fromEntries(completedTimeline.value.days.map((d, i) => [d, completedTimeline.value.counts[i]]))
  timelineChart.setOption({
    grid: { left: 36, right: 16, top: 36, bottom: 30 },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    xAxis: { type: 'category', data: allDays },
    yAxis: { type: 'value' },
    tooltip: { trigger: 'axis' },
    series: [
      { name: 'Создано', type: 'line', data: allDays.map((d) => createdMap[d] || 0), smooth: true, itemStyle: { color: '#4f7cff' }, areaStyle: { color: 'rgba(79,124,255,0.10)' } },
      { name: 'Завершено', type: 'line', data: allDays.map((d) => completedMap[d] || 0), smooth: true, itemStyle: { color: '#1e9e4d' }, areaStyle: { color: 'rgba(30,158,77,0.10)' } },
    ],
  })
}

function renderBuckets() {
  if (!bucketsChart) return
  const b = overview.value.buckets
  const data = Object.entries(b).filter(([, v]) => v > 0).map(([k, v]) => ({ name: BUCKET_LABEL[k], value: v, itemStyle: { color: BUCKET_COLOR[k] } }))
  bucketsChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{ type: 'pie', radius: ['40%', '68%'], data, label: { fontSize: 11 } }],
  })
}

function renderUserTimeline() {
  if (!userTimelineChart || !userDetail.value) return
  const c = userDetail.value.timelineCreated
  const d = userDetail.value.timelineCompleted
  const allDays = [...new Set([...c.days, ...d.days])].sort()
  const createdMap = Object.fromEntries(c.days.map((day, i) => [day, c.counts[i]]))
  const doneMap = Object.fromEntries(d.days.map((day, i) => [day, d.counts[i]]))
  userTimelineChart.setOption({
    grid: { left: 36, right: 16, top: 36, bottom: 30 },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    xAxis: { type: 'category', data: allDays },
    yAxis: { type: 'value' },
    tooltip: { trigger: 'axis' },
    series: [
      { name: 'Назначено (создано)', type: 'bar', data: allDays.map((day) => createdMap[day] || 0), itemStyle: { color: '#4f7cff' } },
      { name: 'Завершено', type: 'bar', data: allDays.map((day) => doneMap[day] || 0), itemStyle: { color: '#1e9e4d' } },
    ],
  })
}

watch(overview, () => nextTick(() => { renderTimeline(); renderBuckets() }))

// userDetail блок рендерится под v-if — при первом появлении нужно инициализировать
// chart, при последующих изменениях — только перерисовать.
watch(userDetail, async (val) => {
  if (!val) return
  await nextTick()
  if (!userTimelineChart && userTimelineEl.value) {
    roUserTimeline?.disconnect()
    roUserTimeline = initWhenVisible(
      userTimelineEl,
      () => userTimelineChart,
      (c) => { userTimelineChart = c },
      renderUserTimeline,
    )
    return
  }
  renderUserTimeline()
})

function userName(id) {
  return usersStore.byId(id)?.name || id
}
</script>

<template>
  <div class="view-header">
    <div class="view-title">
      <span class="list-icon"><AppIcon name="chart" :size="18" /></span>
      <h2>Аналитика</h2>
    </div>
  </div>

  <div class="card filters-panel">
    <div class="filters-row">
      <div class="filter-group" role="group" aria-label="Интервал">
        <button
          v-for="p in DATE_RANGE_PRESETS" :key="p.value" v-show="p.value !== 'custom'"
          class="filter-btn" :class="{ active: datePreset === p.value }"
          @click="setPreset(p.value)"
        >{{ p.label }}</button>
      </div>

      <div class="custom-range" :class="{ active: datePreset === 'custom' }">
        <input v-model="customFrom" type="date" title="С" @change="onCustomDateChange" />
        <span class="range-sep">—</span>
        <input v-model="customTo" type="date" title="По" @change="onCustomDateChange" />
      </div>

      <SearchMultiSelect
        v-model="filterListIds" :options="listOptions"
        placeholder="Все списки" search-placeholder="Поиск по спискам..."
      />
      <SearchMultiSelect
        v-model="filterMeetingIds" :options="meetingOptions"
        placeholder="Все встречи" search-placeholder="Поиск по встречам..."
      />

      <button v-if="hasActiveFilters" class="btn btn-ghost btn-sm reset-btn" @click="resetFilters">Сбросить фильтры</button>
    </div>
  </div>

  <div class="stat-cards">
    <div class="card stat-card">
      <span class="stat-value">{{ overview.created }}</span>
      <span class="stat-label">Создано задач</span>
    </div>
    <div class="card stat-card">
      <span class="stat-value">{{ overview.completed }}</span>
      <span class="stat-label">Завершено ({{ overview.completionRate }}%)</span>
    </div>
    <div class="card stat-card">
      <span class="stat-value">{{ overview.onTimeRate }}%</span>
      <span class="stat-label">Завершено в срок или заранее</span>
    </div>
    <div class="card stat-card">
      <span class="stat-value">{{ overview.rescheduleCount }}</span>
      <span class="stat-label">Переносов срока</span>
    </div>
    <div class="card stat-card">
      <span class="stat-value">{{ overview.open }}</span>
      <span class="stat-label">В работе</span>
    </div>
  </div>

  <div class="charts-row">
    <div class="card chart-card chart-card-wide">
      <h4>Создание и завершение задач по дням</h4>
      <div ref="timelineEl" class="chart-el" />
    </div>
    <div class="card chart-card">
      <h4>Своевременность завершения</h4>
      <div ref="bucketsEl" class="chart-el" />
    </div>
  </div>

  <div class="card table-card">
    <div class="table-card-header">
      <h4>Статистика по исполнителям</h4>
      <input v-model="assigneeSearch" class="assignee-search" placeholder="Поиск по исполнителю..." />
    </div>
    <table class="analytics-table">
      <thead>
        <tr>
          <th
            v-for="f in ASSIGNEE_SORT_FIELDS" :key="f.value" class="sortable-th"
            @click="setAssigneeSort(f.value)"
          >
            {{ f.label }}
            <AppIcon v-if="assigneeSort.field === f.value" :name="assigneeSort.dir === 'asc' ? 'chevronUp' : 'chevronDown'" :size="10" />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in perAssignee" :key="row.userId"
          :class="{ active: selectedUserId === row.userId, 'self-row': row.userId === usersStore.currentUser?.id }"
          @click="selectedUserId = row.userId"
        >
          <td class="user-cell">{{ userName(row.userId) }}{{ row.userId === usersStore.currentUser?.id ? ' (Я)' : '' }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.assigned }}</td>
          <td>{{ row.completed }}</td>
          <td>{{ row.onTimeRate }}%</td>
          <td>{{ row.open }}</td>
          <td>{{ row.rescheduled }}</td>
        </tr>
        <tr v-if="!perAssignee.length">
          <td colspan="7" class="empty-row">Ничего не найдено</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card user-detail-card">
    <div class="user-detail-header">
      <h4>Детально по исполнителю</h4>
      <select v-model="selectedUserId" class="user-select">
        <option v-for="u in userOptions" :key="u.id" :value="u.id">{{ u.name }}{{ u.id === usersStore.currentUser?.id ? ' (Я)' : '' }}</option>
      </select>
    </div>

    <template v-if="userDetail">
      <p v-if="isSelf" class="self-hint"><AppIcon name="star" :size="12" /> Ваша личная статистика — развёрнутый разбор по всем вашим задачам (с учётом фильтров выше).</p>
      <div class="user-stat-cards">
        <div class="mini-stat"><span class="mini-value">{{ userDetail.assignedCount }}</span><span class="mini-label">Назначено задач</span></div>
        <div class="mini-stat"><span class="mini-value">{{ userDetail.createdCount }}</span><span class="mini-label">Создано задач</span></div>
        <div class="mini-stat"><span class="mini-value">{{ userDetail.completedCount }}</span><span class="mini-label">Завершено</span></div>
        <div class="mini-stat"><span class="mini-value">{{ userDetail.completionRate }}%</span><span class="mini-label">Доля завершения</span></div>
        <div class="mini-stat"><span class="mini-value">{{ userDetail.onTimeRate }}%</span><span class="mini-label">В срок / заранее</span></div>
        <div class="mini-stat"><span class="mini-value">{{ userDetail.avgCompletionDays ?? '—' }}</span><span class="mini-label">Ср. дней на задачу</span></div>
        <div class="mini-stat" :class="{ warn: userDetail.overdueOpen > 0 }"><span class="mini-value">{{ userDetail.overdueOpen }}</span><span class="mini-label">Просрочено сейчас</span></div>
        <div class="mini-stat"><span class="mini-value">{{ userDetail.rescheduleCount }}</span><span class="mini-label">Переносов срока</span></div>
      </div>

      <div class="bucket-bar">
        <span
          v-for="(v, k) in userDetail.buckets" :key="k" v-show="v > 0"
          class="bucket-chip" :style="{ background: BUCKET_COLOR[k] + '1f', color: BUCKET_COLOR[k] }"
        >{{ BUCKET_LABEL[k] }}: {{ v }}</span>
      </div>

      <div ref="userTimelineEl" class="chart-el user-chart-el" />
    </template>
  </div>
</template>

<style scoped>
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.view-title { display: flex; align-items: center; gap: 8px; }
.view-title h2 { margin: 0; font-size: 19px; }
.list-icon { display: flex; color: var(--color-primary); }

.filters-panel { padding: 10px 12px; margin-bottom: 14px; }
.filters-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.filter-group { display: flex; gap: 2px; background: #eef1f7; border-radius: 8px; padding: 2px; }
.filter-btn {
  border: none; background: transparent; padding: 5px 10px; border-radius: 6px;
  font-size: 12.5px; color: var(--color-text-muted); cursor: pointer; white-space: nowrap;
}
.filter-btn.active { background: var(--color-surface); color: var(--color-text); font-weight: 600; box-shadow: var(--shadow-1); }
.custom-range { display: flex; align-items: center; gap: 6px; border: 1px solid var(--color-border); border-radius: 8px; padding: 4px 8px; }
.custom-range.active { border-color: var(--color-primary); }
.custom-range input { border: none; outline: none; font-size: 12.5px; background: transparent; }
.range-sep { color: var(--color-text-muted); font-size: 12px; }
.reset-btn { margin-left: auto; }

.stat-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 14px; }
.stat-card { padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; }
.stat-value { font-size: 22px; font-weight: 700; }
.stat-label { font-size: 11.5px; color: var(--color-text-muted); }

.charts-row { display: grid; grid-template-columns: 2fr 1fr; gap: 14px; margin-bottom: 14px; }
.chart-card { padding: 12px 16px; }
.chart-card h4 { margin: 0 0 8px; font-size: 13px; color: var(--color-text-muted); }
.chart-el { width: 100%; height: 220px; }

.table-card { padding: 14px 16px; margin-bottom: 14px; }
.table-card-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.table-card-header h4 { margin: 0; font-size: 13px; color: var(--color-text-muted); }
.assignee-search { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12.5px; min-width: 200px; }
.analytics-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.analytics-table th { text-align: left; padding: 6px 8px; color: var(--color-text-muted); font-weight: 600; border-bottom: 1px solid var(--color-border); }
.sortable-th { cursor: pointer; user-select: none; display: table-cell; white-space: nowrap; }
.sortable-th:hover { color: var(--color-text); }
.analytics-table td { padding: 7px 8px; border-bottom: 1px solid var(--color-border); }
.analytics-table tbody tr { cursor: pointer; }
.analytics-table tbody tr:hover { background: #f7f9fc; }
.analytics-table tbody tr.active { background: #eef2ff; }
.analytics-table tbody tr.self-row { background: #fafbfe; }
.analytics-table tbody tr.self-row.active { background: #eef2ff; }
.user-cell { font-weight: 600; }
.empty-row { text-align: center; color: var(--color-text-muted); padding: 14px; }

.user-detail-card { padding: 14px 16px; }
.user-detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.user-detail-header h4 { margin: 0; font-size: 13px; color: var(--color-text-muted); }
.user-select { border: 1px solid var(--color-border); border-radius: 6px; padding: 5px 8px; font-size: 12.5px; }
.self-hint { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--color-primary-dark); background: #eef2ff; border-radius: 8px; padding: 6px 10px; margin: 0 0 10px; }
.user-stat-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin-bottom: 10px; }
.mini-stat { display: flex; flex-direction: column; gap: 2px; border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 10px; }
.mini-stat.warn .mini-value { color: var(--color-danger); }
.mini-value { font-size: 16px; font-weight: 700; }
.mini-label { font-size: 10.5px; color: var(--color-text-muted); }
.bucket-bar { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.bucket-chip { font-size: 11.5px; font-weight: 600; border-radius: 12px; padding: 3px 9px; }
.user-chart-el { height: 200px; }
</style>
