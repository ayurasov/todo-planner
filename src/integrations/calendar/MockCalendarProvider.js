import { CalendarProvider } from './CalendarProvider'

/**
 * Mock-реализация: имитирует Exchange-подобный провайдер без реального подключения.
 * Реальный EWS-коннектор запланирован как follow-up в v2 (не входит в критерии готовности).
 */
export class MockCalendarProvider extends CalendarProvider {
  constructor() {
    super()
    this._status = 'disconnected'
    this._lastSyncedAt = null
  }

  async connect(config) {
    this._status = 'connected'
    this._config = config
    this._lastSyncedAt = new Date().toISOString()
    return { status: this._status, provider: config?.provider || 'exchange' }
  }

  async disconnect() {
    this._status = 'disconnected'
    return { status: this._status }
  }

  async getStatus() {
    return { status: this._status, lastSyncedAt: this._lastSyncedAt }
  }

  async getBusySlots() {
    if (this._status !== 'connected') return []
    return [
      { start: '2026-08-06T10:00:00', end: '2026-08-06T11:00:00', title: 'Демо-встреча (mock)' },
      { start: '2026-08-07T15:00:00', end: '2026-08-07T15:30:00', title: 'Регулярный стендап (mock)' },
    ]
  }

  async getRecurringMeetings() {
    if (this._status !== 'connected') return []
    return [{ title: 'Еженедельный стендап (mock)', rule: 'weekly, MO,WE,FR 10:00' }]
  }

  async manualResync() {
    this._lastSyncedAt = new Date().toISOString()
    return { lastSyncedAt: this._lastSyncedAt }
  }
}

export const calendarProvider = new MockCalendarProvider()
