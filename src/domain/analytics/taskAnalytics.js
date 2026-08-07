import { TaskStatus, HistoryEventType } from '../entities/enums'

/**
 * Набор чистых функций для страницы аналитики (AnalyticsView.vue).
 * Всё стрится исключительно над уже загруженными в памяти tasksStore.tasks и
 * historyStore.globalLog — без дополнительных запросов к репозиторию.
 *
 * Важно: в текущей модели у task нет надёжного createdBy (см. factories.js) — поэтому
 * "кто создал задачу" выводится из истории (HistoryEventType.CREATED, actorId), а не из самих задач.
 */

function dayKey(iso) {
  return iso ? iso.slice(0, 10) : null
}

function diffDays(a, b) {
  return (new Date(a).getTime() - new Date(b).getTime()) / 86400000
}

/**
 * Классификация завершённой задачи относительно срока:
 * 'no_due' — без срока, 'early' — завершена более чем за 12 часов до срока,
 * 'on_time' — в день срока или раньше (но не «заранее»), 'late' — после срока.
 */
function completionBucket(task) {
  if (!task.completedAt) return null
  if (!task.dueDate) return 'no_due'
  const delta = diffDays(task.dueDate, task.completedAt)
  if (delta > 0.5) return 'early'
  if (delta >= 0) return 'on_time'
  return 'late'
}

/**
 * Общая фильтрация задач и записей истории под панель фильтров аналитики
 * (интервал дат по createdAt задачи/события, набор списков, набор встреч).
 * Пустые массивы listIds/meetingIds означают «без ограничения по этому измерению».
 * Применяется единообразно ко всем графикам и таблицам, включая индивидуальную статистику.
 */
export function filterTasksAndHistory(tasks, historyEntries, { dateFrom, dateTo, listIds = [], meetingIds = [] } = {}) {
  const fromTs = dateFrom ? new Date(`${dateFrom}T00:00:00`).getTime() : null
  const toTs = dateTo ? new Date(`${dateTo}T23:59:59.999`).getTime() : null
  const hasListFilter = listIds.length > 0
  const hasMeetingFilter = meetingIds.length > 0

  const inRange = (iso) => {
    if (!iso) return false
    const ts = new Date(iso).getTime()
    if (fromTs !== null && ts < fromTs) return false
    if (toTs !== null && ts > toTs) return false
    return true
  }

  const matchesTask = (t) => {
    if (!inRange(t.createdAt)) return false
    if (hasListFilter && !listIds.includes(t.listId)) return false
    if (hasMeetingFilter && !meetingIds.includes(t.meetingId)) return false
    return true
  }

  const filteredTasks = tasks.filter(matchesTask)
  const taskIds = new Set(filteredTasks.map((t) => t.id))
  const filteredHistory = historyEntries.filter((e) => taskIds.has(e.taskId) && inRange(e.timestamp))

  return { tasks: filteredTasks, history: filteredHistory }
}

export function buildOverviewStats(tasks, historyEntries) {
  const created = tasks.length
  const completed = tasks.filter((t) => t.status === TaskStatus.DONE).length
  const cancelled = tasks.filter((t) => t.status === TaskStatus.CANCELLED).length
  const open = created - completed - cancelled
  const rescheduleEvents = historyEntries.filter((e) => e.type === HistoryEventType.RESCHEDULED)

  const buckets = { early: 0, on_time: 0, late: 0, no_due: 0 }
  for (const t of tasks) {
    const b = completionBucket(t)
    if (b) buckets[b] += 1
  }

  return {
    created, completed, cancelled, open,
    completionRate: created ? Math.round((completed / created) * 100) : 0,
    onTimeRate: completed ? Math.round(((buckets.early + buckets.on_time) / completed) * 100) : 0,
    rescheduleCount: rescheduleEvents.length,
    buckets,
  }
}

export function buildTimeline(tasks, field) {
  const map = {}
  for (const t of tasks) {
    const key = dayKey(t[field])
    if (!key) continue
    map[key] = (map[key] || 0) + 1
  }
  const days = Object.keys(map).sort()
  return { days, counts: days.map((d) => map[d]) }
}

/**
 * Статистика по каждому исполнителю (assigneeId) + "создано" из истории (actorId события CREATED).
 * Возвращает массив, отсортированный по имени — currentUserId (если передан) всегда закреплён первой строкой.
 */
export function buildPerAssigneeStats(tasks, historyEntries, users, currentUserId = null) {
  const result = new Map()
  const ensure = (userId) => {
    if (!result.has(userId)) {
      result.set(userId, {
        userId, created: 0, assigned: 0, completed: 0, cancelled: 0, open: 0,
        early: 0, onTime: 0, late: 0, rescheduled: 0,
      })
    }
    return result.get(userId)
  }

  for (const e of historyEntries) {
    if (e.type === HistoryEventType.CREATED && e.actorId) ensure(e.actorId).created += 1
    if (e.type === HistoryEventType.RESCHEDULED && e.actorId) ensure(e.actorId).rescheduled += 1
  }

  for (const t of tasks) {
    if (!t.assigneeId) continue
    const s = ensure(t.assigneeId)
    s.assigned += 1
    if (t.status === TaskStatus.DONE) s.completed += 1
    else if (t.status === TaskStatus.CANCELLED) s.cancelled += 1
    else s.open += 1
    const b = completionBucket(t)
    if (b === 'early') s.early += 1
    else if (b === 'on_time') s.onTime += 1
    else if (b === 'late') s.late += 1
  }

  if (currentUserId) ensure(currentUserId)

  for (const s of result.values()) {
    s.completionRate = s.assigned ? Math.round((s.completed / s.assigned) * 100) : 0
    s.onTimeRate = s.completed ? Math.round(((s.early + s.onTime) / s.completed) * 100) : 0
  }

  const rows = [...result.values()].sort(
    (a, b) => (users.find((u) => u.id === b.userId)?.name || '').localeCompare(users.find((u) => u.id === a.userId)?.name || ''),
  )

  if (!currentUserId) return rows
  const selfIdx = rows.findIndex((r) => r.userId === currentUserId)
  if (selfIdx === -1) return rows
  const [self] = rows.splice(selfIdx, 1)
  return [self, ...rows]
}

/**
 * Расширенная детализация по одному конкретному пользователю — используется для блока
 * "особенно развёрнуто про себя" на странице аналитики.
 */
export function buildUserDetail(userId, tasks, historyEntries) {
  const assignedTasks = tasks.filter((t) => t.assigneeId === userId)
  const createdEvents = historyEntries.filter((e) => e.type === HistoryEventType.CREATED && e.actorId === userId)
  const rescheduleEvents = historyEntries.filter((e) => e.type === HistoryEventType.RESCHEDULED && e.actorId === userId)
  const completedTasks = assignedTasks.filter((t) => t.status === TaskStatus.DONE)

  const durations = completedTasks
    .filter((t) => t.createdAt && t.completedAt)
    .map((t) => diffDays(t.completedAt, t.createdAt))
  const avgCompletionDays = durations.length
    ? Math.round((durations.reduce((a, b) => a + b, 0) / durations.length) * 10) / 10
    : null

  const buckets = { early: 0, on_time: 0, late: 0, no_due: 0 }
  for (const t of completedTasks) {
    const b = completionBucket(t)
    if (b) buckets[b] += 1
  }

  const overdueOpen = assignedTasks.filter(
    (t) => t.dueDate && t.status !== TaskStatus.DONE && t.status !== TaskStatus.CANCELLED && new Date(t.dueDate) < new Date(),
  ).length

  return {
    userId,
    assignedCount: assignedTasks.length,
    createdCount: createdEvents.length,
    completedCount: completedTasks.length,
    openCount: assignedTasks.filter((t) => t.status === TaskStatus.OPEN || t.status === TaskStatus.IN_PROGRESS).length,
    overdueOpen,
    rescheduleCount: rescheduleEvents.length,
    completionRate: assignedTasks.length ? Math.round((completedTasks.length / assignedTasks.length) * 100) : 0,
    onTimeRate: completedTasks.length ? Math.round(((buckets.early + buckets.on_time) / completedTasks.length) * 100) : 0,
    avgCompletionDays,
    buckets,
    timelineCreated: buildTimeline(assignedTasks, 'createdAt'),
    timelineCompleted: buildTimeline(completedTasks, 'completedAt'),
  }
}
