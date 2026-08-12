<script setup>
/**
 * Рич-текст редактор на contenteditable, без внешних зависимостей.
 * Поддерживает: жирный, курсив, заголовки, маркированный/нумерованный списки, ссылки, таблицы.
 * Value — санитайзайзированный HTML-строинг (белый список тегов разрешён).
 * Вставка (paste) обрабатывается отдельно: браузер сам нормализует HTML,
 * скопированный из Word/Google Docs (заголовки становятся H1-H4, списки — UL/OL/LI,
 * таблицы — TABLE/TR/TD), поэтому достаточно не резать эти теги в sanitize и вставлять именно HTML,
 * а не голый текст (execCommand('insertHTML') после ручной санитизации буфера).
 * Заметка по таблицам: все атрибуты ячейки/строк/таблицы (включая inline-стили Word)
 * срезаются, визуальный вид таблицы задаётся своим CSS (сетка, паддинги), а не тем, что
 * пришло из буфера — чтобы вставленные из Word таблицы выглядели одинаково во всей системе.
 * Использование: <RichTextEditor v-model="html" :editable="true" placeholder="..." />
 */
import { ref, watch, onMounted } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  editable: { type: Boolean, default: true },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const ALLOWED_TAGS = new Set([
  'B', 'STRONG', 'I', 'EM', 'U', 'UL', 'OL', 'LI', 'BR', 'DIV', 'P', 'A', 'SPAN',
  'H1', 'H2', 'H3', 'H4',
  'TABLE', 'THEAD', 'TBODY', 'TR', 'TD', 'TH',
])

// В буфере Word маркированные/нумерованные списки часто приходят не как
// настоящие <ul>/<ol>, а как отдельные абзацы <p> с ручным тире/буллетом в
// тексте ("-", "•") или числом с точкой ("1.", "2)"). Чтобы такие абзацы при
// вставке становились настоящим списком, а не теряли отступ/нумерацию, при
// санитизации прогоняется каждый блок-контейнер (включая ячейки таблиц) и
// соседние однотипные абзацы сворациваются в один <ul>/<ol>.
const BULLET_RE = /^\s*[-\u2022\u2013\u2043\*]\s+/
const NUMBERED_RE = /^\s*(\d{1,3})[.)]\s+/

function convertFakeListParagraphs(root) {
  const blocks = [...root.querySelectorAll('p, div')].filter((el) => (
    !el.closest('ul, ol') && el.children.length === 0 || [...el.childNodes].every((n) => n.nodeType !== 1 || ['B', 'STRONG', 'I', 'EM', 'U', 'SPAN', 'A', 'BR'].includes(n.tagName))
  ))
  let i = 0
  while (i < blocks.length) {
    const el = blocks[i]
    if (!el.isConnected || el.closest('ul, ol')) { i++; continue }
    const text = el.textContent || ''
    const isBullet = BULLET_RE.test(text)
    const numberedMatch = text.match(NUMBERED_RE)
    if (!isBullet && !numberedMatch) { i++; continue }
    const group = [el]
    let j = i + 1
    while (j < blocks.length) {
      const next = blocks[j]
      if (!next.isConnected) { j++; continue }
      const nextText = next.textContent || ''
      const nextIsSameType = isBullet ? BULLET_RE.test(nextText) : NUMBERED_RE.test(nextText)
      if (!nextIsSameType) break
      group.push(next)
      j++
    }
    const listTag = isBullet ? 'ul' : 'ol'
    const list = document.createElement(listTag)
    group.forEach((groupEl) => {
      const li = document.createElement('li')
      const stripRe = isBullet ? BULLET_RE : NUMBERED_RE
      li.innerHTML = groupEl.innerHTML.replace(stripRe, '')
      list.appendChild(li)
    })
    group[0].replaceWith(list)
    group.slice(1).forEach((g) => g.remove())
    i = j
  }
}

function sanitize(html) {
  const tmp = document.createElement('div')
  tmp.innerHTML = html || ''
  convertFakeListParagraphs(tmp)
  const walk = (node) => {
    ;[...node.childNodes].forEach((child) => {
      if (child.nodeType === 1) {
        if (!ALLOWED_TAGS.has(child.tagName)) {
          const text = document.createTextNode(child.textContent)
          child.replaceWith(text)
          return
        }
        ;[...child.attributes].forEach((attr) => {
          if (child.tagName === 'A' && attr.name === 'href') {
            if (!/^https?:\/\//i.test(attr.value)) child.removeAttribute('href')
          } else {
            child.removeAttribute(attr.name)
          }
        })
        walk(child)
      } else if (child.nodeType !== 3) {
        child.remove()
      }
    })
  }
  walk(tmp)
  return tmp.innerHTML
}

const editorEl = ref(null)

function handleInput() {
  emit('update:modelValue', sanitize(editorEl.value.innerHTML))
}

function exec(command, value = null) {
  editorEl.value.focus()
  document.execCommand(command, false, value)
  handleInput()
}

function insertLink() {
  const url = window.prompt('Вставить ссылку (https://...)')
  if (!url) return
  if (!/^https?:\/\//i.test(url)) return
  exec('createLink', url)
}

// Вставка из Word/Google Docs приходит в буфере как text/html с заголовками,
// списками, таблицами, но также кучей мусорных inline-стилей и вложенных span/font.
// Перехватываем paste, санитизируем HTML-версию буфера сами (а не отдаём это
// браузерному execCommand('paste') по умолчанию, который сохраняет инлайн-стили)
// и вставляем именно санитизированный HTML, чтобы сохранить структуру
// (заголовки H1-H4, списки UL/OL/LI, таблицы), но не тащить оформление документа.
function handlePaste(e) {
  const html = e.clipboardData?.getData('text/html')
  const text = e.clipboardData?.getData('text/plain')
  if (!html && !text) return
  e.preventDefault()
  const clean = html ? sanitize(html) : ''
  if (clean.trim()) {
    document.execCommand('insertHTML', false, clean)
  } else if (text) {
    document.execCommand('insertText', false, text)
  }
  handleInput()
}

onMounted(() => {
  if (editorEl.value) editorEl.value.innerHTML = props.modelValue || ''
})

watch(() => props.modelValue, (val) => {
  if (editorEl.value && val !== editorEl.value.innerHTML) {
    editorEl.value.innerHTML = val || ''
  }
})
</script>

<template>
  <div class="rich-text">
    <div v-if="editable" class="rich-toolbar">
      <button type="button" title="Заголовок 1" @mousedown.prevent="exec('formatBlock', 'H1')">H1</button>
      <button type="button" title="Заголовок 2" @mousedown.prevent="exec('formatBlock', 'H2')">H2</button>
      <button type="button" title="Обычный текст" @mousedown.prevent="exec('formatBlock', 'P')">P</button>
      <span class="sep" />
      <button type="button" title="Жирный" @mousedown.prevent="exec('bold')"><strong>B</strong></button>
      <button type="button" title="Курсив" @mousedown.prevent="exec('italic')"><em>I</em></button>
      <button type="button" title="Подчёркивание" @mousedown.prevent="exec('underline')"><u>U</u></button>
      <span class="sep" />
      <button type="button" title="Маркированный список" @mousedown.prevent="exec('insertUnorderedList')"><AppIcon name="list" :size="13" /></button>
      <button type="button" title="Нумерованный список" @mousedown.prevent="exec('insertOrderedList')"><AppIcon name="checklist" :size="13" /></button>
      <span class="sep" />
      <button type="button" title="Ссылка" @mousedown.prevent="insertLink"><AppIcon name="link" :size="13" /></button>
    </div>
    <div
      ref="editorEl"
      class="rich-content"
      :class="{ readonly: !editable }"
      :contenteditable="editable"
      :data-placeholder="placeholder"
      @input="handleInput"
      @blur="handleInput"
      @paste="handlePaste"
    />
  </div>
</template>

<style scoped>
.rich-text { border: 1px solid var(--color-border); border-radius: 10px; overflow: hidden; }
.rich-toolbar { display: flex; align-items: center; gap: 2px; padding: 6px 8px; border-bottom: 1px solid var(--color-border); background: #fafbfe; flex-wrap: wrap; }
.rich-toolbar button {
  border: none; background: none; min-width: 26px; height: 26px; padding: 0 6px; border-radius: 6px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; color: var(--color-text-muted); font-size: 11.5px; font-weight: 600;
}
.rich-toolbar button:hover { background: #eef1f7; color: var(--color-text); }
.sep { width: 1px; height: 16px; background: var(--color-border); margin: 0 4px; }
.rich-content {
  min-height: 90px; padding: 10px; font-size: 13.5px; outline: none; line-height: 1.55; overflow-x: auto;
}
.rich-content.readonly { cursor: default; }
.rich-content:empty::before { content: attr(data-placeholder); color: var(--color-text-muted); }
.rich-content :deep(ul), .rich-content :deep(ol) { margin: 0 0 8px 20px; padding: 0; }
.rich-content :deep(li) { margin: 2px 0; }
.rich-content :deep(h1) { font-size: 19px; font-weight: 700; margin: 10px 0 6px; }
.rich-content :deep(h2) { font-size: 16px; font-weight: 700; margin: 8px 0 5px; }
.rich-content :deep(h3) { font-size: 14px; font-weight: 700; margin: 6px 0 4px; }
.rich-content :deep(a) { color: var(--color-primary); text-decoration: underline; }
.rich-content :deep(table) {
  border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px;
}
.rich-content :deep(td), .rich-content :deep(th) {
  border: 1px solid var(--color-border); padding: 6px 9px; vertical-align: top; text-align: left;
}
.rich-content :deep(th) { background: #fafbfe; font-weight: 700; }
</style>
