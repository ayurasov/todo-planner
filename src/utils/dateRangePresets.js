// Готовые интервалы для быстрого фильтра по датам на странице аналитики.
// Все границы включительны: from — 00:00:00 начального дня, to — 23:59:59 сегодняшнего дня.

function toDateOnly(d) {
  return d.toISOString().slice(0, 10)
}

export const DATE_RANGE_PRESETS = [
  { value: 'week', label: 'Неделя', days: 7 },
  { value: 'two_weeks', label: '2 недели', days: 14 },
  { value: 'month', label: 'Месяц', days: 30 },
  { value: 'quarter', label: 'Квартал', days: 90 },
  { value: 'custom', label: 'Свой интервал', days: null },
]

export const DEFAULT_DATE_RANGE_PRESET = 'two_weeks'

export function presetToRange(preset) {
  const def = DATE_RANGE_PRESETS.find((p) => p.value === preset)
  if (!def || !def.days) return null
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - (def.days - 1))
  return { from: toDateOnly(from), to: toDateOnly(to) }
}
