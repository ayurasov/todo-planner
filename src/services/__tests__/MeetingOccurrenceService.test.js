import { describe, it, expect } from 'vitest'
import { meetingOccurrenceService } from '../MeetingOccurrenceService'

function iso(daysFromNow, hours = 10, minutes = 0) {
  const d = new Date()
  d.setDate(d.getDate() + daysFromNow)
  d.setHours(hours, minutes, 0, 0)
  return d.toISOString()
}

describe('MeetingOccurrenceService.buildMergedOccurrences', () => {
  it('keeps past occurrences untouched when recurrence/time changes', () => {
    const pastOcc = { id: 'occ-past', meetingId: 'm1', date: iso(-10), description: 'заметки прошлой встречи', link: '' }
    const meeting = {
      id: 'm1',
      date: iso(-10),
      recurrence: { freq: 'weekly', weekdays: [1] },
      occurrences: [pastOcc],
    }

    const merged = meetingOccurrenceService.buildMergedOccurrences(meeting, {
      date: iso(0, 15, 30),
      recurrence: { freq: 'daily', weekdays: [] },
      hasTasks: () => false,
    })

    const keptPast = merged.find((o) => o.id === 'occ-past')
    expect(keptPast).toBeTruthy()
    expect(keptPast.date).toBe(pastOcc.date)
    expect(keptPast.description).toBe('заметки прошлой встречи')
  })

  it('preserves future occurrence id/date when it already has tasks, even if schedule changes', () => {
    const futureOcc = { id: 'occ-future-1', meetingId: 'm1', date: iso(3, 9, 0), description: '', link: '' }
    const meeting = {
      id: 'm1',
      date: iso(-4, 9, 0),
      recurrence: { freq: 'weekly', weekdays: [new Date(iso(-4, 9, 0)).getDay()] },
      occurrences: [futureOcc],
    }

    const merged = meetingOccurrenceService.buildMergedOccurrences(meeting, {
      recurrence: { freq: 'daily', weekdays: [] },
      hasTasks: (id) => id === 'occ-future-1',
    })

    const preserved = merged.find((o) => o.id === 'occ-future-1')
    expect(preserved).toBeTruthy()
    expect(preserved.date).toBe(futureOcc.date)
  })

  it('drops empty future occurrences without tasks and regenerates by new rule', () => {
    const emptyFuture = { id: 'occ-empty', meetingId: 'm1', date: iso(20, 9, 0), description: '', link: '' }
    const meeting = {
      id: 'm1',
      date: iso(-4, 9, 0),
      recurrence: { freq: 'weekly', weekdays: [new Date(iso(-4, 9, 0)).getDay()] },
      occurrences: [emptyFuture],
    }

    const merged = meetingOccurrenceService.buildMergedOccurrences(meeting, {
      recurrence: { freq: 'daily', weekdays: [] },
      hasTasks: () => false,
    })

    expect(merged.find((o) => o.id === 'occ-empty')).toBeFalsy()
    expect(merged.length).toBeGreaterThan(0)
  })

  it('returns empty array when recurrence is disabled', () => {
    const meeting = { id: 'm1', date: iso(0), recurrence: { freq: 'daily', weekdays: [] }, occurrences: [] }
    const merged = meetingOccurrenceService.buildMergedOccurrences(meeting, { recurrence: null, hasTasks: () => false })
    expect(merged).toEqual([])
  })
})
