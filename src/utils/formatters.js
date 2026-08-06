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
