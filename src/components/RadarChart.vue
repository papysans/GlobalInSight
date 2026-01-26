<template>
  <div class="radar-chart-container">
    <canvas ref="chartCanvas"></canvas>
    
    <!-- 图例 -->
    <div class="legend mt-4 flex flex-wrap gap-4 justify-center">
      <div v-for="(platform, index) in data.labels" :key="platform" class="legend-item flex items-center gap-2">
        <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: getColor(index) }"></div>
        <span class="text-xs text-slate-600">{{ platform }}</span>
        <span class="text-xs font-bold text-slate-800">{{ data.datasets[0].data[index] }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Chart } from 'chart.js/auto'

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  theme: {
    type: String,
    default: 'white'
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const getColor = (index) => {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  return colors[index % colors.length]
}

const initChart = () => {
  if (!chartCanvas.value) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')
  
  chartInstance = new Chart(ctx, {
    type: 'radar',
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            callback: (value) => value
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              return `${context.label}: ${context.parsed.r.toFixed(1)}`
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
