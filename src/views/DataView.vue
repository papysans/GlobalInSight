<template>
  <div class="view-section animate-fade-in py-12 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">多维数据洞察</h2>
        <p class="text-slate-500 dark:text-slate-400">基于真实数据的AI推理可视化</p>
      </div>

      <!-- 数据锁定提示 -->
      <div
        v-if="!dataUnlocked"
        class="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/50 rounded-xl p-6 flex items-start gap-4"
      >
        <div class="w-12 h-12 bg-blue-100 dark:bg-blue-800/50 rounded-full flex items-center justify-center flex-shrink-0">
          <Lock class="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        <div class="flex-1">
          <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-2">数据尚未生成</h3>
          <p class="text-slate-600 dark:text-slate-400 mb-4">请先在「舆情推演」页面启动分析，系统将基于辩论结果自动生成数据洞察。</p>
          <button
            @click="$emit('switch-tab', 'home')"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            前往推演
          </button>
        </div>
      </div>

      <!-- 测试按钮（仅在数据已解锁时显示） -->
      <div v-if="dataUnlocked" class="mb-6 space-y-4">
        <!-- 生成图表按钮 -->
        <div class="flex items-center justify-between bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-700/50 rounded-xl p-4">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-purple-100 dark:bg-purple-800/50 rounded-full flex items-center justify-center">
              <Download class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-900 dark:text-white">数据可视化生成</h3>
              <p class="text-xs text-slate-600 dark:text-slate-400">生成三张数据可视化图表用于小红书发布</p>
            </div>
          </div>
          <button
            @click="testGenerateImages"
            :disabled="isGenerating"
            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-300 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <Loader2 v-if="isGenerating" class="w-4 h-4 animate-spin" />
            <span>{{ isGenerating ? '生成中...' : '生成可视化图表' }}</span>
          </button>
        </div>
      </div>

      <!-- 隐藏的 Canvas 组件（用于生成图片） -->
      <div class="hidden">
        <RadarChartCanvas 
          ref="radarChartCanvasRef" 
          :data="radarChartData" 
          :show-preview="false" 
        />
        <DebateTimelineCanvas 
          ref="debateTimelineCanvasRef" 
          :timeline="debateTimelineData" 
          :show-preview="false" 
        />
        <TrendChartCanvas 
          ref="trendChartCanvasRef" 
          :data="trendChartData" 
          :show-preview="false" 
        />
      </div>

      <!-- 双卡布局 -->
      <div v-if="dataUnlocked" class="grid lg:grid-cols-2 gap-6">
        <!-- 左侧列 -->
        <div class="space-y-6">
          <!-- 洞察卡 -->
          <InsightCard
            :conclusion="insightCardData.conclusion"
            :coverage="insightCardData.coverage"
            :key-finding="insightCardData.keyFinding"
          />

          <!-- 关键发现卡片 -->
          <div v-if="keyFindings.length > 0" class="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 rounded-2xl shadow-lg p-6 border border-orange-200 dark:border-orange-700/50">
            <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Sparkles class="w-5 h-5 text-orange-600 dark:text-orange-400" />
              关键发现
            </h3>
            <div class="space-y-3">
              <div v-for="(finding, index) in keyFindings" :key="`finding-${index}`" class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                  {{ index + 1 }}
                </div>
                <p class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{{ finding }}</p>
              </div>
            </div>
          </div>

          <!-- 平台热度分布 -->
          <!-- <div v-if="platformHeatList.length > 0" class="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
            <h3 class="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <BarChart3 class="w-5 h-5 text-blue-600" />
              平台热度分布
            </h3>
            <div class="space-y-3">
              <div v-for="platform in platformHeatList" :key="`platform-${platform.name}`" class="space-y-1">
                <div class="flex items-center justify-between text-sm">
                  <span class="font-medium text-slate-700">{{ platform.name }}</span>
                  <span class="text-slate-500">{{ platform.value }}</span>
                </div>
                <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div 
                    class="h-full rounded-full transition-all duration-500"
                    :class="platform.color"
                    :style="{ width: platform.percentage + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div> -->
        </div>

        <!-- 右侧列：数据可视化卡 -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6 border border-slate-200 dark:border-slate-700">
          <!-- Tab 选择器 -->
          <div class="flex gap-2 mb-6 border-b border-slate-200 dark:border-slate-700 pb-4">
            <button
              v-for="option in vizOptions"
              :key="`viz-${option.type}`"
              @click="selectedVizOption = option.type"
              :class="[
                'px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2',
                selectedVizOption === option.type
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              ]"
            >
              <component :is="option.icon" class="w-4 h-4" />
              {{ option.label }}
            </button>
          </div>

          <!-- 图表容器 -->
          <div class="chart-container relative" style="min-height: 400px;">
            <!-- 雷达图 -->
            <div v-if="selectedVizOption === 'radar'" class="animate-fade-in">
              <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <Radar class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                平台覆盖分布
              </h3>
              <RadarChart
                :data="radarChartData"
                :theme="selectedTheme"
              />
            </div>

            <!-- 辩论时间线 -->
            <div v-if="selectedVizOption === 'timeline'" class="animate-fade-in">
              <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <GitBranch class="w-5 h-5 text-purple-600 dark:text-purple-400" />
                辩论演化过程
              </h3>
              <DebateTimeline
                :timeline="debateTimelineData"
              />
            </div>

            <!-- 热度趋势 -->
            <div v-if="selectedVizOption === 'trend'" class="animate-fade-in">
              <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <TrendingUp class="w-5 h-5 text-green-600 dark:text-green-400" />
                热度趋势分析
              </h3>
              <TrendChart
                :data="trendChartData"
                :theme="selectedTheme"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 旧版控制面板和预览（保留用于导出功能） -->
      <div v-if="false" class="relative grid lg:grid-cols-12 gap-6 items-start mt-8">

        <!-- Left: Control Panel -->
        <div
          :class="[
            'lg:col-span-3 space-y-4 transition-all duration-500',
            (!dataUnlocked && dataSource === 'workflow') ? 'filter blur-sm' : ''
          ]"
        >
          <!-- 数据源选择 -->
          <div class="bg-white p-4 rounded-xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2 text-sm">
              <Database class="w-4 h-4 text-indigo-600" />
              数据源
            </h3>
            <div class="space-y-1.5">
              <button
                @click="dataSource = 'workflow'"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg border-2 transition-all text-sm',
                  dataSource === 'workflow'
                    ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                ]"
              >
                <div class="flex items-center gap-2">
                  <div :class="['w-1.5 h-1.5 rounded-full', dataSource === 'workflow' ? 'bg-indigo-500' : 'bg-slate-300']"></div>
                  <span class="font-medium text-xs">舆情推演</span>
                </div>
              </button>
              <button
                @click="dataSource = 'hotnews'"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg border-2 transition-all text-sm',
                  dataSource === 'hotnews'
                    ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                ]"
              >
                <div class="flex items-center gap-2">
                  <div :class="['w-1.5 h-1.5 rounded-full', dataSource === 'hotnews' ? 'bg-indigo-500' : 'bg-slate-300']"></div>
                  <span class="font-medium text-xs">热点系统</span>
                </div>
              </button>
            </div>
          </div>

          <!-- 热点选择器（仅热点数据源时显示） -->
          <div v-if="dataSource === 'hotnews'" class="bg-white p-4 rounded-xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2 text-sm">
              <TrendingUp class="w-4 h-4 text-orange-600" />
              选择热点
            </h3>
            <div v-if="isLoadingHotNews" class="text-center py-3 text-xs text-slate-500">
              <div class="animate-spin w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              加载中...
            </div>
            <div v-else-if="hotNewsList.length === 0" class="text-center py-3 text-xs text-slate-500">
              暂无数据
              <button
                @click="loadHotNews"
                class="mt-2 text-orange-600 hover:text-orange-700 underline text-xs"
              >
                刷新
              </button>
            </div>
            <div v-else class="space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar">
              <button
                v-for="item in hotNewsList.slice(0, 8)"
                :key="item.id"
                @click="selectHotTopic(item)"
                :class="[
                  'w-full text-left px-2.5 py-1.5 rounded-lg border transition-all text-xs',
                  selectedHotTopic?.id === item.id
                    ? 'bg-orange-50 border-orange-300 text-orange-900'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                ]"
              >
                <div class="font-medium truncate">{{ item.title }}</div>
                <div class="text-[10px] text-slate-500 mt-0.5 truncate">
                  {{ item.platform || '多平台' }} · {{ item.hot_value || '热度未知' }}
                </div>
              </button>
            </div>
            <button
              @click="loadHotNews"
              class="mt-2 w-full px-2.5 py-1.5 text-xs bg-orange-50 hover:bg-orange-100 text-orange-700 rounded-lg transition-colors"
            >
              <RefreshCw class="w-3 h-3 inline mr-1" />
              刷新
            </button>
          </div>

          <!-- 图表数据选择 -->
          <div class="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <LayoutGrid class="w-5 h-5 text-blue-600" />
              图表数据选择
            </h3>
            <div class="space-y-3">
              <button
                v-for="option in availableDataOptions"
                :key="`data-${option.type}`"
                @click="selectDataType(option.type)"
                :class="[
                  'data-btn w-full text-left px-4 py-3 rounded-xl bg-white text-slate-600 border border-slate-200 font-medium hover:bg-slate-50 transition-colors flex justify-between items-center group shadow-sm',
                  selectedDataType === option.type ? 'btn-selected border-blue-500 bg-blue-50' : ''
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

          <!-- 风格配色 -->
          <div class="bg-white p-4 rounded-xl shadow-lg border border-slate-200">
            <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2 text-sm">
              <Palette class="w-4 h-4 text-pink-500" />
              配色方案
            </h3>
            <div class="grid grid-cols-5 gap-1.5">
              <div
                v-for="theme in themes"
                :key="`theme-${theme.name}`"
                @click="setTheme(theme.name)"
                :class="[
                  'theme-btn w-full aspect-square rounded-full border cursor-pointer shadow-sm transition-all',
                  theme.bg,
                  theme.border,
                  selectedTheme === theme.name ? 'active ring-2 ring-blue-500 scale-110' : ''
                ]"
                :title="theme.label"
              ></div>
            </div>
          </div>

          <!-- Agent信息展示（仅舆情推演数据源时显示，紧凑版） -->
          <div v-if="dataSource === 'workflow' && agentInfo.agent_name" class="bg-gradient-to-br from-indigo-50 to-purple-50 p-4 rounded-xl shadow-lg border border-indigo-100">
            <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2 text-sm">
              <BrainCircuit class="w-4 h-4 text-indigo-600" />
              Agent信息
            </h3>
            <div class="space-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-slate-600 text-xs">Agent:</span>
                <span class="font-bold text-indigo-700 text-xs">{{ agentInfo.agent_name.toUpperCase() }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600 text-xs">LLM:</span>
                <span :class="[
                  'px-1.5 py-0.5 rounded text-[10px] font-medium',
                  agentInfo.used_llm 
                    ? 'bg-emerald-100 text-emerald-700' 
                    : 'bg-slate-100 text-slate-600'
                ]">
                  {{ agentInfo.used_llm ? '✓' : '✗' }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600 text-xs">缓存:</span>
                <span :class="[
                  'px-1.5 py-0.5 rounded text-[10px] font-medium',
                  agentInfo.cache_hit 
                    ? 'bg-amber-100 text-amber-700' 
                    : 'bg-blue-100 text-blue-700'
                ]">
                  {{ agentInfo.cache_hit ? '✓' : '✗' }}
                </span>
              </div>
              
              <!-- LLM生成内容展示（紧凑版） -->
              <div v-if="agentInfo.used_llm && agentInfo.llm_reasoning" class="pt-2 border-t border-indigo-200">
                <div class="flex items-center gap-1.5 mb-1.5">
                  <Sparkles class="w-3 h-3 text-indigo-600" />
                  <span class="text-[10px] font-bold text-indigo-700 uppercase tracking-wider">LLM内容</span>
                </div>
                <div class="bg-gradient-to-br from-white to-indigo-50/30 rounded-lg p-2 border border-indigo-200 max-h-32 overflow-y-auto custom-scrollbar shadow-inner">
                  <p class="text-[10px] text-slate-700 leading-relaxed font-mono whitespace-pre-wrap break-words">
                    {{ agentInfo.llm_reasoning }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Preview & Export -->
        <div
          :class="[
            'lg:col-span-9 flex flex-col gap-6 transition-all duration-500',
            (!dataUnlocked && dataSource === 'workflow') ? 'filter blur-sm' : ''
          ]"
        >
          <div class="flex justify-center bg-slate-100 rounded-3xl p-8 border border-slate-200 relative overflow-hidden">
            <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
            
            <!-- 加载遮罩 -->
            <div
              v-if="isChartLoading"
              class="absolute inset-0 z-30 flex items-center justify-center bg-white/90 backdrop-blur-sm rounded-3xl transition-opacity duration-300"
            >
              <div class="text-center">
                <Loader2 class="w-10 h-10 text-blue-600 animate-spin mx-auto mb-3" />
                <p class="text-sm text-slate-700 font-medium">正在生成图表...</p>
              </div>
            </div>
            
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
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useAnalysisStore } from '../stores/analysis'
import { api } from '../api'
import {
  Lock, LayoutGrid, ChevronRight, Edit3, Palette, Download,
  ArrowLeftRight, PieChart, Cloud, Database, TrendingUp, RefreshCw, BarChart3, Loader2, Radar, GitBranch, Sparkles, BrainCircuit
} from 'lucide-vue-next'
import { Chart, registerables } from 'chart.js'
import InsightCard from '../components/InsightCard.vue'
import RadarChart from '../components/RadarChart.vue'
import DebateTimeline from '../components/DebateTimeline.vue'
import TrendChart from '../components/TrendChart.vue'
import RadarChartCanvas from '../components/canvas/RadarChartCanvas.vue'
import DebateTimelineCanvas from '../components/canvas/DebateTimelineCanvas.vue'
import TrendChartCanvas from '../components/canvas/TrendChartCanvas.vue'

Chart.register(...registerables)

// 防抖函数
const debounce = (fn, delay = 300) => {
  let timer = null
  return function(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

const emit = defineEmits(['switch-tab'])

const analysisStore = useAnalysisStore()
const dataUnlocked = computed(() => analysisStore.dataUnlocked)

// Canvas 组件引用
const radarChartCanvasRef = ref(null)
const debateTimelineCanvasRef = ref(null)
const trendChartCanvasRef = ref(null)

// 生成状态
const isGenerating = ref(false)

// 新增：从 store 获取洞察卡和雷达图数据
const insightCardData = computed(() => analysisStore.insightCardData)
const radarChartData = computed(() => analysisStore.radarChartData)
const debateTimelineData = computed(() => analysisStore.debateTimelineData)
const trendChartData = computed(() => analysisStore.trendChartData)

// 关键发现列表
const keyFindings = computed(() => {
  const findings = []
  const insight = analysisStore.insight || ''
  
  // 提取关键发现（以"。"分割，取前3条）
  const sentences = insight.split(/[。！？]/).filter(s => s.trim().length > 10)
  return sentences.slice(0, 3)
})

// 平台热度列表
const platformHeatList = computed(() => {
  const platforms = analysisStore.selectedPlatforms || []
  if (platforms.length === 0) return []
  
  const colors = [
    'bg-blue-500',
    'bg-green-500',
    'bg-purple-500',
    'bg-orange-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-red-500'
  ]
  
  const platformNames = {
    wb: '微博',
    bili: 'B站',
    xhs: '小红书',
    dy: '抖音',
    ks: '快手',
    tieba: '贴吧',
    zhihu: '知乎',
    hn: 'Hacker News'
  }
  
  // 生成热度数据（基于平台名称的伪随机值）
  const heatData = platforms.map((p, index) => {
    const name = platformNames[p] || p
    const baseValue = 60 + (name.charCodeAt(0) % 35)
    return {
      name,
      value: baseValue,
      percentage: baseValue,
      color: colors[index % colors.length]
    }
  })
  
  // 按热度排序
  return heatData.sort((a, b) => b.value - a.value)
})

// 可视化选项状态
const selectedVizOption = ref('radar')
const vizOptions = [
  { type: 'radar', label: '平台覆盖', icon: Radar },
  { type: 'timeline', label: '辩论演化', icon: GitBranch },
  { type: 'trend', label: '热度趋势', icon: TrendingUp }
]

// 生成数据视图卡片图片（右侧三个可视化图表）
const generateDataViewImages = async () => {
  console.log('[DataView] 🎨 开始生成数据视图卡片图片')
  console.log('[DataView] 📊 当前数据状态:', {
    radarLabels: radarChartData.value.labels,
    radarData: radarChartData.value.datasets[0].data,
    timelineRounds: debateTimelineData.value.length,
    trendStage: trendChartData.value.stage,
    trendGrowth: trendChartData.value.growth,
    trendCurve: trendChartData.value.curve
  })
  
  const images = []
  
  try {
    // 生成雷达图
    if (radarChartCanvasRef.value && radarChartData.value.labels.length > 0) {
      console.log('[DataView] 📡 生成雷达图...')
      const img = await radarChartCanvasRef.value.generateImage()
      images.push(img)
      console.log('[DataView] ✅ 雷达图已生成')
    } else {
      console.warn('[DataView] ⚠️ 雷达图数据为空，跳过')
    }
    
    // 生成辩论时间线
    if (debateTimelineCanvasRef.value && debateTimelineData.value.length > 0) {
      console.log('[DataView] 🔄 生成辩论时间线...')
      const img = await debateTimelineCanvasRef.value.generateImage()
      images.push(img)
      console.log('[DataView] ✅ 辩论时间线已生成')
    } else {
      console.warn('[DataView] ⚠️ 辩论时间线数据为空，跳过')
    }
    
    // 生成趋势图
    if (trendChartCanvasRef.value && trendChartData.value.curve.length > 0) {
      console.log('[DataView] 📈 生成趋势图...')
      const img = await trendChartCanvasRef.value.generateImage()
      images.push(img)
      console.log('[DataView] ✅ 趋势图已生成')
    } else {
      console.warn('[DataView] ⚠️ 趋势图数据为空，跳过')
    }
    
    console.log('[DataView] 🎉 所有卡片生成完成，总数:', images.length)
  } catch (error) {
    console.error('[DataView] ❌ 生成数据视图图片失败:', error)
  }
  
  return images
}

// 测试生成图片
const testGenerateImages = async () => {
  if (isGenerating.value) return
  
  isGenerating.value = true
  
  try {
    console.log('开始生成数据可视化图片...')
    const images = await generateDataViewImages()
    
    console.log(`成功生成 ${images.length} 张图片`)
    
    // 保存到 store
    analysisStore.setDataViewImages(images)
    
    // 下载预览
    const names = ['平台覆盖雷达图', '辩论演化时间线', '热度趋势分析']
    images.forEach((img, index) => {
      const link = document.createElement('a')
      link.download = `${names[index]}.png`
      link.href = img
      link.click()
    })
    
    alert(`成功生成 ${images.length} 张数据可视化图片！已自动下载预览。`)
  } catch (error) {
    console.error('测试生成失败:', error)
    alert('生成失败，请查看控制台错误信息')
  } finally {
    isGenerating.value = false
  }
}

// 暴露给父组件使用
defineExpose({
  generateDataViewImages
})

// 数据源：'workflow' 或 'hotnews'
const dataSource = ref('workflow')
const selectedDataType = ref('contrast')
const posterTitle = ref('中外舆论温差')
const posterSubtitle = ref('GrandChart 独家数据洞察')
const selectedTheme = ref('white')
const canvasRef = ref(null)
let chartInstance = null

// 加载状态
const isChartLoading = ref(false)
const isSwitchingDataSource = ref(false)

// 热点数据相关
const hotNewsList = ref([])
const selectedHotTopic = ref(null)
const isLoadingHotNews = ref(false)
const platformHeatData = ref({}) // 平台热度数据

// 数据状态
const contrastData = ref({ domestic: [65, 20, 15], intl: [30, 40, 30] })
const sentimentData = ref([
  { name: '愤怒', value: 55 },
  { name: '嘲讽', value: 25 },
  { name: '失望', value: 12 },
  { name: '中立', value: 8 }
])
const keywordsData = ref([
  { word: '真相', frequency: 1200 },
  { word: '反转', frequency: 950 },
  { word: '烂尾', frequency: 800 },
  { word: '公信力', frequency: 600 },
  { word: '甚至', frequency: 500 }
])
const isLoadingData = ref(false)

// Agent信息状态
const agentInfo = ref({
  agent_name: '',
  used_llm: false,
  cache_hit: false,
  llm_reasoning: '',  // LLM生成的内容片段
  is_thinking: false,  // 是否正在思考
  thinking_step: ''   // 当前思考步骤
})

// 所有可用的图表选项
const allDataOptions = [
  {
    type: 'contrast',
    title: '中外舆论温差',
    subtitle: 'Domestic vs Intl Sentiment',
    icon: ArrowLeftRight,
    color: 'bg-blue-100 text-blue-600',
    availableFor: ['workflow']
  },
  {
    type: 'sentiment',
    title: '网民情感光谱',
    subtitle: 'Emotional Spectrum',
    icon: PieChart,
    color: 'bg-purple-100 text-purple-600',
    availableFor: ['workflow']
  },
  {
    type: 'keywords',
    title: '高频关键词云',
    subtitle: 'Keyword Frequency',
    icon: Cloud,
    color: 'bg-emerald-100 text-emerald-600',
    availableFor: ['workflow']
  },
  {
    type: 'platform-heat',
    title: '平台热度对比',
    subtitle: 'Platform Heat Comparison',
    icon: BarChart3,
    color: 'bg-orange-100 text-orange-600',
    availableFor: ['hotnews']
  }
]

// 根据数据源过滤可用的图表选项
const availableDataOptions = computed(() => {
  return allDataOptions.filter(opt => opt.availableFor.includes(dataSource.value))
})

const themes = [
  { name: 'white', label: '简约白', bg: 'bg-slate-50', border: 'border-slate-200' },
  { name: 'cream', label: '奶油黄', bg: 'bg-[#FFF8E7]', border: 'border-orange-100' },
  { name: 'blue', label: '科技蓝', bg: 'bg-blue-50', border: 'border-blue-200' },
  { name: 'pink', label: '少女粉', bg: 'bg-pink-50', border: 'border-pink-200' },
  { name: 'dark', label: '暗黑风', bg: 'bg-slate-800', border: 'border-slate-600' }
]

const POSTER_THEMES = {
  white: { bgStart: '#ffffff', bgEnd: '#f8fafc', text: '#334155', accent: '#3b82f6', grid: 'rgba(0,0,0,0.05)', colors: ['#3b82f6', '#60a5fa'] },
  cream: { bgStart: '#fffbeb', bgEnd: '#fff7ed', text: '#78350f', accent: '#f59e0b', grid: 'rgba(120, 53, 15, 0.05)', colors: ['#f59e0b', '#fbbf24'] },
  blue: { bgStart: '#eff6ff', bgEnd: '#dbeafe', text: '#1e3a8a', accent: '#2563eb', grid: 'rgba(30, 58, 138, 0.05)', colors: ['#2563eb', '#60a5fa'] },
  pink: { bgStart: '#fff1f2', bgEnd: '#ffe4e6', text: '#881337', accent: '#e11d48', grid: 'rgba(136, 19, 55, 0.05)', colors: ['#e11d48', '#fb7185'] },
  dark: { bgStart: '#1e293b', bgEnd: '#0f172a', text: '#f8fafc', accent: '#818cf8', grid: 'rgba(255,255,255,0.1)', colors: ['#818cf8', '#a5b4fc'] }
}

// 加载热点新闻列表
const loadHotNews = async () => {
  isLoadingHotNews.value = true
  try {
    const result = await api.getHotNewsTrending({ platforms: ['all'], force_refresh: false })
    if (result.success && result.news_list) {
      hotNewsList.value = result.news_list
      if (hotNewsList.value.length > 0 && !selectedHotTopic.value) {
        selectHotTopic(hotNewsList.value[0])
      }
    }
  } catch (err) {
    console.error('加载热点数据失败:', err)
  } finally {
    isLoadingHotNews.value = false
  }
}

// 选择热点话题（带防抖和加载状态）
const selectHotTopicDebounced = debounce(async (topic) => {
  if (isChartLoading.value) return
  
  selectedHotTopic.value = topic
  isChartLoading.value = true
  
  try {
    // 解析平台热度数据
    if (topic.platforms_data && Array.isArray(topic.platforms_data)) {
      const platformMap = {}
      topic.platforms_data.forEach(p => {
        const platformName = p.platform || p.platform_id || '未知平台'
        // 尝试解析热度值
        const hotValue = p.hot_value || p.hot_score || 0
        let heatScore = 0
        if (typeof hotValue === 'number') {
          heatScore = hotValue
        } else if (typeof hotValue === 'string') {
          // 尝试从字符串中提取数字
          const match = hotValue.match(/([\d,.]+)/)
          if (match) {
            heatScore = parseFloat(match[1].replace(/,/g, '')) || 0
          }
        }
        platformMap[platformName] = heatScore
      })
      platformHeatData.value = platformMap
    } else {
      // 如果没有 platforms_data，尝试从 evidence 中提取
      platformHeatData.value = {}
      if (topic.evidence && Array.isArray(topic.evidence)) {
        const platformMap = {}
        topic.evidence.forEach(ev => {
          const platformName = ev.platform || '未知平台'
          platformMap[platformName] = (platformMap[platformName] || 0) + 1
        })
        platformHeatData.value = platformMap
      }
    }
    
    // 更新标题
    posterTitle.value = topic.title || '平台热度对比'
    posterSubtitle.value = `覆盖 ${Object.keys(platformHeatData.value).length} 个平台`
    
    // 如果当前选中的是平台热度对比图表，更新图表
    if (selectedDataType.value === 'platform-heat') {
      await nextTick()
      await updateChart(true)
    }
  } finally {
    // 延迟一点再隐藏，确保动画可见
    setTimeout(() => {
      isChartLoading.value = false
    }, 100)
  }
}, 200)

const selectHotTopic = (topic) => {
  selectHotTopicDebounced(topic)
}

// 生成数据的函数
const generateData = async (type) => {
  if (isLoadingData.value) return
  
  if (dataSource.value === 'workflow') {
    // 舆情推演数据生成逻辑（原有逻辑）
    const systemLog = analysisStore.logs.find(log => log.agent_name === 'System')
    const topic = (systemLog && systemLog.step_content) || '当前议题'
    const insight = analysisStore.insight || '核心洞察'
    
    if (!insight || insight.trim() === '') {
      console.warn('洞察内容为空，无法生成数据')
      return
    }
    
    isLoadingData.value = true
    // 设置思考状态
    agentInfo.value.is_thinking = true
    agentInfo.value.thinking_step = '正在分析议题和洞察...'
    
    try {
      if (type === 'contrast') {
        agentInfo.value.thinking_step = '正在调用LLM分析中外舆论对比...'
        const data = await api.generateContrastData({ topic, insight })
        contrastData.value = data
        // 保存Agent信息
        agentInfo.value = {
          agent_name: data.agent_name || 'analyst',
          used_llm: data.used_llm !== undefined ? data.used_llm : true,
          cache_hit: data.cache_hit !== undefined ? data.cache_hit : false,
          llm_reasoning: data.llm_reasoning || '',
          is_thinking: false,
          thinking_step: ''
        }
        if (analysisStore.insightTitle) {
          posterTitle.value = analysisStore.insightTitle
        }
        if (analysisStore.insightSubtitle) {
          posterSubtitle.value = analysisStore.insightSubtitle
        }
      } else if (type === 'sentiment') {
        const data = await api.generateSentimentData({ topic, insight })
        sentimentData.value = data.emotions
        // 保存Agent信息
        agentInfo.value = {
          agent_name: data.agent_name || 'analyst',
          used_llm: data.used_llm !== undefined ? data.used_llm : true,
          cache_hit: data.cache_hit !== undefined ? data.cache_hit : false,
          llm_reasoning: data.llm_reasoning || ''
        }
      } else if (type === 'keywords') {
        agentInfo.value.thinking_step = '正在调用LLM提取关键词...'
        const data = await api.generateKeywordsData({ topic })
        keywordsData.value = data.keywords
        // 保存Agent信息
        agentInfo.value = {
          agent_name: data.agent_name || 'analyst',
          used_llm: data.used_llm !== undefined ? data.used_llm : true,
          cache_hit: data.cache_hit !== undefined ? data.cache_hit : false,
          llm_reasoning: data.llm_reasoning || '',
          is_thinking: false,
          thinking_step: ''
        }
      }
      updateChart()
    } catch (err) {
      console.error('生成数据失败:', err)
      // 错误时清除思考状态
      agentInfo.value.is_thinking = false
      agentInfo.value.thinking_step = '生成失败，请重试'
    } finally {
      isLoadingData.value = false
      // 确保思考状态被清除
      if (!agentInfo.value.agent_name) {
        agentInfo.value.is_thinking = false
        agentInfo.value.thinking_step = ''
      }
    }
  } else if (dataSource.value === 'hotnews') {
    // 热点数据：平台热度对比直接使用已加载的数据
    if (type === 'platform-heat' && selectedHotTopic.value) {
      // 数据已在 selectHotTopic 中处理
      updateChart(true) // 显示加载动画
    }
  }
}

const initChart = async () => {
  await nextTick()
  if (!canvasRef.value) return

  // 如果已经在加载中，不重复设置
  const wasAlreadyLoading = isChartLoading.value
  if (!wasAlreadyLoading) {
    isChartLoading.value = true
  }
  
  try {
    // 添加小延迟，让加载动画可见
    if (!wasAlreadyLoading) {
      await new Promise(resolve => setTimeout(resolve, 150))
    }
    
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
      ctx.fillText('@观潮GlobalInSight · AI舆情洞察', width / 2, height - 30)
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
        labels: sentimentData.value.map(item => item.name),
        datasets: [{
          data: sentimentData.value.map(item => item.value),
          backgroundColor: [theme.accent, '#f87171', '#fbbf24', '#cbd5e1', '#a78bfa', '#34d399'].slice(0, sentimentData.value.length),
          borderWidth: 0
        }]
      }
    } else if (selectedDataType.value === 'keywords') {
      return {
        labels: keywordsData.value.map(item => item.word),
        datasets: [{
          label: '热度',
          data: keywordsData.value.map(item => item.frequency),
          backgroundColor: theme.accent,
          borderRadius: 6
        }]
      }
    } else if (selectedDataType.value === 'platform-heat') {
      // 平台热度对比
      const platforms = Object.keys(platformHeatData.value)
      const values = Object.values(platformHeatData.value)
      // 如果数据为空，使用示例数据
      if (platforms.length === 0) {
        return {
          labels: ['微博', 'B站', '知乎', '抖音', '百度'],
          datasets: [{
            label: '热度',
            data: [0, 0, 0, 0, 0],
            backgroundColor: theme.accent,
            borderRadius: 6
          }]
        }
      }
      return {
        labels: platforms,
        datasets: [{
          label: '热度',
          data: values,
          backgroundColor: theme.accent,
          borderRadius: 6
        }]
      }
    }
  }

  let chartType = 'bar'
  if (selectedDataType.value === 'sentiment') {
    chartType = 'doughnut'
  } else if (selectedDataType.value === 'platform-heat' || selectedDataType.value === 'keywords') {
    chartType = 'bar'
  }

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
  } else if (selectedDataType.value === 'platform-heat') {
    chartOptions.indexAxis = 'y'
    chartOptions.scales = {
      x: {
        grid: { color: theme.grid },
        border: { display: false }
      },
      y: { grid: { display: false } }
    }
  } else if (selectedDataType.value === 'keywords') {
    // 关键词云：显示y轴标签（关键词名称），隐藏x轴
    chartOptions.indexAxis = 'y'
    chartOptions.scales = {
      x: { 
        display: false,
        grid: { display: false }
      },
      y: { 
        display: true,
        grid: { display: false },
        ticks: {
          color: theme.text,
          font: {
            size: 12,
            weight: 'bold'
          },
          mirror: false,
          padding: 8
        }
      }
    }
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
    
    // 确保图表渲染完成后再隐藏加载状态
    await nextTick()
  } finally {
    // 隐藏加载状态（只有我们设置的才清除）
    if (!wasAlreadyLoading) {
      // 延迟一点再隐藏，确保动画可见
      setTimeout(() => {
        isChartLoading.value = false
      }, 50)
    }
  }
}

// 选择图表类型（带防抖）
const selectDataTypeDebounced = debounce(async (type) => {
  if (isChartLoading.value) return
  
  selectedDataType.value = type
  isChartLoading.value = true
  
  try {
    if (dataSource.value === 'workflow') {
      if (type === 'contrast') {
        posterTitle.value = analysisStore.insightTitle || '中外舆论温差'
        posterSubtitle.value = analysisStore.insightSubtitle || 'GrandChart · 舆情全域扫描'
        await generateData('contrast')
      } else if (type === 'sentiment') {
        posterTitle.value = '网民情感光谱'
        posterSubtitle.value = 'GrandChart · 情绪极化分析'
        await generateData('sentiment')
      } else {
        posterTitle.value = '核心关键词云'
        posterSubtitle.value = 'GrandChart · 高频词汇捕捉'
        await generateData('keywords')
      }
    } else if (dataSource.value === 'hotnews') {
      if (type === 'platform-heat') {
        posterTitle.value = selectedHotTopic.value?.title || '平台热度对比'
        posterSubtitle.value = `覆盖 ${Object.keys(platformHeatData.value).length} 个平台`
        await generateData('platform-heat')
      }
    }
    await updateChart()
  } finally {
    isChartLoading.value = false
  }
}, 200)

const selectDataType = (type) => {
  selectDataTypeDebounced(type)
}

const setTheme = (theme) => {
  selectedTheme.value = theme
  updateChart(false) // 切换主题时不显示加载动画
}

const updateChart = async (showLoading = false) => {
  if (chartInstance) {
    if (showLoading) {
      isChartLoading.value = true
    }
    await initChart()
  }
}

const downloadPoster = () => {
  if (!canvasRef.value) return
  const link = document.createElement('a')
  link.download = `GrandChart_Post_${Date.now()}.png`
  link.href = canvasRef.value.toDataURL('image/png', 2.0)
  link.click()
}

// 监听数据源切换（带防抖和加载状态）
const handleDataSourceChange = debounce(async (newSource) => {
  if (isSwitchingDataSource.value) return
  
  isSwitchingDataSource.value = true
  isChartLoading.value = true
  
  try {
    if (newSource === 'hotnews') {
      // 切换到热点数据源时，加载热点列表
      if (hotNewsList.value.length === 0) {
        await loadHotNews()
      }
      // 自动选择第一个可用的图表类型
      if (availableDataOptions.value.length > 0) {
        await selectDataType(availableDataOptions.value[0].type)
      }
    } else {
      // 切换回舆情推演数据源时，重置为默认图表
      if (availableDataOptions.value.length > 0) {
        await selectDataType(availableDataOptions.value[0].type)
      }
    }
  } finally {
    isSwitchingDataSource.value = false
    isChartLoading.value = false
  }
}, 300)

watch(dataSource, (newSource) => {
  handleDataSourceChange(newSource)
})

// 监听数据解锁（从分析store获取）
watch(() => analysisStore.dataUnlocked, async (unlocked) => {
  if (unlocked && dataSource.value === 'workflow') {
    await generateData('contrast')
    nextTick(() => {
      initChart()
    })
  }
})

// 监听洞察更新，自动更新标题和副标题
watch(() => analysisStore.insightTitle, (title) => {
  if (title && selectedDataType.value === 'contrast' && dataSource.value === 'workflow') {
    posterTitle.value = title
  }
})

watch(() => analysisStore.insightSubtitle, (subtitle) => {
  if (subtitle && selectedDataType.value === 'contrast' && dataSource.value === 'workflow') {
    posterSubtitle.value = subtitle
  }
})

// 数据验证函数
const validateData = () => {
  if (!radarChartCanvasRef.value || !debateTimelineCanvasRef.value || !trendChartCanvasRef.value) {
    console.warn('[DataView] ⚠️ Canvas ref 未就绪')
    return false
  }
  if (radarChartData.value.labels.length === 0 || debateTimelineData.value.length === 0 || trendChartData.value.curve.length === 0) {
    console.warn('[DataView] ⚠️ 数据未完整')
    return false
  }
  return true
}

// 带重试的生成函数
const generateWithRetry = async (maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    if (validateData()) {
      return await generateDataViewImages()
    }
    if (i < maxRetries - 1) {
      await new Promise(resolve => setTimeout(resolve, 300))
    }
  }
  console.error('[DataView] ❌ 重试失败')
  return []
}

onMounted(() => {
  // 监听生成事件
  const handleGenerateCards = async () => {
    console.log('[DataView] 🎨 收到生成事件')
    await nextTick()
    
    try {
      const images = await generateWithRetry()
      if (images.length > 0) {
        analysisStore.setDataViewImages(images)
        console.log('[DataView] ✅ 生成成功:', images.length, '张')
      }
    } catch (error) {
      console.error('[DataView] ❌ 生成失败:', error)
    }
  }
  
  window.addEventListener('generate-dataview-cards', handleGenerateCards)
  
  onUnmounted(() => {
    window.removeEventListener('generate-dataview-cards', handleGenerateCards)
  })
  
  console.log('[DataView] 🚀 组件已挂载')
})

</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}
</style>
