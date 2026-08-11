import { describe, it, expect, vi, beforeEach } from 'vitest'
import { computeNextOccurrence, RecurrenceService } from '../RecurrenceService'
import { RecurrenceFreq, RecurrenceType } from '../../domain/entities/enums'

vi.mock('../../repositories', () => ({
  taskRepository: { create: vi.fn() },
  recurrenceRepository: { update: vi.fn(), getById: vi.fn() },
}))

import { taskRepository, recurrenceRepository } from '../../repositories'

describe('computeNextOccurrence', () => {
  it('adds `interval` days for a daily rule (default interval=1)', () => {
    const next = computeNextOccurrence('2026-08-11T00:00:00.000Z', { freq: RecurrenceFreq.DAILY })
    expect(next.getDate()).toBe(12)
  })

  it('respects a custom daily interval', () => {
    const next = computeNextOccurrence('2026-08-11T00:00:00.000Z', { freq: RecurrenceFreq.DAILY, interval: 5 })
    expect(next.getDate()).toBe(16)
  })

  it('adds `interval` weeks (7 * interval days) for a weekly rule', () => {
    const next = computeNextOccurrence('2026-08-01T00:00:00.000Z', { freq: RecurrenceFreq.WEEKLY, interval: 2 })
    const from = new Date('2026-08-01T00:00:00.000Z')
    const diffDays = (next - from) / (24 * 60 * 60 * 1000)
    expect(diffDays).toBe(14)
  })

  it('advances by `interval` months for a monthly rule, keeping the day', () => {
    const next = computeNextOccurrence('2026-01-15T00:00:00.000Z', { freq: RecurrenceFreq.MONTHLY, interval: 1 })
    expect(next.getMonth()).toBe(1)
    expect(next.getDate()).toBe(15)
  })

  it('uses byMonthDay override when provided', () => {
    const next = computeNextOccurrence('2026-01-05T00:00:00.000Z', {
      freq: RecurrenceFreq.MONTHLY,
      interval: 1,
      byMonthDay: 28,
    })
    expect(next.getMonth()).toBe(1)
    expect(next.getDate()).toBe(28)
  })

  it('rolls a non-existent target day (e.g. 31 in February) back to the last valid day', () => {
    const next = computeNextOccurrence('2026-01-01T00:00:00.000Z', {
      freq: RecurrenceFreq.MONTHLY,
      interval: 1,
      byMonthDay: 31,
    })
    expect(next.getMonth()).toBe(1)
    expect(next.getDate()).toBe(28)
  })

  it('falls back to +interval days for unknown/custom freq', () => {
    const next = computeNextOccurrence('2026-08-11T00:00:00.000Z', { freq: RecurrenceFreq.CUSTOM, interval: 3 })
    expect(next.getDate()).toBe(14)
  })
})

describe('RecurrenceService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('generateNextInstance creates a task from the template and updates lastGeneratedInstanceDate', async () => {
    taskRepository.create.mockResolvedValue({ id: 'new-task' })
    const service = new RecurrenceService()
    const template = { id: 'tpl-1', listId: 'list-1', titleTemplate: 'Weekly review', rule: { freq: RecurrenceFreq.WEEKLY, interval: 1 } }
    const fromTask = { dueDate: '2026-08-01T00:00:00.000Z', assigneeId: 'user-1' }

    const result = await service.generateNextInstance(template, fromTask)

    expect(taskRepository.create).toHaveBeenCalledWith(
      expect.objectContaining({
        listId: 'list-1',
        title: 'Weekly review',
        recurrenceTemplateId: 'tpl-1',
        assigneeId: 'user-1',
      }),
    )
    expect(recurrenceRepository.update).toHaveBeenCalledWith('tpl-1', expect.objectContaining({ lastGeneratedInstanceDate: expect.any(String) }))
    expect(result).toEqual({ id: 'new-task' })
  })

  it('onTaskCompleted returns null when task has no recurrenceTemplateId', async () => {
    const service = new RecurrenceService()
    const result = await service.onTaskCompleted({ id: 'task-1' })
    expect(result).toBeNull()
    expect(recurrenceRepository.getById).not.toHaveBeenCalled()
  })

  it('onTaskCompleted returns null when template is not found', async () => {
    recurrenceRepository.getById.mockResolvedValue(null)
    const service = new RecurrenceService()
    const result = await service.onTaskCompleted({ id: 'task-1', recurrenceTemplateId: 'missing' })
    expect(result).toBeNull()
  })

  it('onTaskCompleted generates the next instance for completion_based templates', async () => {
    recurrenceRepository.getById.mockResolvedValue({
      id: 'tpl-1',
      type: RecurrenceType.COMPLETION_BASED,
      rule: { freq: RecurrenceFreq.DAILY },
      listId: 'list-1',
      titleTemplate: 'Daily standup',
    })
    taskRepository.create.mockResolvedValue({ id: 'new-task' })

    const service = new RecurrenceService()
    const result = await service.onTaskCompleted({ id: 'task-1', recurrenceTemplateId: 'tpl-1', dueDate: '2026-08-11T00:00:00.000Z' })

    expect(taskRepository.create).toHaveBeenCalled()
    expect(result).toEqual({ id: 'new-task' })
  })

  it('onTaskCompleted does not generate a new instance for fixed_schedule templates', async () => {
    recurrenceRepository.getById.mockResolvedValue({
      id: 'tpl-1',
      type: RecurrenceType.FIXED_SCHEDULE,
      rule: { freq: RecurrenceFreq.DAILY },
    })

    const service = new RecurrenceService()
    const result = await service.onTaskCompleted({ id: 'task-1', recurrenceTemplateId: 'tpl-1' })

    expect(result).toBeNull()
    expect(taskRepository.create).not.toHaveBeenCalled()
  })
})
