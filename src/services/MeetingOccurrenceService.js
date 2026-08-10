import { createMeetingOccurrence } from '../domain/entities/factories'

/**
 * Логика подвстреч регулярной серии (см. правило пользователя):
 * 1) Первая подвстреча серии — это дата, указанная в самой встрече (meeting.date).
 *    Дальше движемся вперёд по правилу meeting.recurrence.
 * 2) Подвстречи появляются автоматически за день до начала (occurrence.date - 1 день <= now).
 *    Далеко в будущее заранее не генерируем — только следующую после последней уже
 *    существующей, чтобы не плодить сотен пустых записей.
 * 3) Одна подвстреча существует всегда, даже если по ней ещё не начали работать —
 *    просто отображается как "задач на встрече нет", пока не появится первая задача.
 *
 * meeting.recurrence: null | { freq: 'daily'|'weekly'|'biweekly', weekdays: number[] }
 * weekdays актуальны только для weekly/biweekly (0=вс..6=сб). Если для weekly/biweekly
 * weekdays не заданы — считаем, что повтор идёт строго по дню недели исходной даты.
 *
 * Важно: время суток всегда должно совпадать со временем исходной встречи (seriesStart),
 * а не сбрасываться на 00:00 — все вычисления дня недели/совпадения ведутся на
 * отдельных копиях дат, а итоговый candidate всегда возвращается с тем же временем суток,
 * что и seriesStart. Дополнительно withSeriesTime() используется и для самой первой
 * подвстречи серии (см. buildOccurrences), а не только для последующих — ранее первая
 * подвстреча брала seriesStart "as is", и если он по какой-то причине содержал 00:00
 * (например, встреча была отредактирована без явного времени), это значение так и
 * оставалось зафиксированным навсегда в existing[0], а normalizeOccurrences ниже чинит
 * уже сохранённые записи с таким дефектом.
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
 * fromDate/candidate, чтобы возможные мутации времени в части promiseных вычислений не могли
 * случайно обнулить время подвстречи до 00:00.
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

  // Ищем следующий подходящий день, двигаясь по дням, но ограничиваем шаг между
  // "неделями повтора" через привязку к seriesStart, чтобы раз в 2 недели не
  // превращалось в раз в неделю при нескольких выбранных днях.
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
   * Возвращает актуальный список occurrences для встречи, дополняя его при
   * необходимости. Не мутирует meeting напрямую (вызывающий код (store)
   * решает, нужно ли сохранять результат.
   */
  buildOccurrences(meeting, { now = new Date() } = {}) {
    if (!meeting.recurrence) return []

    const existing = this.normalizeOccurrences(meeting)
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
      existing.push(createMeetingOccurrence({ meetingId: meeting.id, date: next.toISOString() }))
      if (next > genThreshold) break
    }

    return existing
  }

  /**
   * Исправляет уже сохранённые occurrences, у которых время суток равно 00:00,
   * хотя время исходной встречи (meeting.date) — не 00:00. Такие записи могли
   * появиться до фикса генератора или из старых версий localStorage-данных.
   * Первая подвстреча серии (существующая до этого фикса) — самый частый случай:
   * она создавалась "as is" из seriesStart без прогонки через withSeriesTime().
   * День (число/месяц/год) occurrence никогда не трогаем — меняем только часы/минуты.
   */
  normalizeOccurrences(meeting) {
    const seriesTime = new Date(meeting.date)
    const hours = seriesTime.getHours()
    const minutes = seriesTime.getMinutes()
    const seriesIsMidnight = hours === 0 && minutes === 0
    const list = [...(meeting.occurrences || [])].sort((a, b) => new Date(a.date) - new Date(b.date))
    if (seriesIsMidnight) return list
    return list.map((occ) => {
      const d = new Date(occ.date)
      if (d.getHours() === 0 && d.getMinutes() === 0) {
        return { ...occ, date: withTime(d, hours, minutes).toISOString() }
      }
      return occ
    })
  }
}

export const meetingOccurrenceService = new MeetingOccurrenceService()
