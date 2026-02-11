<template>
    <div class="view-section animate-fade-in">
        <!-- Header & Filters -->
        <header class="relative bg-white border-b border-slate-100 pt-10 pb-6 px-4">
            <div class="max-w-7xl mx-auto flex flex-col gap-4">
                <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <div
                            class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-semibold">
                            <TrendingUp class="w-3 h-3" /> 股票热榜
                        </div>
                        <h1 class="text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight mt-3">
                            股票热点 · 行情推演 · 一键创作
                        </h1>
                        <p class="text-slate-500 text-sm mt-2">多源聚类 · 跨平台热度对齐 · 智能推演</p>
                        <!-- 采集统计 -->
                        <div v-if="stockNewsStore.collectionTime" class="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-400">
                            <span class="flex items-center gap-1">
                                <Clock class="w-3 h-3" /> {{ formatTime(stockNewsStore.collectionTime) }}
                            </span>
                            <span class="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
                                {{ stockNewsStore.clusters.length }} 个话题
                            </span>
                            <span v-if="stockNewsStore.crossPlatformCount > 0" class="px-2 py-0.5 rounded-full bg-orange-50 text-orange-600">
                                {{ stockNewsStore.crossPlatformCount }} 个跨平台
                            </span>
                            <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                                {{ stockNewsStore.rawCount }} 条原始数据
                            </span>
                            <span v-if="stockNewsStore.fromCache" class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                                缓存
                            </span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <SentimentGauge
                            v-if="sentimentStore.marketIndex"
                            :index-value="sentimentStore.marketIndex.index_value ?? 50"
                            :label="sentimentStore.marketIndex.label || ''"
                            size="full"
                        />
                        <div v-else class="hidden md:flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
                            <BarChart3 class="w-4 h-4 text-slate-400" />
                            <span>大盘情绪</span>
                            <span class="font-bold text-slate-700">--</span>
                        </div>
                        <button @click="handleRefresh"
                            class="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-colors text-xs font-bold flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                            :disabled="stockNewsStore.loading">
                            <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': stockNewsStore.loading }" />
                            {{ stockNewsStore.loading ? '刷新中...' : '刷新热榜' }}
                        </button>
                        <button @click="goToAnalysis"
                            class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-xs font-bold flex items-center gap-1">
                            <Sparkles class="w-3 h-3" /> 进入推演
                        </button>
                    </div>
                </div>

                <!-- Filter & Search Panel -->
                <div class="glass-card rounded-2xl p-4 shadow-lg">
                    <div class="flex flex-col gap-4">
                        <!-- Source Platform Filter -->
                        <div class="flex flex-wrap items-center gap-2">
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">数据源</span>
                            <button v-for="src in sourceList" :key="src.id"
                                @click="stockNewsStore.selectedSource = src.id" :class="[
                                    'px-3 py-1 rounded-full border text-xs font-semibold transition',
                                    stockNewsStore.selectedSource === src.id
                                        ? 'bg-blue-50 border-blue-300 text-blue-600'
                                        : 'border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600'
                                ]">
                                {{ src.name }}
                            </button>
                        </div>

                        <!-- Sort & Search -->
                        <div class="flex flex-wrap items-center gap-3">
                            <div class="flex items-center gap-2 text-xs text-slate-500 font-semibold">
                                <ArrowUpDown class="w-3 h-3" /> 排序
                            </div>
                            <select v-model="sortBy"
                                class="px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-600 font-semibold outline-none focus:border-blue-400">
                                <option value="heat">热度</option>
                                <option value="platforms">平台数</option>
                                <option value="controversy">争议度</option>
                            </select>

                            <div class="relative w-full sm:w-56">
                                <Search class="w-3 h-3 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input v-model="searchQuery" type="text" placeholder="搜索话题关键词"
                                    class="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg text-slate-600 outline-none focus:border-blue-400" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Content Section -->
        <section class="py-8 px-4 max-w-7xl mx-auto">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <!-- Cluster List -->
                <div class="lg:col-span-7 space-y-4">
                    <div v-if="stockNewsStore.loading" class="flex items-center justify-center py-12">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    </div>
                    <div v-else-if="displayedClusters.length === 0" class="text-center py-12">
                        <AlertCircle class="w-12 h-12 text-slate-300 mx-auto mb-3" />
                        <p class="text-slate-500">暂无数据，点击"刷新热榜"加载数据</p>
                    </div>
                    <div v-for="(item, idx) in displayedClusters" :key="item.id">
                        <div @click="selectItem(item)" :class="[
                            'glass-card rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg border-l-4',
                            stockNewsStore.selectedTopic?.id === item.id
                                ? 'border-l-blue-600 bg-blue-50 shadow-lg'
                                : 'border-l-slate-200 hover:border-l-blue-400'
                        ]">
                            <div class="flex items-start justify-between gap-4">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2 mb-2 flex-wrap">
                                        <!-- Rank Badge -->
                                        <span :class="[
                                            'inline-flex items-center justify-center font-black rounded-lg px-2.5 py-1 shadow-sm transition-all duration-200 hover:scale-105',
                                            idx === 0
                                                ? 'bg-gradient-to-br from-amber-400 via-orange-500 to-amber-600 text-white border-2 border-amber-300 scale-[1.05] shadow-md shadow-amber-200/50'
                                                : idx === 1
                                                ? 'bg-gradient-to-br from-slate-300 via-slate-400 to-slate-500 text-white border-2 border-slate-200 scale-[1.02] shadow-md shadow-slate-200/50'
                                                : idx === 2
                                                ? 'bg-gradient-to-br from-amber-200 via-orange-200 to-amber-300 text-orange-900 border-2 border-amber-100 shadow-sm'
                                                : 'bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-100 text-blue-700 border border-blue-200'
                                        ]">
                                            <span class="text-[10px] opacity-90 mr-0.5 font-bold">#</span>
                                            <span :class="['leading-none font-black', idx < 3 ? 'text-sm' : 'text-xs']">{{ idx + 1 }}</span>
                                        </span>
                                        <!-- Platform count badge: 只在多平台时显示 -->
                                        <span v-if="item.platform_count > 1" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-200">
                                            {{ item.platform_count }}平台热议
                                        </span>
                                        <!-- New badge -->
                                        <span v-if="item.is_new" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-200">
                                            NEW
                                        </span>
                                        <!-- Growth badge -->
                                        <span v-if="item.growth > 50" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-red-50 text-red-600 border border-red-200">
                                            🔥 +{{ item.growth }}%
                                        </span>
                                        <span v-else-if="item.growth < -30" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200">
                                            📉 {{ item.growth }}%
                                        </span>
                                        <!-- Controversy badge -->
                                        <span v-if="item.controversy > 30" class="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-yellow-50 text-yellow-700 border border-yellow-200">
                                            ⚡ 争议
                                        </span>
                                    </div>
                                    <h3 class="text-lg font-bold text-slate-800 line-clamp-2">{{ item.title }}</h3>
                                    <p v-if="item.summary && item.summary !== item.title && !item.title.includes(item.summary)" class="text-sm text-slate-600 mt-1 line-clamp-2">{{ item.summary }}</p>
                                    <!-- Evidence preview: show top platforms -->
                                    <div v-if="item.platforms_data && item.platforms_data.length > 1" class="flex flex-wrap gap-2 mt-2">
                                        <span v-for="pd in item.platforms_data.slice(0, 4)" :key="pd.platform_id"
                                            class="text-[10px] px-2 py-0.5 rounded-full bg-slate-50 text-slate-500 border border-slate-100">
                                            {{ pd.platform }} · {{ pd.hot_value || '-' }}
                                        </span>
                                    </div>
                                </div>
                                <div class="flex flex-col items-end gap-2 flex-shrink-0">
                                    <span class="text-xs font-bold text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
                                        热度 {{ item.hot_value || '-' }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Detail Panel -->
                <div class="lg:col-span-5">
                    <div class="glass-card rounded-2xl p-5 shadow-lg border border-slate-100">
                        <div class="flex items-center justify-between">
                            <div class="flex-1 min-w-0">
                                <h3 class="text-lg font-bold text-slate-800 line-clamp-2">
                                    {{ stockNewsStore.selectedTopic?.title || '选择话题查看详情' }}
                                </h3>
                                <p class="text-xs text-slate-400 mt-1">话题详情 · 跨平台数据 · 一键推演</p>
                            </div>
                            <div class="flex items-center gap-2 flex-shrink-0" v-if="stockNewsStore.selectedTopic">
                                <span class="text-xs font-bold text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
                                    热度 {{ stockNewsStore.selectedTopic.hot_value || '-' }}
                                </span>
                                <button
                                    class="px-3 py-1 text-xs font-bold text-white bg-blue-600 rounded-full hover:bg-blue-700 transition"
                                    @click="goToSimulation">
                                    一键推演
                                </button>
                            </div>
                        </div>

                        <div v-if="stockNewsStore.selectedTopic" class="mt-5 space-y-4">
                            <!-- Summary -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">摘要内容</h4>
                                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                                    <p class="whitespace-pre-line">{{ displaySummary }}</p>
                                </div>
                            </div>

                            <!-- Cluster Meta -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">话题信息</h4>
                                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700 space-y-2">
                                    <div class="flex items-center justify-between">
                                        <span class="font-semibold">覆盖平台</span>
                                        <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-orange-50 text-orange-600">
                                            {{ (stockNewsStore.selectedTopic.platform_ids || []).map(pid => platformName(pid)).join(' · ') || '-' }}
                                        </span>
                                    </div>
                                    <div class="flex items-center justify-between">
                                        <span class="font-semibold">热度评分</span>
                                        <span class="font-bold text-orange-600">{{ stockNewsStore.selectedTopic.heat_score }}</span>
                                    </div>
                                    <div v-if="stockNewsStore.selectedTopic.controversy > 0" class="flex items-center justify-between">
                                        <span class="font-semibold">争议度</span>
                                        <span class="font-bold text-yellow-600">{{ stockNewsStore.selectedTopic.controversy }}</span>
                                    </div>
                                    <div v-if="stockNewsStore.selectedTopic.is_new" class="flex items-center justify-between">
                                        <span class="font-semibold">状态</span>
                                        <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-green-50 text-green-600">新话题</span>
                                    </div>
                                    <div v-if="stockNewsStore.selectedTopic.growth !== 0" class="flex items-center justify-between">
                                        <span class="font-semibold">热度变化</span>
                                        <span :class="[
                                            'font-bold',
                                            stockNewsStore.selectedTopic.growth > 0 ? 'text-red-600' : 'text-green-600'
                                        ]">
                                            {{ stockNewsStore.selectedTopic.growth > 0 ? '+' : '' }}{{ stockNewsStore.selectedTopic.growth }}%
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <!-- Controversy reasons -->
                            <div v-if="stockNewsStore.selectedTopic.controversy_reasons && stockNewsStore.selectedTopic.controversy_reasons.length > 0">
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">争议分析</h4>
                                <div class="rounded-xl border border-yellow-100 bg-yellow-50 p-3 text-sm text-yellow-800 space-y-1">
                                    <p v-for="(reason, i) in stockNewsStore.selectedTopic.controversy_reasons" :key="i">
                                        ⚡ {{ reason }}
                                    </p>
                                </div>
                            </div>

                            <!-- Evidence: cross-platform data -->
                            <div v-if="stockNewsStore.selectedTopic.evidence && stockNewsStore.selectedTopic.evidence.length > 0">
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                                    跨平台数据 ({{ stockNewsStore.selectedTopic.evidence.length }})
                                </h4>
                                <div class="space-y-2 max-h-80 overflow-y-auto">
                                    <div v-for="(ev, i) in stockNewsStore.selectedTopic.evidence" :key="i"
                                        class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs">
                                        <div class="flex items-center justify-between mb-1">
                                            <span class="font-bold text-slate-600">{{ ev.platform }}</span>
                                            <span class="text-orange-600 font-semibold">{{ ev.hot_value || '-' }}</span>
                                        </div>
                                        <p class="text-slate-700 line-clamp-2">{{ ev.title }}</p>
                                        <div class="flex items-center justify-between mt-1">
                                            <span v-if="ev.published_time" class="text-slate-400">{{ formatTime(ev.published_time) }}</span>
                                            <a v-if="ev.url" :href="ev.url" target="_blank" rel="noreferrer"
                                                class="text-blue-500 hover:text-blue-700 hover:underline flex items-center gap-1"
                                                @click.stop>
                                                <ExternalLink class="w-3 h-3" /> 原文
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 个股情绪指数 -->
                            <div v-if="selectedStockSentiment">
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">个股情绪指数</h4>
                                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3">
                                    <div class="flex items-center justify-center mb-3">
                                        <SentimentGauge
                                            :index-value="selectedStockSentiment.index_value ?? 50"
                                            :label="selectedStockSentiment.label || ''"
                                            size="mini"
                                        />
                                    </div>
                                    <SentimentChart
                                        v-if="selectedStockHistory.length > 0"
                                        :history-data="selectedStockHistory"
                                        :stock-code="selectedStockCode"
                                        :show-sub-scores="true"
                                    />
                                    <p v-else class="text-center text-xs text-slate-400 py-2">暂无历史趋势数据</p>
                                </div>
                            </div>
                        </div>
                        <div v-else class="mt-5 text-center py-8 text-slate-400">
                            <AlertCircle class="w-8 h-8 mx-auto mb-2 opacity-50" />
                            <p>暂无选择，请点击左侧话题卡片。</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
    TrendingUp, RefreshCw, Sparkles, Search, ArrowUpDown, AlertCircle,
    Clock, ExternalLink, BarChart3
} from 'lucide-vue-next'
import { useStockNewsStore } from '../stores/stockNews'
import { useSentimentStore } from '../stores/sentiment'
import { useRouter } from 'vue-router'
import SentimentGauge from '../components/SentimentGauge.vue'
import SentimentChart from '../components/SentimentChart.vue'

const router = useRouter()
const stockNewsStore = useStockNewsStore()
const sentimentStore = useSentimentStore()

const sortBy = ref('heat')
const searchQuery = ref('')

// 详情面板摘要：和标题一样就不显示
const displaySummary = computed(() => {
    const t = stockNewsStore.selectedTopic
    if (!t) return '暂无摘要'
    if (!t.summary || t.summary === t.title || t.title.includes(t.summary)) return '暂无额外摘要'
    return t.summary
})

// Platform name mapping
const platformNameMap = {
    akshare: 'AKShare',
    sina: '新浪财经',
    '10jqka': '同花顺',
    xueqiu: '雪球',
}

function platformName(pid) {
    return platformNameMap[pid] || pid
}

// Sentiment: extract stock code from selected topic
const selectedStockCode = computed(() => {
    const topic = stockNewsStore.selectedTopic
    if (!topic) return null
    if (topic.stock_code) return topic.stock_code
    const match = (topic.title || '').match(/\b([036]\d{5})\b/)
    return match ? match[1] : null
})

const selectedStockSentiment = computed(() => {
    const code = selectedStockCode.value
    if (!code) return null
    return sentimentStore.stockIndices[code] || null
})

const selectedStockHistory = computed(() => {
    const code = selectedStockCode.value
    if (!code) return []
    return sentimentStore.stockHistory[code] || []
})

// Source list
const sourceList = computed(() => {
    const sources = [{ id: 'all', name: '全部' }]
    for (const s of stockNewsStore.availableSources) {
        sources.push({ id: s, name: platformName(s) })
    }
    return sources
})

// Filtered + sorted clusters
const displayedClusters = computed(() => {
    let items = stockNewsStore.filteredClusters.slice()

    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        items = items.filter(c =>
            c.title.toLowerCase().includes(q) ||
            (c.summary && c.summary.toLowerCase().includes(q))
        )
    }

    items.sort((a, b) => {
        if (sortBy.value === 'heat') return (b.heat_score || 0) - (a.heat_score || 0)
        if (sortBy.value === 'platforms') return (b.platform_count || 1) - (a.platform_count || 1)
        if (sortBy.value === 'controversy') return (b.controversy || 0) - (a.controversy || 0)
        return 0
    })

    return items
})

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

function selectItem(item) {
    stockNewsStore.selectTopic(item)
}

function handleRefresh() {
    stockNewsStore.fetchNews(true)
}

function goToAnalysis() {
    router.push('/analysis')
}

function goToSimulation() {
    if (!stockNewsStore.selectedTopic) return
    try {
        sessionStorage.setItem('stock_topic_draft', JSON.stringify(stockNewsStore.selectedTopic))
    } catch (e) {
        console.warn('failed to cache topic for simulation', e)
    }
    router.push('/analysis')
}

onMounted(() => {
    if (stockNewsStore.clusters.length === 0) {
        stockNewsStore.fetchNews()
    }
    sentimentStore.fetchMarketIndex()
})

watch(selectedStockCode, async (code) => {
    if (code) {
        await sentimentStore.fetchStockIndex(code)
        await sentimentStore.fetchHistory(code, 30)
    }
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
