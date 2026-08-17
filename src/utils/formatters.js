export function formatDate(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' })
}

export function formatDateTime(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export function isOverdue(dueDate, status) {
  if (!dueDate || status === 'done' || status === 'cancelled') return false
  return new Date(dueDate) < new Date()
}

/**
 * Компактная относительная метка для "давности" момента (используется для
 * "последнее изменение", в отличие от relativeDay, которая про день недели
 * относительно due date). Возвращает "только что" / "5 мин назад" /
 * "3 ч назад" / дату, если прошло больше суток.
 */
export function relativeTimeAgo(iso) {
  if (!iso) return null
  const diffMs = Date.now() - new Date(iso).getTime()
  const diffMin = Math.round(diffMs / 60000)
  if (diffMin < 1) return 'только что'
  if (diffMin < 60) return `${diffMin} мин назад`
  const diffHours = Math.round(diffMin / 60)
  if (diffHours < 24) return `${diffHours} ч назад`
  const diffDays = Math.round(diffHours / 24)
  if (diffDays === 1) return 'вчера'
  if (diffDays < 7) return `${diffDays} дн назад`
  return formatDate(iso)
}

export function relativeDay(iso) {
  if (!iso) return null
  const d = new Date(iso)
  const now = new Date()
  const diffDays = Math.round((d.setHours(0,0,0,0) - now.setHours(0,0,0,0)) / 86400000)
  if (diffDays === 0) return 'Сегодня'
  if (diffDays === 1) return 'Завтра'
  if (diffDays === -1) return 'Вчера'
  if (diffDays < 0) return `Просрочено на ${Math.abs(diffDays)} дн.`
  return formatDate(iso)
}

const WEEKDAY_LABEL_SHORT = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб']
const WEEKDAY_LABEL_GENITIVE_PLURAL = {
  1: 'понедельникам', 2: 'вторникам', 3: 'средам', 4: 'четвергам',
  5: 'пятницам', 6: 'субботам', 0: 'воскресеньям',
}

/**
 * Человекочитаемое описание регулярности встречи для карточки/списка встреч.
 * Модель: meeting.recurrence = null | { freq: 'daily'|'weekly'|'biweekly', weekdays: number[] }
 * weekdays — номера дней недели (0=вс..6=сб), актуальны только для weekly/biweekly.
 * Если recurrence отсутствует — встреча считается разовой.
 */
export function formatTime(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

export function formatMeetingRecurrence(recurrence) {
  if (!recurrence || !recurrence.freq) return 'Разовая'
  const days = [...(recurrence.weekdays || [])].sort((a, b) => a - b)
  const daysLabel = days.length
    ? days.map((d) => WEEKDAY_LABEL_GENITIVE_PLURAL[d] || WEEKDAY_LABEL_SHORT[d]).join(', ')
    : null

  switch (recurrence.freq) {
    case 'daily':
      return 'Регулярная: каждый день'
    case 'weekly':
      return daysLabel ? `Регулярная: каждую неделю по ${daysLabel}` : 'Регулярная: каждую неделю'
    case 'biweekly':
      return daysLabel ? `Регулярная: раз в 2 недели по ${daysLabel}` : 'Регулярная: раз в 2 недели'
    default:
      return 'Регулярная'
  }
}

/**
 * Убирает HTML-теги, декодирует сущности и нормализует пробелы/переводы
 * строк. Используется везде, где rich-text поле (например description)
 * нужно показать как обычный текст — карточки встреч, история изменений.
 */
export function stripHtml(html) {
  if (!html) return ''
  const div = document.createElement('div')
  div.innerHTML = html
  const text = div.textContent || div.innerText || ''
  return text.replace(/\s+/g, ' ').trim()
}

/**
 * Обрезает текст до maxLength символов, добавляя многоточие. Используется
 * для отображения диффов истории по крупным rich-text полям, чтобы не
 * выводить в UI полотно текста.
 */
export function truncateText(text, maxLength = 80) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength).trimEnd()}…`
}
