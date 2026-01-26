<template>
  <div class="trend-chart-container">
    <canvas ref="chartCanvas"></canvas>
    
    <!-- 阶段标签 -->
    <div class="stage-labels mt-6 grid grid-cols-3 gap-4 text-center">
      <div class="stage-label">
        <div class="font-bold text-green-600 text-sm">爆发期</div>
        <div class="text-slate-500 text-xs">快速上升</div>
      </div>
      <div class="stage-label">
        <div class="font-bold text-blue-600 text-sm">扩散期</div>
        <div class="text-slate-500 text-xs">持续增长</div>
      </div>
      <div class="stage-label">
        <div class="font-bold text-orange-600 text-sm">回落期</div>
        <div class="text-slate-500 text-xs">逐渐降温</div>
      </div>
    </div>

    <!-- 当前状态 -->
    <div class="current-status mt-4 p-4 bg-slate-50 rounded-lg flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full animate-pulse" :class="stageColor"></div>
        <span class="text-sm text-slate-700">当前阶段：<strong>{{ data.stage }}</strong></span>
      </div>
      <div class="text-sm text-slate-700">
        增速：<strong :class="growthColor">{{ formatGrowth(data.growth) }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { Chart } from 'chart.js/auto'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({
      stage: '扩散期',
      growth: 50,
      curve: [40, 55, 70, 80, 90, 95, 92]
    })
  },
  theme: {
    type: String,
    default: 'white'
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const stageColor = computed(() => {
  const stage = props.data.stage
  if (stage === '爆发期') return 'bg-green-500'
  if (stage === '扩散期') return 'bg-blue-500'
  if (stage === '回落期') return 'bg-orange-500'
  return 'bg-slate-500'
})

const growthColor = computed(() => {
  const growth = props.data.growth
  if (growth > 100) return 'text-green-600'
  if (growth > 0) return 'text-blue-600'
  return 'text-red-600'
})

const formatGrowth = (growth) => {
  if (growth > 100) return `+${growth}%`
  if (growth > 0) return `+${growth}%`
  return `${growth}%`
}

const initChart = () => {
  if (!chartCanvas.value) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'],
      datasets: [{
        label: '热度指数',
        data: props.data.curve,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (value) => value + '%',
            color: '#64748b',
            font: {
              size: 11
            }
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#64748b',
            font: {
              size: 11
            }
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: '#3b82f6',
          borderWidth: 1,
          callbacks: {
            label: (context) => {
              return `热度: ${context.parsed.y}%`
            }
          }
        }
      }
    }
  })
}

onMounted(() => {
  initChart()
})

watch(() => props.data, () => {
  initChart()
}, { deep: true })

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.trend-chart-container {
  width: 100%;
}
</style>
