/**
 * Разбор текстового резюме встречи в кандидаты-задачи.
 *
 * v2 -- улучшенная логика:
 *   1. Перед разбором HTML-текст преобразуется в плоский текст сохраняя
 *      структуру списков (<ol>/<ul>/<li>): каждый <li> становится
 *      отдельной строкой вывода.
 *   2. Текст группируется в блоки: новый блок начинается номером / маркером,
 *      все последующие строки до следующего маркера считаются его частью.
 *   3. Внутри блока ищем метку "Ответственный: Имя" -- если найдено,
 *      сопоставляем имя с известными пользователями.
 *   4. Основной текст задачи -- первая непустая строка блока (без меток
 *      "Ответственный" / "Дата" / "Срок").
 */

/**
 * @typedef {Object} ParsedTaskCandidate
 * @property {string} rawLine
 * @property {string} title
 * @property {string|null} assigneeGuess
 * @property {string|null} assigneeNameRaw
 * @property {string} matchedPattern
 * @property {boolean} accepted
 */

export class SummaryParser {
  parse(_text, _options) {
    throw new Error('Not implemented')
  }
}

// Строка начинает новый пункт-блок
const BLOCK_START_DASH     = /^\s*[-–—]\s+/
const BLOCK_START_BULLET   = /^\s*[•●▪]\s+/
const BLOCK_START_NUMBERED = /^\s*\d+[.)\u0029]\s+/

// Метка ответственного внутри блока
const RESPONSIBLE_PATTERN  = /^Ответственный[: ]*\*{0,2}\s*(.+?)\*{0,2}\s*$/i

// Формат "Имя: задача" в отдельной строке
const NAMED_PATTERN        = /^\s*([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё .]{1,29}):\s+(.+)$/

function isBlockStart(line) {
  return BLOCK_START_DASH.test(line) || BLOCK_START_BULLET.test(line) || BLOCK_START_NUMBERED.test(line)
}

function blockPattern(line) {
  if (BLOCK_START_DASH.test(line)) return 'dash'
  if (BLOCK_START_BULLET.test(line)) return 'bullet'
  if (BLOCK_START_NUMBERED.test(line)) return 'numbered'
  return null
}

function stripBlockMarker(line) {
  return line
    .replace(BLOCK_START_NUMBERED, '')
    .replace(BLOCK_START_DASH, '')
    .replace(BLOCK_START_BULLET, '')
    .trim()
}

/**
 * Удаляет HTML-теги, сохраняя структуру списков.
 * Каждый <li> становится отдельной строкой, чтобы не сливаться.
 * <br> и блочные элементы дают перенос строки.
 */
export function htmlToPlainLines(html) {
  if (!html) return ''
  // <li> -- новая строка
  let text = html
    .replace(/<li[^>]*>/gi, '\n')
    .replace(/<\/li>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|h[1-6]|tr|blockquote)>/gi, '\n')
    .replace(/<[^>]+>/g, '')

  // Декодируем HTML-энтити
  const ta = document.createElement('textarea')
  ta.innerHTML = text
  return ta.value
}

/**
 * Сопоставляет сырое имя с известными пользователями.
 * Сначала пробует полное совпадение, затем вхождение по фамилии или имени.
 */
function matchUser(rawName, knownUsers = []) {
  if (!rawName) return null
  const norm = rawName.trim().toLowerCase().replace(/\s+/g, ' ')
  // 1. Точное совпадение
  let found = knownUsers.find((u) => u.name.toLowerCase() === norm)
  if (found) return found.id
  // 2. Полное имя входит в rawName ("Юрасов Александр" → matches "Юрасов Александр")
  found = knownUsers.find((u) => norm.includes(u.name.toLowerCase()))
  if (found) return found.id
  // 3. rawName входит в полное имя пользователя (только если длиннее 1 слова)
  const parts = norm.split(' ').filter(Boolean)
  if (parts.length > 1) {
    found = knownUsers.find((u) => u.name.toLowerCase().includes(norm))
    if (found) return found.id
  }
  // 4. Совпадение по фамилии (первое слово rawName)
  const firstToken = parts[0]
  if (firstToken && firstToken.length > 2) {
    found = knownUsers.find((u) => u.name.toLowerCase().split(' ').some((w) => w === firstToken))
    if (found) return found.id
  }
  return null
}

export class MockRegexSummaryParser extends SummaryParser {
  parse(rawInput, { knownUsers = [] } = {}) {
    if (!rawInput) return []

    // Если на входе HTML (есть теги) -- преобразуем с сохранением структуры списков
    const text = /<[a-z]/i.test(rawInput) ? htmlToPlainLines(rawInput) : rawInput

    const lines = text.split('\n').map((l) => l.trim()).filter((l) => l.length > 0)
    const candidates = []

    // --- Группировка строк в блоки ---
    // Блок = первая строка (start-marker) + все следующие до следующего start-marker'а
    const blocks = [] // [{ pattern, lines: string[] }]
    let currentBlock = null

    for (const line of lines) {
      if (isBlockStart(line)) {
        if (currentBlock) blocks.push(currentBlock)
        currentBlock = { pattern: blockPattern(line), lines: [line] }
      } else if (currentBlock) {
        // продолжение текущего блока
        currentBlock.lines.push(line)
      } else {
        // строка до первого маркера -- проверяем на формат "Имя: задача"
        const namedMatch = line.match(NAMED_PATTERN)
        if (namedMatch) {
          blocks.push({ pattern: 'named', lines: [line] })
        }
        // остальные строки без маркера -- пропускаем
      }
    }
    if (currentBlock) blocks.push(currentBlock)

    // --- Извлекаем задачу из каждого блока ---
    for (const block of blocks) {
      if (block.pattern === 'named') {
        const namedMatch = block.lines[0].match(NAMED_PATTERN)
        if (!namedMatch) continue
        const rawName = namedMatch[1].trim()
        const body = namedMatch[2].trim()
        candidates.push({
          rawLine: block.lines[0],
          title: body,
          assigneeNameRaw: rawName,
          assigneeGuess: matchUser(rawName, knownUsers),
          matchedPattern: 'named',
          accepted: true,
        })
        continue
      }

      // Для dash/bullet/numbered:
      // Основной текст -- первая строка без маркера +
      // последующие строки блока, которые НЕ являются метками (Ответственный/Дата/Срок)
      // Ищем метку "Ответственный:"
      let assigneeNameRaw = null
      let assigneeGuess = null

      const titleParts = []
      for (let i = 0; i < block.lines.length; i++) {
        const ln = i === 0 ? stripBlockMarker(block.lines[i]) : block.lines[i]
        const respMatch = ln.match(RESPONSIBLE_PATTERN)
        if (respMatch) {
          // Строка -- метка ответственного
          assigneeNameRaw = respMatch[1].trim()
          assigneeGuess = matchUser(assigneeNameRaw, knownUsers)
          // не добавляем в title
        } else if (/^(Дата|Deadline|Срок)[:\s]/i.test(ln)) {
          // метка даты/срока -- тоже не в title
        } else if (ln) {
          titleParts.push(ln)
        }
      }

      const title = titleParts.join(' ').trim()
      if (!title) continue

      candidates.push({
        rawLine: block.lines[0],
        title,
        assigneeNameRaw,
        assigneeGuess,
        matchedPattern: block.pattern,
        accepted: true,
      })
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
