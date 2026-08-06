<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { useTasksStore } from '../../stores/tasksStore'
import { useUsersStore } from '../../stores/usersStore'

const tasksStore = useTasksStore()
const usersStore = useUsersStore()
const chartEl = ref(null)
let chart = null

const chartData = computed(() => {
  const names = []
  const counts = []
  for (const user of usersStore.users) {
    const tasks = tasksStore.tasksByAssignee[user.id] || []
    const open = tasks.filter((t) => t.status !== 'done' && t.status !== 'cancelled')
    if (open.length === 0) continue
    names.push(user.name)
    counts.push(open.length)
  }
  return { names, counts }
})

function render() {
  if (!chart || !chartEl.value) return
  chart.setOption({
    grid: { left: 90, right: 20, top: 20, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: chartData.value.names },
    series: [{ type: 'bar', data: chartData.value.counts, itemStyle: { color: '#4f7cff', borderRadius: [0, 4, 4, 0] }, barWidth: 18 }],
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
    <h4>Нагрузка по исполнителям (активные задачи)</h4>
    <div ref="chartEl" class="chart-el" />
  </div>
</template>

<style scoped>
.chart-card { padding: 12px 16px; margin-bottom: 14px; }
.chart-card h4 { margin: 0 0 8px; font-size: 13px; color: var(--color-text-muted); }
.chart-el { width: 100%; height: 200px; }
</style>
