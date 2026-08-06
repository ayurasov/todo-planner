<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import * as echarts from 'echarts'
import { useHistoryStore } from '../../stores/historyStore'

const historyStore = useHistoryStore()
const chartEl = ref(null)
let chart = null

const chartData = computed(() => {
  const buckets = {}
  for (const entry of historyStore.globalLog) {
    const day = entry.timestamp.slice(0, 10)
    buckets[day] = (buckets[day] || 0) + 1
  }
  const days = Object.keys(buckets).sort()
  return { days, counts: days.map((d) => buckets[d]) }
})

function render() {
  if (!chart) return
  chart.setOption({
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: chartData.value.days },
    yAxis: { type: 'value' },
    series: [{ type: 'line', data: chartData.value.counts, smooth: true, itemStyle: { color: '#4f7cff' }, areaStyle: { color: 'rgba(79,124,255,0.12)' } }],
    tooltip: { trigger: 'axis' },
  })
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  render()
  window.addEventListener('resize', () => chart?.resize())
})

watch(chartData, render)
</script>

<template>
  <div class="card chart-card">
    <h4>Активность по дням</h4>
    <div ref="chartEl" class="chart-el" />
  </div>
</template>

<style scoped>
.chart-card { padding: 12px 16px; margin-bottom: 14px; }
.chart-card h4 { margin: 0 0 8px; font-size: 13px; color: var(--color-text-muted); }
.chart-el { width: 100%; height: 200px; }
</style>
