<template>
    <div class="view-section animate-fade-in">
        <!-- Header & Filters -->
        <header class="relative bg-white border-b border-slate-100 pt-10 pb-6 px-4">
            <div class="max-w-7xl mx-auto flex flex-col gap-4">
                <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <div
                            class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-semibold">
                            <Flame class="w-3 h-3" /> 热榜选题
                        </div>
                        <h1 class="text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight mt-3">
                            发现热点 · 快速推演 · 一键创作
                        </h1>
                        <p class="text-slate-500 text-sm mt-2">跨平台热度对齐 + 争议识别 + 创作者工具链</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <button @click="refreshTrending({ forceRefresh: true })"
                            class="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-colors text-xs font-bold flex items-center gap-1"
                            :disabled="isLoading">
                            <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': isLoading }" />
                            刷新热榜
                        </button>
                        <button @click="switchTab('home')"
                            class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors text-xs font-bold flex items-center gap-1">
                            <Sparkles class="w-3 h-3" /> 进入推演
                        </button>
                    </div>
                </div>

                <!-- Filter & Search Panel -->
                <div class="glass-card rounded-2xl p-4 shadow-lg">
                    <div class="flex flex-col gap-4">
                        <!-- Platform Filter -->
                        <div class="flex flex-wrap items-center gap-2">
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">平台</span>
                            <button v-for="platform in platformList" :key="platform.id"
                                @click="selectPlatformAndRefresh(platform.id)" :class="[
                                    'px-3 py-1 rounded-full border text-xs font-semibold transition',
                                    selectedPlatform === platform.id
                                        ? 'bg-blue-50 border-blue-300 text-blue-600'
                                        : 'border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600'
                                ]">
                                {{ platform.name }}
                            </button>
                        </div>

                        <!-- Category & Sort & Search -->
                        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                            <!-- Category Filter -->
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">分区</span>
                                <div class="flex flex-wrap gap-2">
                                    <button v-for="cat in categoryList" :key="cat.id" @click="selectedCategory = cat.id"
                                        :class="[
                                            'px-3 py-1 rounded-full text-xs font-semibold transition',
                                            selectedCategory === cat.id
                                                ? 'bg-blue-50 border-blue-300 text-blue-600 border'
                                                : 'border border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600'
                                        ]">
                                        {{ cat.name }}
                                    </button>
                                </div>
                            </div>

                            <!-- Sort & Search -->
                            <div class="flex flex-wrap items-center gap-3">
                                <div class="flex items-center gap-2 text-xs text-slate-500 font-semibold">
                                    <ArrowUpDown class="w-3 h-3" /> 排序
                                </div>
                                <select v-model="sortBy"
                                    class="px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-600 font-semibold outline-none focus:border-blue-400">
                                    <option value="heat">综合热度</option>
                                    <option value="growth">增速</option>
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
            </div>
        </header>

        <!-- Content Section -->
        <section class="py-8 px-4 max-w-7xl mx-auto">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <!-- Topics List -->
                <div class="lg:col-span-7 space-y-4">
                    <div v-if="isLoading" class="flex items-center justify-center py-12">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    </div>
                    <div v-else-if="filteredTopics.length === 0" class="text-center py-12">
                        <AlertCircle class="w-12 h-12 text-slate-300 mx-auto mb-3" />
                        <p class="text-slate-500">暂无数据，点击"刷新热榜"加载数据</p>
                    </div>
                    <div v-for="(topic, idx) in filteredTopics" :key="`${topic.id}-${idx}`">
                        <div @click="selectTopic(topic)" :class="[
                            'glass-card rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg border-l-4',
                            selectedTopic?.id === topic.id
                                ? 'border-l-blue-600 bg-blue-50 shadow-lg'
                                : 'border-l-slate-200 hover:border-l-blue-400'
                        ]">
                            <div class="flex items-start justify-between gap-4">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2 mb-2">
                                        <span
                                            class="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                                            #{{ idx + 1 }}
                                        </span>
                                        <span v-if="topic.platform" class="text-[10px] font-bold text-slate-400">{{
                                            topic.platform }}</span>
                                        <span v-if="topic.category" class="text-[10px] font-bold text-slate-400">{{
                                            topic.category }}</span>
                                    </div>
                                    <h3 class="text-lg font-bold text-slate-800 line-clamp-2">{{ topic.title }}</h3>
                                    <p v-if="topic.description" class="text-sm text-slate-600 mt-1 line-clamp-2">{{
                                        topic.description }}</p>
                                    <div class="flex flex-wrap items-center gap-3 mt-3 text-xs text-slate-500">
                                        <span v-if="topic.source" class="flex items-center gap-1">
                                            <Globe class="w-3 h-3" /> {{ topic.source }}
                                        </span>
                                    </div>
                                </div>
                                <div class="flex flex-col items-end gap-2">
                                    <span class="text-xs font-bold text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
                                        热度 {{ topic.heat_display || '-' }}
                                    </span>
                                    <span v-if="topic.rank" class="text-[10px] font-bold text-slate-400">排名 #{{
                                        topic.rank }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Detail Panel -->
                <div class="lg:col-span-5">
                    <div class="glass-card rounded-2xl p-5 shadow-lg border border-slate-100 sticky top-24">
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="text-lg font-bold text-slate-800">
                                    {{ selectedTopic?.title || '选择话题查看详情' }}
                                </h3>
                                <p class="text-xs text-slate-400 mt-1">跨平台对齐 · 证据列表 · 争议预判</p>
                            </div>
                            <div class="flex items-center gap-2" v-if="selectedTopic">
                                <span class="text-xs font-bold text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
                                    热度 {{ selectedTopic.heat_display || '-' }}
                                </span>
                                <button
                                    class="px-3 py-1 text-xs font-bold text-white bg-blue-600 rounded-full hover:bg-blue-700 transition"
                                    @click="goToSimulation">
                                    一键推演
                                </button>
                            </div>
                        </div>

                        <div v-if="selectedTopic" class="mt-5 space-y-4">
                            <!-- Platform Alignment -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">跨平台对齐</h4>
                                <div
                                    class="text-sm text-slate-700 bg-slate-50 rounded-xl p-3 border border-slate-100 space-y-2">
                                    <div v-if="selectedTopic.platforms_data && selectedTopic.platforms_data.length > 0">
                                        <div v-for="plat in selectedTopic.platforms_data" :key="plat.platform"
                                            class="flex items-center justify-between">
                                            <span class="font-semibold">{{ plat.platform }}</span>
                                            <span class="text-orange-600">热度: {{ plat.hot_value || '-' }}</span>
                                        </div>
                                    </div>
                                    <div v-else class="text-slate-500">{{ selectedTopic.platform || '未指定' }}</div>
                                </div>
                            </div>

                            <!-- Evidence -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">证据列表</h4>
                                <div class="grid gap-2">
                                    <div v-if="selectedTopic.evidence && selectedTopic.evidence.length > 0"
                                        v-for="(ev, i) in selectedTopic.evidence" :key="i"
                                        class="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs text-slate-600">
                                        <p class="font-semibold text-slate-700">{{ ev.platform || 'Platform' }}</p>
                                        <p class="text-[11px] text-slate-500 mt-1">{{ ev.title || '获取中...' }}</p>
                                    </div>
                                    <div v-else
                                        class="p-3 rounded-lg border border-slate-100 bg-slate-50 text-sm text-slate-500">
                                        暂无证据数据
                                    </div>
                                </div>
                            </div>

                            <!-- Conflicts -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">可能冲突点</h4>
                                <ul v-if="selectedTopic.conflicts"
                                    class="list-disc list-inside text-sm text-slate-600 space-y-1">
                                    <li v-for="(conflict, i) in selectedTopic.conflicts" :key="i">{{ conflict }}</li>
                                </ul>
                                <div v-else class="text-sm text-slate-500 text-center py-2">暂无冲突预警</div>
                            </div>
                        </div>
                        <div v-else class="mt-5 text-center py-8 text-slate-400">
                            <AlertCircle class="w-8 h-8 mx-auto mb-2 opacity-50" />
                            <p>暂无选择，请点击左侧热榜卡片。</p>
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
    Flame, RefreshCw, Sparkles, Search, ArrowUpDown, Globe, AlertCircle
} from 'lucide-vue-next'
import { useConfigStore } from '../stores/config'

const emit = defineEmits(['switch-tab'])

const switchTab = (tab) => {
    emit('switch-tab', tab)
}

const configStore = useConfigStore()

// State
const topics = ref([])
const selectedTopic = ref(null)
const isLoading = ref(false)
const selectedPlatform = ref(null) // 单选平台
const selectedCategory = ref('all')
const sortBy = ref('heat')
const searchQuery = ref('')

// Platforms and Categories
const platformList = ref([
    { id: 'all', name: '全榜' },
    { id: 'weibo', name: '微博' },
    { id: 'bilibili', name: 'B站' },
    { id: 'douyin', name: '抖音' },
    { id: 'baidu', name: '百度' },
    { id: 'tieba', name: '贴吧' },
    { id: 'kuaishou', name: '快手' },
    { id: 'zhihu', name: '知乎' }
])

const categoryList = ref([
    { id: 'all', name: '综合' },
    { id: 'society', name: '社会' },
    { id: 'ent', name: '娱乐' },
    { id: 'finance', name: '财经' },
    { id: 'tech', name: '科技' },
    { id: 'intl', name: '国际' }
])

// Computed
const filteredTopics = computed(() => {
    let result = topics.value

    // Filter by category
    if (selectedCategory.value !== 'all') {
        result = result.filter(t => t.category === selectedCategory.value)
    }

    // Filter by search query
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        result = result.filter(
            t => t.title.toLowerCase().includes(q) || (t.description && t.description.toLowerCase().includes(q))
        )
    }

    // Sort
    result.sort((a, b) => {
        if (sortBy.value === 'heat') {
            return (b.heat_score || 0) - (a.heat_score || 0)
        } else if (sortBy.value === 'growth') {
            return (b.growth || 0) - (a.growth || 0)
        } else if (sortBy.value === 'controversy') {
            return (b.controversy || 0) - (a.controversy || 0)
        }
        return 0
    })

    return result
})

// Methods
const selectPlatformAndRefresh = (platformId) => {
    // 如果点击相同的平台，则取消选择
    selectedPlatform.value = selectedPlatform.value === platformId ? null : platformId
    refreshTrending({ forceRefresh: false })
}

const selectTopic = (topic) => {
    selectedTopic.value = topic
}

const goToSimulation = () => {
    if (!selectedTopic.value) return
    try {
        sessionStorage.setItem('hot_topic_draft', JSON.stringify(selectedTopic.value))
    } catch (e) {
        console.warn('failed to cache topic for simulation', e)
    }
    emit('switch-tab', 'home')
}

// 解析热度为数值与展示字符串
const parseHeatValue = (raw) => {
    if (!raw) return { score: 0, display: '-' }
    const text = String(raw).trim()
    // 提取纯数字和小数
    const numMatch = text.match(/([\d,.]+)\s*(亿|万)?/)
    let score = 0
    if (numMatch) {
        const num = parseFloat(numMatch[1].replace(/,/g, '')) || 0
        const unit = numMatch[2] || ''
        if (unit === '亿') score = num * 1e8
        else if (unit === '万') score = num * 1e4
        else score = num
    }
    // 特殊：次播放
    const playMatch = text.match(/([\d,.]+)\s*次播放/)
    if (playMatch) {
        score = parseFloat(playMatch[1].replace(/,/g, '')) || score
    }
    return { score, display: text }
}

const refreshTrending = async ({ forceRefresh = false } = {}) => {
    isLoading.value = true
    try {
        const apiUrl = 'http://127.0.0.1:8000/api'
        // 构建请求体，包含选中的平台
        const requestBody = {
            platforms: selectedPlatform.value ? [selectedPlatform.value] : null,
            force_refresh: forceRefresh
        }
        const response = await fetch(`${apiUrl}/hot-news/collect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        const data = await response.json()

        // 转换 API 响应为视图所需格式
        if (data.news_by_platform) {
            const allNews = []

            for (const [platformName, newsList] of Object.entries(data.news_by_platform)) {
                if (Array.isArray(newsList)) {
                    newsList.forEach((news, idx) => {
                        // 后端返回的字段：title, url, hot_value, rank, source, source_id, category, platform（全榜特有）
                        const topicId = `${news.source_id}-${news.rank}`
                        const heat = parseHeatValue(news.hot_value)
                        
                        // 对于全榜数据，可能包含 platform 字段；其他平台则用 news.source
                        const platformDisplay = news.platform || news.source || '未知平台'

                        allNews.push({
                            id: topicId,
                            title: news.title || `话题 #${idx + 1}`,
                            description: news.description || '',
                            platform_id: news.source_id,
                            platform: platformDisplay,
                            heat_score: heat.score,
                            heat_display: heat.display,
                            rank: news.rank || (idx + 1),
                            category: news.category || 'all',
                            source: news.url ? new URL(news.url).hostname : platformDisplay,
                            url: news.url,
                            growth: Math.floor(Math.random() * 50), // 模拟增速（后续可优化）
                            controversy: Math.floor(Math.random() * 30), // 模拟争议度（后续可优化）
                            evidence: [
                                {
                                    platform: platformDisplay,
                                    title: news.title || `话题证据 #${idx + 1}`
                                }
                            ],
                            conflicts: [],
                            platforms_data: [
                                {
                                    platform: platformDisplay,
                                    hot_value: heat.display
                                }
                            ]
                        })
                    })
                }
            }
            topics.value = allNews
            selectedTopic.value = null
        }
    } catch (error) {
        console.error('Failed to fetch trending:', error)
        alert('加载热榜失败: ' + error.message)
    } finally {
        isLoading.value = false
    }
}

const getPlatformName = (platformId) => {
    const map = {
        'all': '全榜',
        'weibo': '微博',
        'bilibili': 'B站',
        'douyin': '抖音',
        'baidu': '百度',
        'tieba': '贴吧',
        'kuaishou': '快手',
        'zhihu': '知乎'
    }
    return map[platformId] || platformId
}

// Load on mount
onMounted(() => {
    // 初始加载热榜数据
    refreshTrending()
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
