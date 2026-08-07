import { onMounted, onUnmounted } from 'vue'

// ignoreRef — доп. элемент (например, кнопка-триггер), клик по которому не
// должен считаться "снаружи": иначе mousedown на самой кнопке сначала
// закрывает попап через этот хендлер, а затем её же click-хендлер открывает
// его заново — попап дёргается/мигает при открытии через один и тот же
// триггер (встречается в выпадающих меню, спозиционированных через Teleport).
export function useClickOutside(elRef, callback, ignoreRef = null) {
  function handler(e) {
    if (elRef.value && !elRef.value.contains(e.target)) {
      if (ignoreRef?.value && ignoreRef.value.contains(e.target)) return
      callback(e)
    }
  }
  onMounted(() => document.addEventListener('mousedown', handler))
  onUnmounted(() => document.removeEventListener('mousedown', handler))
}
