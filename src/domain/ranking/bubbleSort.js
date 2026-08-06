import { isTaskDone } from './rankingScore'

/**
 * "Пузырьковая" сортировка (bubble view) — раздел 3.3 ТЗ TaskBubbler.
 *
 * В отличие от rankingScore.js (единая непрерывная шкала релевантности),
 * здесь задачи жёстко разбиваются на два блока — "Не выполнено" и
 * "Выполнено" — и сортируются внутри каждого блока по собственному,
 * простому и предсказуемому правилу без весов и смешивания факторов:
 *
 * Блок "Не выполнено" — трёхуровневый приоритет позиции (bubbleTier),
 * внутри уровня — сортировка по dueDate (раньше — выше):
 *   Уровень 0: просрочено (dueDate < сегодня 00:00) или срок сегодня.
 *   Уровень 1: срок в будущем (дальше сегодняшнего дня).
 *   Уровень 2: без срока.
 *
 * Блок "Выполнено" — сортировка по completedAt по убыванию (последние
 * завершённые — сверху).
 */

const MS_DAY = 24 * 60 * 60 * 1000

export function bubbleTier(task, now = new Date()) {
  if (!task.dueDate) return 2
  const startOfToday = new Date(now)
  startOfToday.setHours(0, 0, 0, 0)
  const startOfTomorrow = new Date(startOfToday.getTime() + MS_DAY)
  const due = new Date(task.dueDate)
  if (due < startOfTomorrow) return 0 // просрочено или сегодня
  return 1 // будущий срок
}

export const BUBBLE_TIER_LABEL = {
  0: 'Срочно: сегодня или просрочено',
  1: 'Будущий срок',
  2: 'Без срока',
}

export function splitIntoBubbles(tasks, { now = new Date() } = {}) {
  const notDone = []
  const done = []
  for (const task of tasks) {
    if (isTaskDone(task)) done.push(task)
    else notDone.push(task)
  }

  const sortedNotDone = [...notDone].sort((a, b) => {
    const tierA = bubbleTier(a, now)
    const tierB = bubbleTier(b, now)
    if (tierA !== tierB) return tierA - tierB
    if (!a.dueDate && !b.dueDate) return 0
    if (!a.dueDate) return 1
    if (!b.dueDate) return -1
    return new Date(a.dueDate) - new Date(b.dueDate)
  }).map((t) => ({ ...t, __bubbleTier: bubbleTier(t, now) }))

  const sortedDone = [...done].sort((a, b) => {
    const ca = a.completedAt ? new Date(a.completedAt) : new Date(0)
    const cb = b.completedAt ? new Date(b.completedAt) : new Date(0)
    return cb - ca
  })

  return { notDone: sortedNotDone, done: sortedDone }
}
