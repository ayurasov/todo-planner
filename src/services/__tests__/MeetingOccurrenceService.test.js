import { describe, it, expect } from 'vitest'
import { meetingOccurrenceService } from '../MeetingOccurrenceService'

function iso(daysFromNow, hours = 10, minutes = 0) {
  const d = new Date()
  d.setDate(d.getDate() + daysFromNow)
  d.setHours(hours, minutes, 0, 0)
  return d.toISOString()
}

describe('MeetingOccurrenceService.computeNextSuggestedDate', () => {
  it('suggests the series start date/time as the first occurrence when there are none yet', () => {
    const meeting = { id: 'm1', date: iso(-4, 9, 0), recurrence: { freq: 'weekly', weekdays: [1] }, occurrences: [] }
    const suggested = meetingOccurrenceService.computeNextSuggestedDate(meeting)
    expect(suggested).toBe(meeting.date)
  })

  it('suggests the next date after the last existing occurrence, following the recurrence rule', () => {
    const lastOcc = { id: 'occ-1', meetingId: 'm1', date: iso(-4, 9, 0), description: '', link: '' }
    const meeting = { id: 'm1', date: iso(-4, 9, 0), recurrence: { freq: 'daily', weekdays: [] }, occurrences: [lastOcc] }
    const suggested = meetingOccurrenceService.computeNextSuggestedDate(meeting)
    const expected = new Date(lastOcc.date)
    expected.setDate(expected.getDate() + 1)
    expect(new Date(suggested).toDateString()).toBe(expected.toDateString())
    expect(new Date(suggested).getHours()).toBe(9)
  })

  it('keeps the time of day from the series start regardless of which occurrence is last', () => {
    const lastOcc = { id: 'occ-1', meetingId: 'm1', date: iso(3, 14, 30), description: '', link: '' }
    const meeting = { id: 'm1', date: iso(-4, 9, 0), recurrence: { freq: 'weekly', weekdays: [new Date(iso(-4, 9, 0)).getDay()] }, occurrences: [lastOcc] }
    const suggested = meetingOccurrenceService.computeNextSuggestedDate(meeting)
    expect(new Date(suggested).getHours()).toBe(9)
    expect(new Date(suggested).getMinutes()).toBe(0)
  })

  it('returns null when the meeting has no recurrence', () => {
    const meeting = { id: 'm1', date: iso(0), recurrence: null, occurrences: [] }
    expect(meetingOccurrenceService.computeNextSuggestedDate(meeting)).toBeNull()
  })
})

describe('MeetingOccurrenceService.buildOccurrenceDraft', () => {
  it('builds an occurrence bound to the meeting with the given date/description/link', () => {
    const meeting = { id: 'm1', date: iso(-4, 9, 0), recurrence: { freq: 'daily', weekdays: [] }, occurrences: [] }
    const draft = meetingOccurrenceService.buildOccurrenceDraft(meeting, { date: iso(1, 9, 0), description: 'agenda', link: 'https://x' })
    expect(draft.meetingId).toBe('m1')
    expect(draft.description).toBe('agenda')
    expect(draft.link).toBe('https://x')
    expect(draft.date).toBe(iso(1, 9, 0))
  })

  it('falls back to the suggested next date when no date is provided', () => {
    const meeting = { id: 'm1', date: iso(-4, 9, 0), recurrence: { freq: 'daily', weekdays: [] }, occurrences: [] }
    const draft = meetingOccurrenceService.buildOccurrenceDraft(meeting)
    expect(draft.date).toBe(meeting.date)
  })
})
