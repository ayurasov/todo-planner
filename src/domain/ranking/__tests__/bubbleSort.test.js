import { describe, it, expect } from 'vitest'
import { bubbleTier, splitIntoBubbles, BUBBLE_TIER_LABEL } from '../bubbleSort'

function makeTask(overrides = {}) {
  return {
    id: 't1',
    status: 'open',
    dueDate: null,
    completedAt: null,
    ...overrides,
  }
}

const NOW = new Date('2026-08-11T15:00:00.000Z')

describe('bubbleTier', () => {
  it('returns tier 2 for tasks without a due date', () => {
    expect(bubbleTier(makeTask(), NOW)).toBe(2)
  })

  it('returns tier 0 for overdue tasks', () => {
    expect(bubbleTier(makeTask({ dueDate: '2026-08-10T10:00:00.000Z' }), NOW)).toBe(0)
  })

  it('returns tier 0 for tasks due later today', () => {
    expect(bubbleTier(makeTask({ dueDate: '2026-08-11T23:00:00.000Z' }), NOW)).toBe(0)
  })

  it('returns tier 1 for tasks due tomorrow or later', () => {
    expect(bubbleTier(makeTask({ dueDate: '2026-08-12T00:00:00.000Z' }), NOW)).toBe(1)
    expect(bubbleTier(makeTask({ dueDate: '2026-09-01T00:00:00.000Z' }), NOW)).toBe(1)
  })

  it('exposes human-readable labels for every tier', () => {
    expect(BUBBLE_TIER_LABEL[0]).toBeTruthy()
    expect(BUBBLE_TIER_LABEL[1]).toBeTruthy()
    expect(BUBBLE_TIER_LABEL[2]).toBeTruthy()
  })
})

describe('splitIntoBubbles', () => {
  it('separates done tasks (done/cancelled) from the rest', () => {
    const open = makeTask({ id: 'open', status: 'open' })
    const done = makeTask({ id: 'done', status: 'done', completedAt: '2026-08-11T10:00:00.000Z' })
    const cancelled = makeTask({ id: 'cancelled', status: 'cancelled', completedAt: '2026-08-11T09:00:00.000Z' })

    const { notDone, done: doneList } = splitIntoBubbles([open, done, cancelled], { now: NOW })

    expect(notDone.map((t) => t.id)).toEqual(['open'])
    expect(doneList.map((t) => t.id).sort()).toEqual(['cancelled', 'done'].sort())
  })

  it('orders not-done tasks by tier, then by dueDate within a tier', () => {
    const overdue = makeTask({ id: 'overdue', dueDate: '2026-08-01T00:00:00.000Z' })
    const dueSoon = makeTask({ id: 'due-soon', dueDate: '2026-08-11T20:00:00.000Z' })
    const dueLater = makeTask({ id: 'due-later', dueDate: '2026-08-20T00:00:00.000Z' })
    const noDueDate = makeTask({ id: 'no-due-date' })

    const { notDone } = splitIntoBubbles([noDueDate, dueLater, overdue, dueSoon], { now: NOW })

    expect(notDone.map((t) => t.id)).toEqual(['overdue', 'due-soon', 'due-later', 'no-due-date'])
  })

  it('attaches __bubbleTier to not-done tasks', () => {
    const overdue = makeTask({ id: 'overdue', dueDate: '2026-08-01T00:00:00.000Z' })
    const { notDone } = splitIntoBubbles([overdue], { now: NOW })
    expect(notDone[0].__bubbleTier).toBe(0)
  })

  it('orders done tasks by completedAt descending (most recently completed first)', () => {
    const earlier = makeTask({ id: 'earlier', status: 'done', completedAt: '2026-08-01T00:00:00.000Z' })
    const later = makeTask({ id: 'later', status: 'done', completedAt: '2026-08-10T00:00:00.000Z' })

    const { done } = splitIntoBubbles([earlier, later], { now: NOW })

    expect(done.map((t) => t.id)).toEqual(['later', 'earlier'])
  })

  it('treats missing completedAt as oldest when sorting done tasks', () => {
    const noCompletedAt = makeTask({ id: 'no-completed', status: 'done', completedAt: null })
    const withCompletedAt = makeTask({ id: 'with-completed', status: 'done', completedAt: '2026-08-05T00:00:00.000Z' })

    const { done } = splitIntoBubbles([noCompletedAt, withCompletedAt], { now: NOW })

    expect(done.map((t) => t.id)).toEqual(['with-completed', 'no-completed'])
  })
})
