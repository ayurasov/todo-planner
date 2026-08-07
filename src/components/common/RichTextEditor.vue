<script setup>
/**
 * Минимальный rich-text редактор на contenteditable, без внешних зависимостей.
 * Поддерживает: жирный, курсив, маркированный/нумерованный списки, ссылки.
 * Value — санитайзированный HTML-строинг (белый список тегов разрешён).
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

const ALLOWED_TAGS = new Set(['B', 'STRONG', 'I', 'EM', 'U', 'UL', 'OL', 'LI', 'BR', 'DIV', 'P', 'A', 'SPAN'])

function sanitize(html) {
  const tmp = document.createElement('div')
  tmp.innerHTML = html || ''
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
    />
  </div>
</template>

<style scoped>
.rich-text { border: 1px solid var(--color-border); border-radius: 10px; overflow: hidden; }
.rich-toolbar { display: flex; align-items: center; gap: 2px; padding: 6px 8px; border-bottom: 1px solid var(--color-border); background: #fafbfe; }
.rich-toolbar button {
  border: none; background: none; width: 26px; height: 26px; border-radius: 6px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; color: var(--color-text-muted); font-size: 12.5px;
}
.rich-toolbar button:hover { background: #eef1f7; color: var(--color-text); }
.sep { width: 1px; height: 16px; background: var(--color-border); margin: 0 4px; }
.rich-content {
  min-height: 90px; padding: 10px; font-size: 13.5px; outline: none; line-height: 1.55;
}
.rich-content.readonly { cursor: default; }
.rich-content:empty::before { content: attr(data-placeholder); color: var(--color-text-muted); }
.rich-content :deep(ul), .rich-content :deep(ol) { margin: 0 0 0 20px; padding: 0; }
.rich-content :deep(a) { color: var(--color-primary); text-decoration: underline; }
</style>
