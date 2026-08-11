import { createMeetingOccurrence } from '../domain/entities/factories'

/**
 * Логика подвстреч регулярной серии (новая модель — добавление вручную, см.
 * обсуждение багов автогенерации occurrences):
 *
 * 1) При создании регулярной встречи occurrences НЕ генерируются автоматически.
 *    Существует только сама встреча (meeting.date — дата её создания/старта серии,
 *    используется исключительно как опорная точка для расчёта дня недели/шага
 *    повторения, в UI встречи отображается только время, а не дата).
 * 2) Каждая подвстреча добавляется пользователем вручную через кнопку
 *    "Добавить подвстречу серии" (см. MeetingDetailView). Дата/время следующей
 *    подвстречи предзаполняются по правилу recurrence (computeNextSuggestedDate),
 *    но пользователь может их поправить перед сохранением — а также сразу
 *    заполнить описание и ссылку на материалы.
 * 3) Автогенерация "на день вперёд" удалена полностью (buildOccurrences/
 *    ensureOccurrences), т.к. именно она была источником путаницы и обрывов связи
 *    occurrenceId у задач при пересборке серии.
 *
 * meeting.recurrence: null | { freq: 'daily'|'weekly'|'biweekly', weekdays: number[] }
 * weekdays актуальны только для weekly/biweekly (0=вс..6=сб). Если для weekly/biweekly
 * weekdays не заданы — считаем, что повтор идёт строго по дню недели исходной даты.
 */

function addDays(date, days) {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

function matchesWeekday(date, weekdays) {
  if (!weekdays || !weekdays.length) return true
  return weekdays.includes(date.getDay())
}

function startOfDay(date) {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

function withTime(date, hours, minutes) {
  const d = new Date(date)
  d.setHours(hours, minutes, 0, 0)
  return d
}

/**
 * Вычисляет следующую дату после `fromDate` (не включая её), удовлетворяющую
 * правилу recurrence. Для daily — просто +1 день. Для weekly/biweekly с заданными
 * weekdays — перебираем дни вперёд, пока не найдём подходящий день недели, учитывая
 * шаг в неделях (интервал между "витками" по weekdays: каждую неделю или раз в 2).
 *
 * Время результата всегда берётся из seriesStart (время исходной встречи), а не из
 * fromDate/candidate.
 */
function nextOccurrenceDate(fromDate, recurrence, seriesStart) {
  const stepDays = recurrence.freq === 'biweekly' ? 14 : 7
  const seriesTime = new Date(seriesStart)
  const hours = seriesTime.getHours()
  const minutes = seriesTime.getMinutes()

  function withSeriesTime(date) { return withTime(date, hours, minutes) }

  if (recurrence.freq === 'daily') return withSeriesTime(addDays(fromDate, 1))

  const weekdays = recurrence.weekdays && recurrence.weekdays.length
    ? recurrence.weekdays
    : [seriesTime.getDay()]

  let candidate = addDays(fromDate, 1)
  const seriesStartDay = startOfDay(seriesStart)
  for (let i = 0; i < 60; i += 1) {
    const candidateDay = startOfDay(candidate)
    const daysSinceStart = Math.round((candidateDay - seriesStartDay) / 86400000)
    const weekIndex = Math.floor(daysSinceStart / 7)
    const isRightWeek = recurrence.freq !== 'biweekly' || weekIndex % 2 === 0
    if (isRightWeek && matchesWeekday(candidate, weekdays)) return withSeriesTime(candidate)
    candidate = addDays(candidate, 1)
  }
  return withSeriesTime(addDays(fromDate, stepDays))
}

export class MeetingOccurrenceService {
  /**
   * Предлагает дату/время следующей подвстречи серии для предзаполнения формы
   * "Добавить подвстречу серии": берёт дату последней существующей подвстречи
   * (либо дату создания встречи, если подвстреч ещё нет) и считает следующую
   * по правилу recurrence. Если такая дата уже существует среди occurrences —
   * возвращает null (в UI это означает "такая подвстреча уже есть", пользователь
   * должен либо открыть её, либо вручную задать другую дату).
   */
  computeNextSuggestedDate(meeting) {
    if (!meeting.recurrence) return null
    const existing = [...(meeting.occurrences || [])].sort((a, b) => new Date(a.date) - new Date(b.date))
    const seriesStart = meeting.date
    const last = existing.length ? existing[existing.length - 1] : null
    const base = last ? new Date(last.date) : new Date(seriesStart)
    if (!last) return base.toISOString()
    return nextOccurrenceDate(base, meeting.recurrence, seriesStart).toISOString()
  }

  /**
   * Создаёт объект новой подвстречи (не сохраняет её) — используется формой
   * "Добавить подвстречу серии" перед вызовом meetingsStore.addOccurrence.
   */
  buildOccurrenceDraft(meeting, { date, description = '', link = '' } = {}) {
    return createMeetingOccurrence({
      meetingId: meeting.id,
      date: date || this.computeNextSuggestedDate(meeting) || meeting.date,
      description,
      link,
    })
  }
}

export const meetingOccurrenceService = new MeetingOccurrenceService()
