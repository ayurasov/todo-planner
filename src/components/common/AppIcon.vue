<script setup>
/**
 * Единый набор иконок для всего приложения — тонкие линии (stroke-based),
 * одинаковая толщина и скругление углов, как в Feather/Lucide.
 * Гораздо более деликатно и согласованно, чем разностильные emoji.
 * Использование: <AppIcon name="trash" />
 */
const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 },
})

const PATHS = {
  grouping: 'M4 6h7M4 12h16M4 18h11',
  bubbles: 'M8.5 13.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9ZM16 20.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z',
  sort: 'M6 4v16m0 0-3-3m3 3 3-3M18 20V4m0 0 3 3m-3-3-3 3',
  layers: 'm12 3 9 5-9 5-9-5 9-5ZM3 13l9 5 9-5M3 17l9 5 9-5',
  density: 'M4 7h16M4 12h16M4 17h16',
  more: 'M5 12h.01M12 12h.01M19 12h.01',
  users: 'M8 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM2.5 20c.6-3.2 3-5 5.5-5s4.9 1.8 5.5 5M16.5 11a3 3 0 1 0 0-6M17 14.2c2 .4 3.5 1.9 4 4.8',
  calendar: 'M7 3v3M17 3v3M4 9h16M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z',
  trash: 'M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m3 0-.8 12.1a1.6 1.6 0 0 1-1.6 1.5H7.4a1.6 1.6 0 0 1-1.6-1.5L5 7m3.5 4v5m4-5v5',
  edit: 'M4 20h4l10-10a2 2 0 0 0-4-4L4 16v4Z',
  plus: 'M12 5v14M5 12h14',
  list: 'M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01',
  pin: 'M9.5 3h5l.6 5.4L18 11v2h-6v6l-1 2-1-2v-6H4v-2l2.9-2.6L7.5 3Z',
  unpin: 'M9.5 3h5l.6 5.4L18 11v2h-6v6l-1 2-1-2v-6H4v-2l2.9-2.6L7.5 3Z',
  copy: 'M8 8V5a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1h-3M6 8h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z',
  check: 'M4 12.5 9 17.5 20 6',
  undo: 'M4 10h9a5 5 0 0 1 0 10h-2M4 10l4-4M4 10l4 4',
  standaloneOn: 'M4 5h16v14H4V5ZM9 5v14',
  standaloneOff: 'M4 5h16v14H4V5Z',
  close: 'M6 6l12 12M18 6 6 18',
  detail: 'M4 6h16M4 12h10M4 18h16',
  chevronDown: 'm6 9 6 6 6-6',
  chevronUp: 'm18 15-6-6-6 6',
}
</script>

<template>
  <svg
    :width="size" :height="size" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
    class="app-icon" aria-hidden="true"
  >
    <path :d="PATHS[name] || ''" />
  </svg>
</template>

<style scoped>
.app-icon { display: block; flex-shrink: 0; }
</style>
