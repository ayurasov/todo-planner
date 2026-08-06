/**
 * Контракт провайдера календаря. Не привязан к Exchange — любой провайдер
 * (Exchange/Google/иной) реализует этот интерфейс (раздел "Требования к Exchange").
 */
export class CalendarProvider {
  async connect(_config) { throw new Error('Not implemented') }
  async disconnect() { throw new Error('Not implemented') }
  async getStatus() { throw new Error('Not implemented') }
  async getBusySlots(_rangeFrom, _rangeTo) { throw new Error('Not implemented') }
  async getRecurringMeetings() { throw new Error('Not implemented') }
  async manualResync() { throw new Error('Not implemented') }
}
