/**
 * Разбор текстового резюме встречи в кандидаты-задачи.
 *
 * v3 -- полная переработка:
 *   Режим HTML (скопировано из Word/Google Docs/Confluence):
 *     - Каждый <li> → отдельный блок-кандидат.
 *     - Внутри <li> ищем Ответственный: <Имя> -- может быть внутри строки,
 *       в HTML-атрибутах <strong> или за тегом ---.
 *     - Текст задачи = всё до метки Ответственный.
 *   Режим plain text:
 *     - Любой нумерованный маркер ("1.", "1)", ...) или символьный (• - – — *)
 *       начинает новый блок.
 *     - Строка Ответственный: До знака препинания/переноса -- имя.
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

// ---------- Константы регекспов ----------

// Маркер начала блока в plain text
const RX_NUMBERED  = /^\s*\d+[.)\u0029]\s+/
const RX_DASH      = /^\s*[-–—*]\s+/
const RX_BULLET    = /^\s*[•●▪]\s+/

/**
 * Ответственный: -- внутри строки plain text.
 * Сразу захватывает имя (до знака препинания, запятой, переноса или конца строки).
 * Группа 1 -- имя с звёздочками или без, группа 2 -- всё после ":"
 */
const RX_RESPONSIBLE_INLINE = /Ответственный[:\s*]*\*{0,2}([^,;.\n*]+)/i

// Форматы «Имя: задача» и «Имя - задача» в отдельной строке/пункте списка
const RX_NAMED = /^([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё .]{1,29}):\s+(.{3,})$/
const RX_NAMED_DASH = /^([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё .]{1,29})\s*[-–—]\s+(.{3,})$/

// ---------- Вспомогательные функции ----------

function isBlockStart(line) {
  return RX_NUMBERED.test(line) || RX_DASH.test(line) || RX_BULLET.test(line)
}

function blockPattern(line) {
  if (RX_NUMBERED.test(line)) return 'numbered'
  if (RX_DASH.test(line))    return 'dash'
  if (RX_BULLET.test(line))  return 'bullet'
  return null
}

function stripBlockMarker(line) {
  return line
    .replace(RX_NUMBERED, '')
    .replace(RX_DASH, '')
    .replace(RX_BULLET, '')
    .trim()
}

/**
 * Извлекает имя ответственного из строки/фрагмента.
 * Останавливается на первом знаке препинания, запятой, переносе или звёздочке.
 */
function extractResponsibleName(text) {
  const m = text.match(RX_RESPONSIBLE_INLINE)
  if (!m) return null
  return m[1].replace(/\*+/g, '').trim()
}

/**
 * Извлекает текст задачи -- всё ДО метки Ответственный.
 * Также убирает хвосты --- (три дефиса -- типичный Pandoc артефакт).
 */
function extractTitle(text) {
  // всё до слова Ответственный (без регистра)
  const idx = text.search(/Ответственный/i)
  const raw = idx >= 0 ? text.slice(0, idx) : text
  return raw
    .replace(/[-–—]{2,}/g, ' ')  // убираем ---
    .replace(/\*+/g, '')        // убираем markdown жирный
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Ищет в начале пункта формат назначения через имя: 
 * - «Имя: задача»
 * - «Имя - задача» / «Имя – задача» / «Имя — задача»
 *
 * Возвращает rawName и title без префикса, если совпадение найдено.
 */
function extractLeadingAssignee(text) {
  const cleaned = (text || '').trim()
  let m = cleaned.match(RX_NAMED)
  if (m) return { rawName: m[1].trim(), title: m[2].trim(), pattern: 'named' }
  m = cleaned.match(RX_NAMED_DASH)
  if (m) return { rawName: m[1].trim(), title: m[2].trim(), pattern: 'named_dash' }
  return null
}

/**
 * Сопоставляет сырое имя с известными пользователями.
 * 1. Точное совпадение
 * 2. Полное имя входит в rawName или rawName в полное имя
 * 3. По фамилии (первое слово rawName)
 * 4. По имени (второе слово rawName)
 */
function matchUser(rawName, knownUsers = []) {
  if (!rawName) return null
  const norm = rawName.trim().toLowerCase().replace(/\s+/g, ' ')
  const parts = norm.split(' ').filter(Boolean)

  // 1. Точно
  let found = knownUsers.find((u) => u.name.toLowerCase() === norm)
  if (found) return found.id

  // 2. Взаимное вхождение
  found = knownUsers.find((u) => {
    const uNorm = u.name.toLowerCase()
    return uNorm.includes(norm) || norm.includes(uNorm)
  })
  if (found) return found.id

  // 3. По фамилии
  if (parts[0] && parts[0].length > 2) {
    found = knownUsers.find((u) =>
      u.name.toLowerCase().split(' ').some((w) => w === parts[0])
    )
    if (found) return found.id
  }

  // 4. По имени (rawName вида "Фамилия Имя" -- взять второй токен)
  if (parts[1] && parts[1].length > 1) {
    found = knownUsers.find((u) =>
      u.name.toLowerCase().split(' ').some((w) => w === parts[1])
    )
    if (found) return found.id
  }

  return null
}

// ---------- HTML-парсинг: извлекаем блоки из <li> ----------

/**
 * Извлекает все <li>...</li> блоки из HTML как плайнтекстовые строки.
 * Внутри каждого <li> все HTML-теги удаляются, остаётся plain text.
 * Особо: <br> и блочные элементы внутри <li> заменяются пробелом, чтобы
 * сохранить весь текст пункта в одну строку (включая Имя из Ответственный).
 */
function extractLiBlocks(html) {
  const blocks = []
  const liRx = /<li[^>]*>([\s\S]*?)<\/li>/gi
  let m
  while ((m = liRx.exec(html)) !== null) {
    const inner = m[1]
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/<\/(p|div|h[1-6]|blockquote|span|strong|em|b|i)>/gi, ' ')
      .replace(/<[^>]+>/g, '')
      .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ').replace(/&#\d+;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
    if (inner) blocks.push(inner)
  }
  return blocks
}

/**
 * Fallback: если <li> нет -- весь HTML в плайн строками.
 */
export function htmlToPlainLines(html) {
  if (!html) return ''
  let text = html
    .replace(/<li[^>]*>/gi, '\n')
    .replace(/<\/li>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|h[1-6]|tr|blockquote)>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ')
  // Декодируем HTML-энтити
  if (typeof document !== 'undefined') {
    const ta = document.createElement('textarea')
    ta.innerHTML = text
    text = ta.value
  }
  return text
}

// ---------- Основной парсер ----------

export class MockRegexSummaryParser extends SummaryParser {
  parse(rawInput, { knownUsers = [] } = {}) {
    if (!rawInput) return []

    const isHtml = /<[a-z]/i.test(rawInput)

    if (isHtml) {
      return this._parseHtml(rawInput, knownUsers)
    }
    return this._parsePlain(rawInput, knownUsers)
  }

  // ---- HTML-режим ----
  _parseHtml(html, knownUsers) {
    const liBlocks = extractLiBlocks(html)

    if (liBlocks.length > 0) {
      // Есть <li> -- каждый блок это одна задача
      return liBlocks
        .map((block) => this._candidateFromText(block, 'list_item', knownUsers))
        .filter(Boolean)
    }

    // Fallback: HTML без <li> -- сводим к plain text
    const plain = htmlToPlainLines(html)
    return this._parsePlain(plain, knownUsers)
  }

  // ---- Plain text режим ----
  _parsePlain(text, knownUsers) {
    const lines = text.split('\n').map((l) => l.trim()).filter((l) => l.length > 0)
    const blocks = []
    let cur = null

    for (const line of lines) {
      if (isBlockStart(line)) {
        if (cur) blocks.push(cur)
        cur = { pattern: blockPattern(line), lines: [stripBlockMarker(line)] }
      } else if (cur) {
        // если строка сама содержит Ответственный -- добавляем к блоку
        cur.lines.push(line)
      } else {
        // строка до первого маркера -- проверяем форматы «Имя: задача» и «Имя - задача»
        if (RX_NAMED.test(line)) blocks.push({ pattern: 'named', lines: [line] })
        else if (RX_NAMED_DASH.test(line)) blocks.push({ pattern: 'named_dash', lines: [line] })
      }
    }
    if (cur) blocks.push(cur)

    return blocks.map((b) => {
      if (b.pattern === 'named' || b.pattern === 'named_dash') {
        const named = extractLeadingAssignee(b.lines[0])
        if (!named) return null
        return {
          rawLine: b.lines[0],
          title: named.title,
          assigneeNameRaw: named.rawName,
          assigneeGuess: matchUser(named.rawName, knownUsers),
          matchedPattern: named.pattern,
          accepted: true,
        }
      }
      // Собираем весь текст блока в одну строку и извлекаем
      const fullText = b.lines.join(' ')
      return this._candidateFromText(fullText, b.pattern, knownUsers)
    }).filter(Boolean)
  }

  /**
   * Извлекает кандидата из плайн-текстового фрагмента одного пункта.
   * Ищет Ответственный внутри строки, остальное -- текст задачи.
   */
  _candidateFromText(text, pattern, knownUsers) {
    const leading = extractLeadingAssignee(text)
    if (leading) {
      return {
        rawLine: text.slice(0, 120),
        title: leading.title,
        assigneeNameRaw: leading.rawName,
        assigneeGuess: matchUser(leading.rawName, knownUsers),
        matchedPattern: leading.pattern,
        accepted: true,
      }
    }

    const assigneeNameRaw = extractResponsibleName(text)
    const title = extractTitle(text)
    if (!title) return null
    return {
      rawLine: text.slice(0, 120),
      title,
      assigneeNameRaw,
      assigneeGuess: matchUser(assigneeNameRaw, knownUsers),
      matchedPattern: pattern,
      accepted: true,
    }
  }
}

export const meetingSummaryParser = new MockRegexSummaryParser()

export const MATCHED_PATTERN_LABEL = {
  numbered:  'Нумерованный пункт',
  dash:      'Маркер «–»',
  bullet:    'Маркер «•»',
  list_item: 'Пункт списка',
  named:      'Формат «Имя: задача»',
  named_dash: 'Формат «Имя - задача»',
}
