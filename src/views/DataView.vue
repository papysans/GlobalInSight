<template>
  <div class="view-section animate-fade-in py-12 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-slate-900 mb-2">多维数据洞察</h2>
        <p class="text-slate-500">生成式数据可视化卡片 (Generative Data Cards)</p>
      </div>

      <div class="relative grid lg:grid-cols-12 gap-8 items-start">
        <div
          v-if="!dataUnlocked"
          class="absolute inset-0 z-20 rounded-3xl locked-overlay flex flex-col items-center justify-center text-center p-8"
        >
          <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 shadow-sm">
            <Lock class="w-8 h-8 text-slate-400" />
          </div>
          <h3 class="text-xl font-bold text-slate-700 mb-2">数据尚未生成</h3>
          <p class="text-slate-500 max-w-md">请先在「舆情推演」页面启动分析，系统将基于辩论结果自动生成"中外舆论对比"等数据。</p>
          <button
            @click="$emit('switch-tab', 'home')"
            class="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            前往推演
          </button>
        </div>

        <!-- Left: Control Panel -->
        <div
          :class="[
            'lg:col-span-4 space-y-6 transition-all duration-500',
            !dataUnlocked ? 'filter blur-sm' : ''
          ]"
        >
          <div class="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <LayoutGrid class="w-5 h-5 text-blue-600" /> 图表数据选择
            </h3>
            <div class="space-y-3">
              <button
                v-for="option in dataOptions"
                :key="option.type"
                @click="selectDataType(option.type)"
                :class="[
                  'data-btn w-full text-left px-4 py-3 rounded-xl bg-white text-slate-600 border border-slate-200 font-medium hover:bg-slate-50 transition-colors flex justify-between items-center group shadow-sm',
                  selectedDataType === option.type ? 'btn-selected' : ''
                ]"
              >
                <div class="flex items-center gap-3">
                  <div :class="['w-8 h-8 rounded-full flex items-center justify-center', option.color]">
                    <component :is="option.icon" class="w-4 h-4" />
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-800">{{ option.title }}</div>
                    <div class="text-[10px] text-slate-400">{{ option.subtitle }}</div>
                  </div>
                </div>
                <ChevronRight class="w-4 h-4 opacity-50 group-hover:opacity-100" />
              </button>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Edit3 class="w-5 h-5 text-slate-600" /> 卡片文本编辑
            </h3>
            <div class="space-y-3">
              <div>
                <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 block">
                  主标题 (Main Title)
                </label>
                <input
                  v-model="posterTitle"
                  type="text"
                  @input="updateChart"
                  class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:border-blue-500 outline-none font-bold text-slate-700"
                />
              </div>
              <div>
                <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 block">
                  副标题 (Subtitle)
                </label>
                <input
                  v-model="posterSubtitle"
                  type="text"
                  @input="updateChart"
                  class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:border-blue-500 outline-none text-slate-600"
                />
              </div>
            </div>
          </div>
          
          <div class="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Palette class="w-5 h-5 text-pink-500" /> 风格配色
            </h3>
            <div class="grid grid-cols-5 gap-2">
              <div
                v-for="theme in themes"
                :key="theme.name"
                @click="setTheme(theme.name)"
                :class="[
                  'theme-btn w-full aspect-square rounded-full border cursor-pointer shadow-sm transition-all',
                  theme.bg,
                  theme.border,
                  selectedTheme === theme.name ? 'active ring-2 ring-blue-500' : ''
                ]"
                :title="theme.label"
              ></div>
            </div>
          </div>
        </div>

        <!-- Right: Preview & Export -->
        <div
          :class="[
            'lg:col-span-8 flex flex-col gap-6 transition-all duration-500',
            !dataUnlocked ? 'filter blur-sm' : ''
          ]"
        >
          <div class="flex justify-center bg-slate-100 rounded-3xl p-8 border border-slate-200 relative overflow-hidden">
            <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
            
            <div class="relative w-full max-w-[480px] poster-container bg-white rounded-xl overflow-hidden shadow-2xl transform transition hover:scale-[1.01] duration-300">
              <canvas ref="canvasRef" class="w-full h-full"></canvas>
            </div>
          </div>
          
          <div class="flex justify-end">
            <button
              @click="downloadPoster"
              class="px-8 py-4 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl font-bold shadow-xl shadow-slate-300 transition-all flex items-center gap-3 transform hover:-translate-y-1"
            >
              <Download class="w-5 h-5" /> 导出小红书配图 (HD)
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useAnalysisStore } from '../stores/analysis'
import {
  Lock, LayoutGrid, ChevronRight, Edit3, Palette, Download,
  ArrowLeftRight, PieChart, Cloud
} from 'lucide-vue-next'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const emit = defineEmits(['switch-tab'])

const analysisStore = useAnalysisStore()
const dataUnlocked = computed(() => analysisStore.dataUnlocked)
const selectedDataType = ref('contrast')
const posterTitle = ref('中外舆论温差')
const posterSubtitle = ref('GrandChart 独家数据洞察')
const selectedTheme = ref('white')
const canvasRef = ref(null)
let chartInstance = null

const dataOptions = [
  {
    type: 'contrast',
    title: '中外舆论温差',
    subtitle: 'Domestic vs Intl Sentiment',
    icon: ArrowLeftRight,
    color: 'bg-blue-100 text-blue-600'
  },
  {
    type: 'sentiment',
    title: '网民情感光谱',
    subtitle: 'Emotional Spectrum',
    icon: PieChart,
    color: 'bg-purple-100 text-purple-600'
  },
  {
    type: 'keywords',
    title: '高频关键词云',
    subtitle: 'Keyword Frequency',
    icon: Cloud,
    color: 'bg-emerald-100 text-emerald-600'
  }
]

const themes = [
  { name: 'white', label: '简约白', bg: 'bg-slate-50', border: 'border-slate-200' },
  { name: 'cream', label: '奶油黄', bg: 'bg-[#FFF8E7]', border: 'border-orange-100' },
  { name: 'blue', label: '科技蓝', bg: 'bg-blue-50', border: 'border-blue-200' },
  { name: 'pink', label: '少女粉', bg: 'bg-pink-50', border: 'border-pink-200' },
  { name: 'dark', label: '暗黑风', bg: 'bg-slate-800', border: 'border-slate-600' }
]

const contrastData = ref({ domestic: [65, 20, 15], intl: [30, 40, 30] })

const POSTER_THEMES = {
  white: { bgStart: '#ffffff', bgEnd: '#f8fafc', text: '#334155', accent: '#3b82f6', grid: 'rgba(0,0,0,0.05)', colors: ['#3b82f6', '#60a5fa'] },
  cream: { bgStart: '#fffbeb', bgEnd: '#fff7ed', text: '#78350f', accent: '#f59e0b', grid: 'rgba(120, 53, 15, 0.05)', colors: ['#f59e0b', '#fbbf24'] },
  blue: { bgStart: '#eff6ff', bgEnd: '#dbeafe', text: '#1e3a8a', accent: '#2563eb', grid: 'rgba(30, 58, 138, 0.05)', colors: ['#2563eb', '#60a5fa'] },
  pink: { bgStart: '#fff1f2', bgEnd: '#ffe4e6', text: '#881337', accent: '#e11d48', grid: 'rgba(136, 19, 55, 0.05)', colors: ['#e11d48', '#fb7185'] },
  dark: { bgStart: '#1e293b', bgEnd: '#0f172a', text: '#f8fafc', accent: '#818cf8', grid: 'rgba(255,255,255,0.1)', colors: ['#818cf8', '#a5b4fc'] }
}

const initChart = async () => {
  await nextTick()
  if (!canvasRef.value) return

  const ctx = canvasRef.value.getContext('2d')
  const theme = POSTER_THEMES[selectedTheme.value]

  // Custom plugin for poster background
  const posterPlugin = {
    id: 'posterBackground',
    beforeDraw: (chart) => {
      const ctx = chart.ctx
      const width = chart.width
      const height = chart.height
      const theme = POSTER_THEMES[selectedTheme.value]

      // Background gradient
      const gradient = ctx.createLinearGradient(0, 0, 0, height)
      gradient.addColorStop(0, theme.bgStart)
      gradient.addColorStop(1, theme.bgEnd)
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, width, height)

      // Decorative circle
      ctx.beginPath()
      ctx.arc(width, 0, 150, 0, 2 * Math.PI)
      ctx.fillStyle = theme.accent
      ctx.globalAlpha = 0.05
      ctx.fill()
      ctx.globalAlpha = 1.0

      // Title & Subtitle
      ctx.save()
      ctx.fillStyle = theme.text
      ctx.textAlign = 'left'
      ctx.textBaseline = 'top'
      
      ctx.font = '900 36px "Noto Sans SC"'
      ctx.fillText(posterTitle.value, 40, 60)
      
      ctx.fillStyle = theme.accent
      ctx.fillRect(40, 110, 60, 6)

      ctx.fillStyle = theme.text
      ctx.globalAlpha = 0.7
      ctx.font = 'bold 18px "Noto Sans SC"'
      ctx.fillText(posterSubtitle.value, 40, 130)
      ctx.restore()

      // Footer
      ctx.save()
      ctx.fillStyle = theme.text
      ctx.globalAlpha = 0.4
      ctx.font = '12px "Noto Sans SC"'
      ctx.textAlign = 'center'
      ctx.fillText('@观潮GrandChart · AI舆情洞察', width / 2, height - 30)
      ctx.restore()
    }
  }

  const getChartData = () => {
    const theme = POSTER_THEMES[selectedTheme.value]
    if (selectedDataType.value === 'contrast') {
      return {
        labels: ['支持/正面', '中立/客观', '反对/负面'],
        datasets: [
          {
            label: '国内舆论',
            data: contrastData.value.domestic,
            backgroundColor: theme.colors[0],
            borderRadius: 8,
            barPercentage: 0.6
          },
          {
            label: '国际舆论',
            data: contrastData.value.intl,
            backgroundColor: '#94a3b8',
            borderRadius: 8,
            barPercentage: 0.6
          }
        ]
      }
    } else if (selectedDataType.value === 'sentiment') {
      return {
        labels: ['愤怒', '嘲讽', '失望', '中立'],
        datasets: [{
          data: [55, 25, 12, 8],
          backgroundColor: [theme.accent, '#f87171', '#fbbf24', '#cbd5e1'],
          borderWidth: 0
        }]
      }
    } else {
      return {
        labels: ['真相', '反转', '烂尾', '公信力', '甚至'],
        datasets: [{
          label: '热度',
          data: [1200, 950, 800, 600, 500],
          backgroundColor: theme.accent,
          borderRadius: 6
        }]
      }
    }
  }

  const chartType = selectedDataType.value === 'sentiment' ? 'doughnut' : 'bar'
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { top: 180, bottom: 60, left: 30, right: 30 } },
    plugins: {
      legend: {
        position: 'top',
        align: 'end',
        labels: {
          usePointStyle: true,
          boxWidth: 8,
          color: theme.text
        }
      }
    }
  }

  if (selectedDataType.value === 'contrast') {
    chartOptions.scales = {
      y: {
        grid: { color: theme.grid },
        border: { display: false }
      },
      x: { grid: { display: false } }
    }
    chartOptions.indexAxis = 'x'
  } else if (selectedDataType.value === 'sentiment') {
    chartOptions.scales = { x: { display: false }, y: { display: false } }
  } else {
    chartOptions.indexAxis = 'y'
    chartOptions.scales = { x: { display: false }, y: { display: false } }
  }

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(ctx, {
    type: chartType,
    data: getChartData(),
    options: chartOptions,
    plugins: [posterPlugin]
  })
}

const selectDataType = (type) => {
  selectedDataType.value = type
  if (type === 'contrast') {
    posterTitle.value = '中外舆论温差'
    posterSubtitle.value = 'GrandChart · 舆情全域扫描'
  } else if (type === 'sentiment') {
    posterTitle.value = '网民情感光谱'
    posterSubtitle.value = 'GrandChart · 情绪极化分析'
  } else {
    posterTitle.value = '核心关键词云'
    posterSubtitle.value = 'GrandChart · 高频词汇捕捉'
  }
  updateChart()
}

const setTheme = (theme) => {
  selectedTheme.value = theme
  updateChart()
}

const updateChart = () => {
  if (chartInstance) {
    initChart()
  }
}

const downloadPoster = () => {
  if (!canvasRef.value) return
  const link = document.createElement('a')
  link.download = `GrandChart_Post_${Date.now()}.png`
  link.href = canvasRef.value.toDataURL('image/png', 2.0)
  link.click()
}

// 监听数据解锁（从分析store获取）
watch(() => analysisStore.dataUnlocked, (unlocked) => {
  if (unlocked) {
    nextTick(() => {
      initChart()
    })
  }
})

// 监听对比数据更新
watch(() => analysisStore.contrastData, (data) => {
  if (data) {
    contrastData.value = data
    updateChart()
  }
})

onMounted(() => {
  // 如果数据已解锁，初始化图表
  if (analysisStore.dataUnlocked) {
    nextTick(() => {
      initChart()
    })
  }
})
</script>