import { onMounted, onUnmounted } from 'vue'

export function useClickOutside(elRef, callback) {
  function handler(e) {
    if (elRef.value && !elRef.value.contains(e.target)) callback(e)
  }
  onMounted(() => document.addEventListener('mousedown', handler))
  onUnmounted(() => document.removeEventListener('mousedown', handler))
}
