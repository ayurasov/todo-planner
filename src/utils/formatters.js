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
