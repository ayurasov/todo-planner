import { ref, computed } from 'vue'

/**
 * Готовая логика drag-n-drop сортировки с «liveOrder»-предпросмотром: в отличие
 * от простого @drop-обмена двух элементов (как было раньше в ListsManagerView),
 * при каждом @dragenter над элементом перестраивается весь массив id так, чтобы
 * перетаскиваемый элемент встал на место цели, а остальные сдвинулись —
 * именно это даёт «видно, куда передвигаешь», в отличие от старого onDrop,
 * где перестройка случалась только в момент отпускания и без визуального превью.
 * Совместно с <TransitionGroup name="fade"> и .fade-move из style.css это даёт плавный «raздвиг»
 * соседних элементов.
 *
 * @param {import('vue').Ref<Array<{id: string}>>|import('vue').ComputedRef<Array<{id:string}>>} sourceItemsRef — базовые элементы (уже отсортированные по order), каждый с полем id
 * @param {(orderedIds: string[]) => Promise<void>|void} onCommit — вызывается с итоговым порядком id при завершении drag
 */
export function useDragReorder(sourceItemsRef, onCommit) {
  const draggingId = ref(null)
  const liveOrder = ref(null) // массив id во время активного перетаскивания, иначе null

  const displayItems = computed(() => {
    const base = sourceItemsRef.value
    if (!liveOrder.value) return base
    const byId = new Map(base.map((item) => [item.id, item]))
    return liveOrder.value.map((id) => byId.get(id)).filter(Boolean)
  })

  function startDrag(id) {
    draggingId.value = id
    liveOrder.value = sourceItemsRef.value.map((item) => item.id)
  }

  // Вызывается на @dragenter каждого элемента-цели — перестраивает liveOrder вживую,
  // чтобы пользователь сразу видел, как соседние элементы расстуупяются.
  function dragOver(targetId) {
    if (!draggingId.value || !liveOrder.value || draggingId.value === targetId) return
    const ids = [...liveOrder.value]
    const from = ids.indexOf(draggingId.value)
    const to = ids.indexOf(targetId)
    if (from === -1 || to === -1 || from === to) return
    ids.splice(to, 0, ids.splice(from, 1)[0])
    liveOrder.value = ids
  }

  // Зона после последнего элемента (нижний/правый край контейнера) — без неё перетаскивание
  // в конец списка было невозможным — у последнего элемента нет «следующего соседа»,
  // над которым мог бы сработать dragenter, а dragover на пустой области контейнера закрывает гап.
  function dragOverEnd() {
    if (!draggingId.value || !liveOrder.value) return
    const ids = [...liveOrder.value]
    const from = ids.indexOf(draggingId.value)
    if (from === -1 || from === ids.length - 1) return
    ids.push(ids.splice(from, 1)[0])
    liveOrder.value = ids
  }

  async function endDrag() {
    const finalOrder = liveOrder.value
    const originalIds = sourceItemsRef.value.map((item) => item.id)
    draggingId.value = null
    liveOrder.value = null
    if (!finalOrder) return
    const changed = finalOrder.length !== originalIds.length || finalOrder.some((id, i) => id !== originalIds[i])
    if (changed) await onCommit(finalOrder)
  }

  function cancelDrag() {
    draggingId.value = null
    liveOrder.value = null
  }

  return { draggingId, displayItems, startDrag, dragOver, dragOverEnd, endDrag, cancelDrag }
}
