import { createMeetingOccurrence } from '../domain/entities/factories'

/**
 * Логика подвстреч регулярной серии (см. правило пользователя):
 * 1) Первая подвстреча серии — это дата, указанная в самой встрече (meeting.date).
 *    Дальше движемся вперёд по правилу meeting.recurrence.
 * 2) Подвстречи появляются автоматически за день до начала (occurrence.date - 1 день <= now).
 *    Далеко в будущее заранее не генерируем — только следующую после последней уже
 *    существующей, чтобы не плодить сотни пустых записей.
 * 3) Одна подвстреча существует всегда, даже если по ней ещё не начали работать —
 *    просто отображается как "задач на встрече нет", пока не появится первая задача.
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

/**
 * Вычисляет следующую дату после `fromDate` (не включая её), удовлетворяющую
 * правилу recurrence. Для daily — просто +1 день. Для weekly/biweekly с заданными
 * weekdays — перебираем дни вперёд, пока не найдём подходящий день недели, учитывая
 * шаг в неделях (интервал между "витками" по weekdays: каждую неделю или раз в 2).
 */
function nextOccurrenceDate(fromDate, recurrence, seriesStart) {
  const stepDays = recurrence.freq === 'biweekly' ? 14 : 7
  if (recurrence.freq === 'daily') return addDays(fromDate, 1)

  const weekdays = recurrence.weekdays && recurrence.weekdays.length
    ? recurrence.weekdays
    : [new Date(seriesStart).getDay()]

  // Ищем следующий подходящий день, двигаясь по дням, но ограничиваем шаг между
  // "неделями повтора" через привязку к seriesStart, чтобы раз в 2 недели не
  // превращалось в раз в неделю при нескольких выбранных днях.
  let candidate = addDays(fromDate, 1)
  for (let i = 0; i < 60; i += 1) {
    const daysSinceStart = Math.floor((candidate.setHours(0, 0, 0, 0) - new Date(seriesStart).setHours(0, 0, 0, 0)) / 86400000)
    const weekIndex = Math.floor(daysSinceStart / 7)
    const isRightWeek = recurrence.freq !== 'biweekly' || weekIndex % 2 === 0
    if (isRightWeek && matchesWeekday(candidate, weekdays)) return candidate
    candidate = addDays(candidate, 1)
  }
  return addDays(fromDate, stepDays)
}

export class MeetingOccurrenceService {
  /**
   * Возвращает актуальный список occurrences для встречи, дополняя его при
   * необходимости. Не мутирует meeting напрямую — вызывающий код (store)
   * решает, нужно ли сохранять результат.
   */
  buildOccurrences(meeting, { now = new Date() } = {}) {
    if (!meeting.recurrence) return []

    const existing = [...(meeting.occurrences || [])].sort((a, b) => new Date(a.date) - new Date(b.date))
    const seriesStart = meeting.date

    if (!existing.length) {
      existing.push(createMeetingOccurrence({ meetingId: meeting.id, date: seriesStart }))
    }

    const genThreshold = addDays(now, 1) // подвстреча должна существовать за день до начала
    let guard = 0
    while (guard < 200) {
      guard += 1
      const last = existing[existing.length - 1]
      if (new Date(last.date) >= genThreshold) break
      const next = nextOccurrenceDate(last.date, meeting.recurrence, seriesStart)
      if (next > genThreshold) {
        existing.push(createMeetingOccurrence({ meetingId: meeting.id, date: next.toISOString() }))
        break
      }
      existing.push(createMeetingOccurrence({ meetingId: meeting.id, date: next.toISOString() }))
    }

    return existing
  }
}

export const meetingOccurrenceService = new MeetingOccurrenceService()
