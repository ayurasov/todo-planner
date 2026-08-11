import { describe, it, expect } from 'vitest'
import {
  RANKING_WEIGHTS,
  computeRankingScore,
  sortTasksByRanking,
  explainVisibility,
  isTaskDone,
} from '../rankingScore'

function makeTask(overrides = {}) {
  return {
    id: 't1',
    title: 'Task',
    status: 'open',
    priority: 'medium',
    dueDate: null,
    lastActivityAt: null,
    assigneeId: null,
    pinned: false,
    listId: 'list-1',
    ...overrides,
  }
}

const NOW = new Date('2026-08-11T12:00:00.000Z')

describe('computeRankingScore', () => {
  it('returns 0 factors for a bare task with no due date/activity/priority match', () => {
    const { score, factors } = computeRankingScore(makeTask({ priority: undefined }), { now: NOW })
    expect(factors.overdue).toBe(0)
    expect(factors.dueSoon).toBe(0)
    expect(factors.pinned).toBe(0)
    expect(factors.assignedToMe).toBe(0)
    expect(score).toBeGreaterThanOrEqual(0)
  })

  it('caps overdue factor at 1 after 7+ days overdue', () => {
    const farOverdue = makeTask({ dueDate: '2026-07-01T00:00:00.000Z' })
    const { factors } = computeRankingScore(farOverdue, { now: NOW })
    expect(factors.overdue).toBe(1)
  })

  it('scales overdue factor linearly within the 7-day window', () => {
    const twoDaysOverdue = makeTask({ dueDate: '2026-08-09T12:00:00.000Z' })
    const { factors } = computeRankingScore(twoDaysOverdue, { now: NOW })
    expect(factors.overdue).toBeCloseTo(2 / 7, 5)
  })

  it('gives dueSoon=1 when due date is exactly now', () => {
    const dueNow = makeTask({ dueDate: NOW.toISOString() })
    const { factors } = computeRankingScore(dueNow, { now: NOW })
    expect(factors.dueSoon).toBeCloseTo(1, 5)
  })

  it('gives dueSoon=0 when due date is more than 3 days away', () => {
    const farFuture = makeTask({ dueDate: '2026-08-20T12:00:00.000Z' })
    const { factors } = computeRankingScore(farFuture, { now: NOW })
    expect(factors.dueSoon).toBe(0)
  })

  it('decays recency factor exponentially as lastActivityAt ages', () => {
    const recentTask = makeTask({ lastActivityAt: '2026-08-11T11:00:00.000Z' })
    const oldTask = makeTask({ lastActivityAt: '2026-08-08T12:00:00.000Z' })
    const { factors: recentFactors } = computeRankingScore(recentTask, { now: NOW })
    const { factors: oldFactors } = computeRankingScore(oldTask, { now: NOW })
    expect(recentFactors.recency).toBeGreaterThan(oldFactors.recency)
    expect(oldFactors.recency).toBeGreaterThanOrEqual(0)
  })

  it('sets assignedToMe=1 only when assigneeId matches currentUserId', () => {
    const task = makeTask({ assigneeId: 'user-1' })
    const { factors: mine } = computeRankingScore(task, { currentUserId: 'user-1', now: NOW })
    const { factors: notMine } = computeRankingScore(task, { currentUserId: 'user-2', now: NOW })
    expect(mine.assignedToMe).toBe(1)
    expect(notMine.assignedToMe).toBe(0)
  })

  it('applies the pinned weight fully when task is pinned', () => {
    const pinned = makeTask({ pinned: true })
    const notPinned = makeTask({ pinned: false })
    const { score: pinnedScore } = computeRankingScore(pinned, { now: NOW })
    const { score: plainScore } = computeRankingScore(notPinned, { now: NOW })
    expect(pinnedScore - plainScore).toBeCloseTo(RANKING_WEIGHTS.pinned, 5)
  })

  it('increases score with higher priority', () => {
    const low = makeTask({ priority: 'low' })
    const urgent = makeTask({ priority: 'urgent' })
    const { score: lowScore } = computeRankingScore(low, { now: NOW })
    const { score: urgentScore } = computeRankingScore(urgent, { now: NOW })
    expect(urgentScore).toBeGreaterThan(lowScore)
  })
})

describe('sortTasksByRanking', () => {
  it('sorts tasks by descending score and attaches __score/__factors', () => {
    const low = makeTask({ id: 'low', priority: 'low' })
    const urgentPinned = makeTask({ id: 'urgent-pinned', priority: 'urgent', pinned: true })
    const sorted = sortTasksByRanking([low, urgentPinned], { now: NOW })

    expect(sorted.map((t) => t.id)).toEqual(['urgent-pinned', 'low'])
    expect(sorted[0]).toHaveProperty('__score')
    expect(sorted[0]).toHaveProperty('__factors')
    expect(sorted[0].__score).toBeGreaterThan(sorted[1].__score)
  })

  it('does not mutate the original array', () => {
    const tasks = [makeTask({ id: 'a' }), makeTask({ id: 'b', pinned: true })]
    const original = [...tasks]
    sortTasksByRanking(tasks, { now: NOW })
    expect(tasks).toEqual(original)
  })
})

describe('explainVisibility', () => {
  it('returns no reasons when task passes all filters', () => {
    const task = makeTask({ status: 'open', listId: 'list-1' })
    const reasons = explainVisibility(task, {
      statusFilter: ['open'],
      listFilter: ['list-1'],
      accessibleListIds: ['list-1'],
    })
    expect(reasons).toEqual([])
  })

  it('explains status mismatch', () => {
    const task = makeTask({ status: 'done' })
    const reasons = explainVisibility(task, { statusFilter: ['open'] })
    expect(reasons.some((r) => r.includes('Статус'))).toBe(true)
  })

  it('explains missing list access', () => {
    const task = makeTask({ listId: 'list-x' })
    const reasons = explainVisibility(task, { accessibleListIds: ['list-1'] })
    expect(reasons.some((r) => r.includes('доступа к списку'))).toBe(true)
  })

  it('explains due date range mismatch', () => {
    const task = makeTask({ dueDate: '2026-08-01T00:00:00.000Z' })
    const reasons = explainVisibility(task, {
      dueRangeFilter: { from: '2026-08-05T00:00:00.000Z', to: '2026-08-20T00:00:00.000Z' },
    })
    expect(reasons.some((r) => r.includes('раньше начала'))).toBe(true)
  })
})

describe('isTaskDone', () => {
  it('treats done and cancelled as done', () => {
    expect(isTaskDone(makeTask({ status: 'done' }))).toBe(true)
    expect(isTaskDone(makeTask({ status: 'cancelled' }))).toBe(true)
  })

  it('treats open and in_progress as not done', () => {
    expect(isTaskDone(makeTask({ status: 'open' }))).toBe(false)
    expect(isTaskDone(makeTask({ status: 'in_progress' }))).toBe(false)
  })
})
