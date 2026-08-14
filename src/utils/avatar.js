/**
 * Инициалы пользователя из полного имени (до двух букв: имя + фамилия).
 * "Иван Петров" -> "ИП", "Мария" -> "М". Используется вместо одной буквы,
 * чтобы разных людей было легче отличить друг от друга в компактных
 * аватарах (жалоба: "по одной букве не понятно, кто исполнитель").
 */
export function getInitials(name) {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase()
  return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase()
}

// Небольшая палитра с достаточным контрастом текста (#fff) для стабильного
// хэш-подбора цвета аватара по имени — одинаковое имя всегда даёт один цвет,
// разные имена, как правило, получают визуально разные цвета.
const AVATAR_PALETTE = [
  '#4f7cff', '#e8a13a', '#e5484d', '#1e9e4d', '#7c5cd6',
  '#0f9fae', '#d6499a', '#8a6d3b', '#5b6b8c', '#c2410c',
]

export function getAvatarColor(nameOrId) {
  const s = String(nameOrId || '')
  let hash = 0
  for (let i = 0; i < s.length; i++) {
    hash = (hash * 31 + s.charCodeAt(i)) & 0xffffffff
  }
  const idx = Math.abs(hash) % AVATAR_PALETTE.length
  return AVATAR_PALETTE[idx]
}

/**
 * Короткое отображаемое имя для меток рядом с аватаром (имя + первая буква
 * фамилии с точкой), например "Иван П.". Используется там, где рядом с
 * аватаром есть место показать не только инициалы, но и понятное имя.
 */
export function getShortName(name) {
  if (!name) return ''
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0]
  return `${parts[0]} ${parts[1].charAt(0).toUpperCase()}.`
}

/**
 * Возвращает URL аватара с cache-busting параметром, который меняется раз в
 * минуту. Это гарантирует, что после перебилда/замены файла браузер не будет
 * показывать устаревшую версию из кэша.
 * Если url пустой — возвращает пустую строку.
 */
export function avatarSrc(url) {
  if (!url) return ''
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}_v=${Math.floor(Date.now() / 60000)}`
}
