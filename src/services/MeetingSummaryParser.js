/**
 * Разбор текстового резюме встречи в кандидаты-задачи (раздел 3.7 ТЗ
 * TaskBubbler). Реализовано как абстракция SummaryParser с mock-реализацией
 * на regex-эвристиках (без реального NLP) — контракт спроектирован так,
 * чтобы в v2 его можно было заменить на LLM-based парсер без изменения
 * вызывающего кода (форма подтверждения работает с одинаковой формой
 * результата — массивом ParsedTaskCandidate).
 *
 * Использование:
 *   const parser = new MockRegexSummaryParser()
 *   const candidates = parser.parse(summaryText, { knownUsers })
 *   // candidates: ParsedTaskCandidate[]
 */

/**
 * @typedef {Object} ParsedTaskCandidate
 * @property {string} rawLine        - исходная строка резюме
 * @property {string} title          - извлечённый текст задачи (без маркера/имени)
 * @property {string|null} assigneeGuess - id пользователя, если имя из строки
 *                                          однозначно сопоставилось с известным
 *                                          пользователем, иначе null
 * @property {string|null} assigneeNameRaw - сырое имя/инициал из строки,
 *                                            если паттерн "[Имя]: ..." сработал
 * @property {string} matchedPattern - какой эвристический паттерн сработал
 *                                      ('dash' | 'bullet' | 'numbered' | 'named')
 * @property {boolean} accepted      - выбрана ли строка пользователем (для UI формы,
 *                                      по умолчанию true — пользователь может снять галочку)
 */

export class SummaryParser {
  /**
   * @param {string} _text
   * @param {{ knownUsers?: Array<{id: string, name: string}> }} _options
   * @returns {ParsedTaskCandidate[]}
   */
  parse(_text, _options) {
    throw new Error('Not implemented')
  }
}

const DASH_PATTERN = /^\s*[-–—]\s+(.+)$/
const BULLET_PATTERN = /^\s*[•●▪]\s+(.+)$/
const NUMBERED_PATTERN = /^\s*\d+[.)]\s+(.+)$/
// "[Имя]: сделать..." — имя/инициал до двоеточия, короче ~30 символов (иначе
// это скорее обычное предложение с двоеточием внутри, а не имя).
const NAMED_PATTERN = /^\s*([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё .]{1,29}):\s+(.+)$/

/**
 * Пытается сопоставить сырое имя из строки с известным пользователем.
 * Сопоставление по вхождению (без учёта регистра) части имени — сознательно
 * простое правило, без fuzzy-matching, чтобы поведение было прозрачным и
 * предсказуемым для пользователя (не "магия").
 */
function matchUser(rawName, knownUsers = []) {
  if (!rawName) return null
  const normalized = rawName.trim().toLowerCase()
  const found = knownUsers.find((u) => {
    const userNameLower = u.name.toLowerCase()
    return userNameLower === normalized || userNameLower.includes(normalized) || normalized.includes(userNameLower.split(' ')[0])
  })
  return found ? found.id : null
}

export class MockRegexSummaryParser extends SummaryParser {
  parse(text, { knownUsers = [] } = {}) {
    if (!text) return []
    const lines = text.split('\n')
    const candidates = []

    for (const rawLine of lines) {
      const line = rawLine.trim()
      if (!line) continue

      let match
      if ((match = line.match(NAMED_PATTERN))) {
        const rawName = match[1].trim()
        const body = match[2].trim()
        candidates.push({
          rawLine,
          title: body,
          assigneeNameRaw: rawName,
          assigneeGuess: matchUser(rawName, knownUsers),
          matchedPattern: 'named',
          accepted: true,
        })
        continue
      }
      if ((match = line.match(DASH_PATTERN))) {
        candidates.push({
          rawLine, title: match[1].trim(), assigneeNameRaw: null, assigneeGuess: null,
          matchedPattern: 'dash', accepted: true,
        })
        continue
      }
      if ((match = line.match(BULLET_PATTERN))) {
        candidates.push({
          rawLine, title: match[1].trim(), assigneeNameRaw: null, assigneeGuess: null,
          matchedPattern: 'bullet', accepted: true,
        })
        continue
      }
      if ((match = line.match(NUMBERED_PATTERN))) {
        candidates.push({
          rawLine, title: match[1].trim(), assigneeNameRaw: null, assigneeGuess: null,
          matchedPattern: 'numbered', accepted: true,
        })
        continue
      }
      // Строка не соответствует ни одной эвристике — не кандидат в задачу.
    }

    return candidates
  }
}

export const meetingSummaryParser = new MockRegexSummaryParser()

export const MATCHED_PATTERN_LABEL = {
  dash: 'Маркер "–"',
  bullet: 'Маркер "•"',
  numbered: 'Нумерованный пункт',
  named: 'Формат "Имя: задача"',
}
