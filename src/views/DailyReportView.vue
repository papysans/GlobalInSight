<template>
  <div class="view-section animate-fade-in">
    <!-- Header -->
    <header class="relative bg-white border-b border-slate-100 pt-10 pb-6 px-4">
      <div class="max-w-7xl mx-auto flex flex-col gap-4">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-semibold">
              <FileText class="w-3 h-3" /> 每日速报
            </div>
            <h1 class="text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight mt-3">
              每日股市速报
            </h1>
            <p class="text-slate-500 text-sm mt-2">{{ todayDateStr }} · 汇总热点资讯 · 多平台一键发布</p>
            <!-- 定时状态指示 -->
            <div class="flex items-center gap-3 mt-2 text-xs text-slate-400">
              <span class="flex items-center gap-1">
                <Clock class="w-3 h-3" /> 下次自动生成：18:00
              </span>
              <span v-if="store.currentReport" class="px-2 py-0.5 rounded-full bg-green-50 text-green-600">
                已生成
              </span>
              <span v-else class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                未生成
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <!-- 大盘情绪迷你仪表盘 placeholder (Phase 3) -->
            <div class="hidden md:flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
              <BarChart3 class="w-4 h-4 text-slate-400" />
              <span>大盘情绪</span>
              <span class="font-bold text-slate-700">--</span>
            </div>
            <button @click="handleGenerate"
              class="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-colors text-xs font-bold flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="store.isGenerating">
              <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': store.isGenerating }" />
              {{ store.isGenerating ? '生成中...' : '手动生成速报' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Content Section -->
    <section class="py-8 px-4 max-w-7xl mx-auto space-y-8">
      <!-- Main Grid: Left content + Right preview -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <!-- Left: 速报内容预览 -->
        <div class="lg:col-span-7 space-y-4">
          <!-- 生成中状态 -->
          <div v-if="store.isGenerating" class="glass-card rounded-xl p-8 text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p class="text-sm font-medium text-slate-600">正在生成今日速报...</p>
            <p class="text-xs text-slate-400 mt-1">汇总热点资讯、分析板块异动</p>
          </div>

          <!-- 未生成占位 -->
          <div v-else-if="!store.currentReport" class="glass-card rounded-xl p-8 text-center">
            <AlertCircle class="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p class="text-slate-500 text-sm">今日速报尚未生成</p>
            <button @click="handleGenerate"
              class="mt-4 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-xs font-bold inline-flex items-center gap-1">
              <Sparkles class="w-3 h-3" /> 立即生成
            </button>
          </div>

          <!-- 速报内容卡片 -->
          <template v-else>
            <!-- 情绪概况 -->
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-orange-400">
              <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2 mb-3">
                <BarChart3 class="w-4 h-4 text-orange-500" /> 情绪概况
              </h3>
              <div class="text-sm text-slate-600 leading-relaxed">
                <div class="flex items-center gap-4 mb-2">
                  <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200">
                    <span class="text-xs text-slate-500">综合情绪指数</span>
                    <span class="font-bold text-slate-800">--</span>
                  </div>
                  <span class="text-xs text-slate-400">Phase 3 情绪模块完成后自动注入</span>
                </div>
              </div>
            </div>

            <!-- 大盘概况 -->
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-blue-400">
              <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2 mb-3">
                <TrendingUp class="w-4 h-4 text-blue-500" /> 大盘概况
              </h3>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                <p class="whitespace-pre-line">{{ extractSection(reportBody, '大盘') || '暂无大盘概况数据' }}</p>
              </div>
            </div>

            <!-- 板块异动 -->
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-emerald-400">
              <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2 mb-3">
                <Layers class="w-4 h-4 text-emerald-500" /> 板块异动
              </h3>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                <p class="whitespace-pre-line">{{ extractSection(reportBody, '板块') || '暂无板块异动数据' }}</p>
              </div>
            </div>

            <!-- 热点事件解读 -->
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-purple-400">
              <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2 mb-3">
                <Zap class="w-4 h-4 text-purple-500" /> 热点事件解读
              </h3>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                <p class="whitespace-pre-line">{{ extractSection(reportBody, '热点') || reportBody || '暂无热点事件数据' }}</p>
              </div>
            </div>
          </template>
        </div>

        <!-- Right: 多平台预览区 -->
        <div class="lg:col-span-5">
          <div class="glass-card rounded-2xl p-5 shadow-lg border border-slate-100 sticky top-24">
            <PlatformPreview
              :platform-contents="store.platformContents"
              :selected-platform="store.selectedPlatform"
              :is-editing="store.isEditing"
              :editable-content="store.editableContent"
              @update:selected-platform="store.switchPlatform"
              @start-editing="store.startEditing()"
              @update-content="handleUpdateContent"
            />
          </div>
        </div>
      </div>

      <!-- 平台发布区 -->
      <div v-if="store.currentReport" class="glass-card rounded-xl p-6 shadow-lg border-t-4 border-t-emerald-500">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2">
            <Upload class="w-4 h-4 text-emerald-600" /> 平台发布
          </h3>
          <button @click="handlePublishAll"
            :disabled="store.isPublishing"
            class="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors text-xs font-bold flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
            <Send class="w-3 h-3" />
            {{ store.isPublishing ? '发布中...' : '一键发布全平台' }}
          </button>
        </div>

        <!-- 各平台发布状态卡片 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="p in platformList" :key="p.id"
            class="rounded-lg border p-3 text-center transition-all"
            :class="platformStatusClass(p.id)">
            <div class="text-lg mb-1">{{ p.icon }}</div>
            <div class="text-xs font-bold text-slate-700">{{ p.name }}</div>
            <div class="text-[10px] mt-1" :class="platformStatusTextClass(p.id)">
              {{ platformStatusLabel(p.id) }}
            </div>
            <div class="mt-2 flex flex-col gap-1">
              <!-- 小红书：自动发布 -->
              <button v-if="p.id === 'xhs' && store.platformStatuses[p.id] === 'failed'"
                @click="handleRetryPlatform(p.id)"
                class="px-2 py-1 text-[10px] font-bold rounded bg-red-50 text-red-600 hover:bg-red-100 transition-colors">
                重试
              </button>
              <!-- 非小红书：复制到剪贴板 -->
              <button v-if="p.id !== 'xhs'"
                @click="copyPlatformContent(p.id)"
                class="px-2 py-1 text-[10px] font-bold rounded bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors flex items-center justify-center gap-1">
                <Copy class="w-2.5 h-2.5" />
                {{ copiedPlatform === p.id ? '已复制' : '复制到剪贴板' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史速报列表 -->
      <div class="flex flex-col gap-2">
        <div class="flex items-center justify-between px-1">
          <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Clock class="w-5 h-5 text-slate-500" /> 历史速报
          </h2>
          <button @click="loadHistory" class="text-xs text-blue-600 hover:text-blue-700 font-medium">
            刷新
          </button>
        </div>

        <div v-if="store.reportHistory.length === 0"
          class="glass-card rounded-xl p-6 text-center text-slate-400 text-sm">
          暂无历史速报记录
        </div>
        <div v-else class="space-y-2">
          <div v-for="item in store.reportHistory" :key="item.id"
            class="glass-card rounded-xl p-4 cursor-pointer hover:shadow-md transition-all border-l-4 border-l-slate-200 hover:border-l-blue-400"
            @click="toggleHistoryItem(item.id)">
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-bold text-slate-800 truncate">{{ item.title || '每日速报' }}</h4>
                <p class="text-xs text-slate-400 mt-1">{{ formatTime(item.created_at) }}</p>
              </div>
              <ChevronDown class="w-4 h-4 text-slate-400 flex-shrink-0 transition-transform"
                :class="{ 'rotate-180': expandedHistoryId === item.id }" />
            </div>
            <!-- 展开内容 -->
            <div v-if="expandedHistoryId === item.id" class="mt-3 pt-3 border-t border-slate-100">
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                <p class="whitespace-pre-line line-clamp-6">{{ item.body || '暂无内容' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  FileText, Clock, RefreshCw, BarChart3, AlertCircle, Sparkles,
  TrendingUp, Layers, Zap, Upload, Send, Copy, ChevronDown
} from 'lucide-vue-next'
import { useDailyReportStore } from '../stores/dailyReport'
import PlatformPreview from '../components/PlatformPreview.vue'

const store = useDailyReportStore()

// Local state
const expandedHistoryId = ref(null)
const copiedPlatform = ref(null)

// Platform list for publish status cards
const platformList = [
  { id: 'xhs', name: '小红书', icon: '📕' },
  { id: 'weibo', name: '微博', icon: '🔵' },
  { id: 'xueqiu', name: '雪球', icon: '❄️' },
  { id: 'zhihu', name: '知乎', icon: '💡' },
]

// Today's date string
const todayDateStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

// Report body from current report
const reportBody = computed(() => {
  return store.currentReport?.body || store.currentReport?.content || ''
})

// Extract section from report body by keyword
function extractSection(text, keyword) {
  if (!text) return ''
  const lines = text.split('\n')
  let capturing = false
  const result = []
  for (const line of lines) {
    if (line.includes(keyword)) {
      capturing = true
      continue
    }
    if (capturing) {
      // Stop at next section header (lines starting with # or 【)
      if ((line.startsWith('#') || line.startsWith('【')) && result.length > 0) break
      result.push(line)
    }
  }
  return result.join('\n').trim()
}

// Format time
function formatTime(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    if (isNaN(d.getTime())) return isoStr
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hour = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hour}:${min}`
  } catch {
    return isoStr
  }
}

// Platform status helpers
function platformStatusClass(platformId) {
  const status = store.platformStatuses[platformId]
  if (status === 'published') return 'border-green-200 bg-green-50'
  if (status === 'publishing') return 'border-blue-200 bg-blue-50'
  if (status === 'failed') return 'border-red-200 bg-red-50'
  return 'border-slate-200 bg-slate-50'
}

function platformStatusTextClass(platformId) {
  const status = store.platformStatuses[platformId]
  if (status === 'published') return 'text-green-600'
  if (status === 'publishing') return 'text-blue-600'
  if (status === 'failed') return 'text-red-600'
  return 'text-slate-400'
}

function platformStatusLabel(platformId) {
  const status = store.platformStatuses[platformId]
  const map = { idle: '待发布', publishing: '发布中...', published: '已发布', failed: '发布失败' }
  return map[status] || '待发布'
}

// Actions
async function handleGenerate() {
  try {
    await store.generateReport()
  } catch (err) {
    console.error('Generate report failed:', err)
  }
}

async function handlePublishAll() {
  try {
    await store.publishAllPlatforms()
  } catch (err) {
    console.error('Publish all failed:', err)
  }
}

async function handleRetryPlatform(platformId) {
  try {
    await store.publishToSinglePlatform(null, platformId)
  } catch (err) {
    console.error('Retry publish failed:', err)
  }
}

function handleUpdateContent(platform, updates) {
  store.updateContent(updates)
}

async function copyPlatformContent(platformId) {
  const content = store.platformContents[platformId]
  if (!content) return
  const text = [content.title, content.body].filter(Boolean).join('\n\n')
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copiedPlatform.value = platformId
    setTimeout(() => { copiedPlatform.value = null }, 2000)
  } catch (e) {
    console.warn('Copy failed', e)
  }
}

function toggleHistoryItem(id) {
  expandedHistoryId.value = expandedHistoryId.value === id ? null : id
}

async function loadHistory() {
  await store.fetchHistory()
}

// Load on mount
onMounted(async () => {
  await store.fetchLatest()
  await store.fetchHistory()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
