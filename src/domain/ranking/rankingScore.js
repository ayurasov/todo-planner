import { PRIORITY_WEIGHT, TaskStatus } from '../entities/enums'

// Прозрачные веса ranking-алгоритма (см. раздел 6 утверждённой архитектуры).
// Зафиксированы как константы по решению заказчика (допущение #2).
export const RANKING_WEIGHTS = {
  overdue: 3.0,
  dueSoon: 2.0,
  recency: 2.5,
  assignedToMe: 1.0,
  pinned: 5.0,
  priority: 1.5,
}

const MS_DAY = 24 * 60 * 60 * 1000
const RECENCY_DECAY_HOURS = 36 // время "остывания" бонуса вываливания вверх

function overdueFactor(dueDate, now) {
  if (!dueDate) return 0
  const diffDays = (now - new Date(dueDate)) / MS_DAY
  if (diffDays <= 0) return 0
  return Math.min(1, diffDays / 7) // капируется за 7 дней просрочки
}

function dueSoonFactor(dueDate, now) {
  if (!dueDate) return 0
  const diffDays = (new Date(dueDate) - now) / MS_DAY
  if (diffDays < 0) return 0 // просрочку считает overdueFactor
  if (diffDays > 3) return 0
  return 1 - diffDays / 3 // максимум сегодня/завтра
}

function recencyFactor(lastActivityAt, now) {
  if (!lastActivityAt) return 0
  const hours = (now - new Date(lastActivityAt)) / (60 * 60 * 1000)
  if (hours < 0) return 1
  return Math.exp(-hours / RECENCY_DECAY_HOURS)
}

/**
 * Вычисляет ranking score задачи для текущего пользователя.
 * Возвращает score и разложение по факторам (для отладки/прозрачности UI).
 */
export function computeRankingScore(task, { currentUserId, now = new Date() } = {}) {
  const w = RANKING_WEIGHTS
  const factors = {
    overdue: overdueFactor(task.dueDate, now),
    dueSoon: dueSoonFactor(task.dueDate, now),
    recency: recencyFactor(task.lastActivityAt, now),
    assignedToMe: task.assigneeId === currentUserId ? 1 : 0,
    pinned: task.pinned ? 1 : 0,
    priority: PRIORITY_WEIGHT[task.priority] ?? 0.5,
  }
  const score =
    w.overdue * factors.overdue +
    w.dueSoon * factors.dueSoon +
    w.recency * factors.recency +
    w.assignedToMe * factors.assignedToMe +
    w.pinned * factors.pinned +
    w.priority * factors.priority

  return { score, factors }
}

export function sortTasksByRanking(tasks, opts) {
  return [...tasks]
    .map((task) => ({ task, ranking: computeRankingScore(task, opts) }))
    .sort((a, b) => b.ranking.score - a.ranking.score)
    .map((x) => ({ ...x.task, __score: x.ranking.score, __factors: x.ranking.factors }))
}

/**
 * Отвечает на вопрос "почему задачи здесь нет" — прозрачное объяснение
 * условий исчезания из текущего представления (раздел 6 архитектуры).
 */
export function explainVisibility(task, { statusFilter, assigneeFilter, listFilter, dueRangeFilter, currentUserId, accessibleListIds } = {}) {
  const reasons = []
  if (statusFilter && statusFilter.length && !statusFilter.includes(task.status)) {
    reasons.push(`Статус задачи "${task.status}" не входит в фильтр (${statusFilter.join(', ')})`)
  }
  if (assigneeFilter && task.assigneeId !== assigneeFilter) {
    reasons.push('Задача назначена на другого исполнителя')
  }
  if (listFilter && listFilter.length && !listFilter.includes(task.listId)) {
    reasons.push('Задача находится в другом списке')
  }
  if (accessibleListIds && !accessibleListIds.includes(task.listId)) {
    reasons.push('У вас нет доступа к списку этой задачи')
  }
  if (dueRangeFilter && task.dueDate) {
    const d = new Date(task.dueDate)
    if (dueRangeFilter.from && d < new Date(dueRangeFilter.from)) reasons.push('Срок раньше начала диапазона представления')
    if (dueRangeFilter.to && d > new Date(dueRangeFilter.to)) reasons.push('Срок позже конца диапазона представления')
  }
  return reasons
}

export function isTaskDone(task) {
  return task.status === TaskStatus.DONE || task.status === TaskStatus.CANCELLED
}
