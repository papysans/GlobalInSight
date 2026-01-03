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
                            class="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-colors text-xs font-bold flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                            :disabled="isLoading">
                            <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': isLoading }" />
                            {{ isLoading ? '刷新中...' : '刷新热榜' }}
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
                                            <span :class="[
                                                'leading-none font-black',
                                                idx < 3 ? 'text-sm' : 'text-xs'
                                            ]">{{ idx + 1 }}</span>
                                        </span>
                                        <span v-if="topic.platform && topic.platform !== 'aligned'" class="text-[10px] font-bold text-slate-400">{{
                                            topic.platform }}</span>
                                        <span v-if="topic.category && topic.category !== 'aligned'" class="text-[10px] font-bold text-slate-400">{{
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
                                <p class="text-xs text-slate-400 mt-1">热点演化解读 · 扩散态势 · 分歧观察</p>
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

                            <!-- Evolution Interpretation -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">热点演化解读</h4>
                                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                                    <div v-if="isInterpreting" class="text-slate-500">解读生成中...</div>
                                    <div v-else-if="interpretError" class="text-rose-600">{{ interpretError }}</div>
                                    <div v-else-if="topicInsight">
                                        <div class="flex items-center gap-2 mb-2 flex-wrap">
                                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
                                                生命周期：{{ topicInsight.lifecycle_stage }}
                                            </span>
                                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
                                                Agent：{{ topicInsight.agent_name || 'hotnews_interpretation_agent' }}
                                            </span>
                                            <span v-if="topicInsight.cache_hit"
                                                class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">
                                                缓存命中
                                            </span>
                                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
                                                置信度：{{ Math.round((topicInsight.confidence || 0.6) * 100) }}%
                                            </span>
                                        </div>
                                        <p class="text-sm text-slate-700 whitespace-pre-line">{{ topicInsight.diffusion_summary }}</p>
                                        <div v-if="topicInsight.divergence_points && topicInsight.divergence_points.length" class="mt-3">
                                            <div class="text-xs font-bold text-slate-500 mb-1">分歧点</div>
                                            <ul class="list-disc list-inside text-sm text-slate-600 space-y-1">
                                                <li v-for="(x, i) in topicInsight.divergence_points" :key="`d-${i}`">{{ x }}</li>
                                            </ul>
                                        </div>
                                        <div v-if="topicInsight.watch_points && topicInsight.watch_points.length" class="mt-3">
                                            <div class="text-xs font-bold text-slate-500 mb-1">观察点</div>
                                            <ul class="list-disc list-inside text-sm text-slate-600 space-y-1">
                                                <li v-for="(x, i) in topicInsight.watch_points" :key="`w-${i}`">{{ x }}</li>
                                            </ul>
                                        </div>
                                    </div>
                                    <div v-else class="text-slate-500">点击左侧话题后生成演化解读。</div>
                                </div>
                            </div>

                            <!-- Sources (optional) -->
                            <div>
                                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">来源链接</h4>
                                <div class="grid gap-2">
                                    <div v-if="selectedTopic.evidence && selectedTopic.evidence.length > 0"
                                        v-for="(ev, i) in selectedTopic.evidence.slice(0, 6)" :key="i"
                                        class="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs text-slate-600">
                                        <p class="font-semibold text-slate-700">{{ ev.platform || ev.platform_id || 'Platform' }}</p>
                                        <a v-if="ev.url" class="text-[11px] text-blue-600 hover:underline mt-1 block"
                                            :href="ev.url" target="_blank" rel="noreferrer">
                                            {{ ev.title || '打开链接' }}
                                        </a>
                                        <p v-else class="text-[11px] text-slate-500 mt-1">{{ ev.title || '无链接' }}</p>
                                    </div>
                                    <div v-else
                                        class="p-3 rounded-lg border border-slate-100 bg-slate-50 text-sm text-slate-500">
                                        暂无来源链接
                                    </div>
                                </div>
                            </div>

                            <!-- Trace (optional, placed at the very end) -->
                            <div v-if="topicInsight && topicInsight.trace_steps && topicInsight.trace_steps.length">
                                <details class="rounded-xl border border-slate-100 bg-white/60 p-3">
                                    <summary class="cursor-pointer text-xs font-bold text-slate-500 uppercase tracking-wider">
                                        过程信息（可选）
                                    </summary>
                                    <div class="mt-2 text-sm text-slate-700">
                                        <div class="text-xs font-bold text-slate-500 mb-1">分析链路</div>
                                        <ul class="list-disc list-inside text-sm text-slate-600 space-y-1">
                                            <li v-for="(x, i) in topicInsight.trace_steps" :key="`s-${i}`">{{ x }}</li>
                                        </ul>
                                    </div>
                                </details>
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
const topicInsight = ref(null)
const isInterpreting = ref(false)
const interpretError = ref('')
const isLoading = ref(false)
const selectedPlatform = ref('all') // 单选平台，默认为全榜
const selectedCategory = ref('all')
const sortBy = ref('heat')
const searchQuery = ref('')

// 防抖相关
const debounceTimer = ref(null)
const lastRefreshTime = ref(0)
const DEBOUNCE_DELAY = 1000 // 防抖延迟时间（毫秒），1秒内只执行一次

// Platforms and Categories
const platformList = ref([
    { id: 'all', name: '全榜' },
    { id: 'weibo', name: '微博' },
    { id: 'bilibili', name: 'B站' },
    { id: 'douyin', name: '抖音' },
    { id: 'baidu', name: '百度' },
    { id: 'tieba', name: '贴吧' },
    { id: 'kuaishou', name: '快手' },
    { id: 'zhihu', name: '知乎' },
    { id: 'hn', name: 'Hacker News' }
])

const categoryList = ref([
    { id: 'all', name: '综合' },
    { id: 'ent', name: '娱乐' },
    { id: 'society', name: '社会' },
    { id: 'tech', name: '科技' },
    { id: 'intl', name: '国际' },
    { id: 'finance', name: '财经' }
])

// 关键词分类规则（基于实际新闻标题分析）
const categoryKeywords = {
    ent: [
        // 娱乐明星/人物
        '明星', '演员', '歌手', '艺人', '偶像', '网红', '博主', 'up主', '主播',
        '何同学', '潘晓婷', '白冰', '梁立', '羊驼',
        // 娱乐内容
        '电影', '电视剧', '综艺', '音乐', '歌曲', 'MV', '演唱会', '舞台', '表演',
        '钢琴', '台球', '游戏', '电竞', '直播', '短视频', 'vlog', '测评', '开箱',
        '烟花', '跨年', '过年', '春节', '春晚', '节日', '庆祝',
        // 娱乐标签
        '#', 'bgm', '配乐', '跳舞', '舞蹈', '搞笑', '段子', '梗', '表情包'
    ],
    society: [
        // 社会事件
        '交警', '警察', '公安', '民警', '执法', '治安', '安全', '事故', '车祸', '交通',
        '教育', '学校', '学生', '老师', '考试', '高考', '中考', '大学', '毕业',
        '医疗', '医院', '医生', '健康', '疫情', '疫苗', '治疗', '手术',
        '民生', '政策', '法规', '法律', '法院', '判决', '起诉', '维权',
        '社会', '民生', '生活', '日常', '百姓', '群众', '市民',
        '过年', '回家', '回村', '春运', '假期', '放假',
        '赶海', '渔民', '农民', '农村', '乡村', '城市'
    ],
    tech: [
        // 科技产品
        'AI', '人工智能', 'ChatGPT', 'GPT', '大模型', '深度学习', '机器学习',
        '芯片', '半导体', 'CPU', 'GPU', '处理器',
        '手机', 'iPhone', '华为', '小米', 'OPPO', 'vivo', '三星',
        '电脑', '笔记本', '平板', 'iPad',
        // 科技公司
        '苹果', '微软', '谷歌', 'Meta', 'OpenAI', 'DeepSeek', '字节', '腾讯', '阿里', '百度',
        // 科技概念
        '算法', '代码', '编程', '开发', '软件', '应用', 'APP', '系统', '操作系统',
        '互联网', '网络', '5G', '6G', '物联网', '区块链', '加密货币', '比特币',
        '开源', 'GitHub', '技术', '创新', '研发', '科技', '数字化', '智能化',
        'Hacker News', 'HN', '程序员', '工程师'
    ],
    intl: [
        // 国际人物
        '特朗普', '拜登', '普京', '马克龙', '默克尔', '安倍', '金正恩',
        // 国际地区
        '美国', '中国', '俄罗斯', '英国', '法国', '德国', '日本', '韩国', '朝鲜',
        '欧洲', '欧盟', '北约', '联合国', '世卫', 'WTO',
        '委内瑞拉', '伊朗', '以色列', '巴勒斯坦', '乌克兰', '俄罗斯',
        // 国际事件
        '外交', '贸易', '制裁', '战争', '冲突', '和平', '谈判', '协议',
        '总统', '总理', '首相', '领导人', '政府', '议会', '选举', '投票',
        '国际', '全球', '世界', '海外', '境外'
    ],
    finance: [
        // 金融概念
        '股价', '股市', '股票', 'A股', '港股', '美股', '纳斯达克', '道琼斯',
        '投资', '基金', '理财', '银行', '贷款', '利率', '汇率', '货币',
        '经济', 'GDP', '通胀', '通缩', '消费', '消费', '市场', '交易',
        '公司', '企业', '上市', 'IPO', '财报', '业绩', '利润', '营收',
        '房地产', '房价', '楼市', '买房', '卖房',
        '油价', '能源', '石油', '天然气', '电力',
        '财经', '金融', '商业', '创业', '融资'
    ]
}

// 根据标题自动分类（基于关键词匹配）
const classifyTopic = (title) => {
    if (!title || typeof title !== 'string') return 'all'
    
    const titleLower = title.toLowerCase()
    const titleText = titleLower.replace(/[#@]/g, ' ') // 移除标签符号，避免误匹配
    
    // 计算每个分类的匹配分数（支持部分匹配）
    const scores = {}
    for (const [cat, keywords] of Object.entries(categoryKeywords)) {
        let score = 0
        for (const keyword of keywords) {
            const keywordLower = keyword.toLowerCase()
            // 完全匹配权重更高
            if (titleText.includes(keywordLower)) {
                // 如果关键词较长（>=3字符），权重更高
                score += keywordLower.length >= 3 ? 2 : 1
            }
        }
        if (score > 0) {
            scores[cat] = score
        }
    }
    
    // 返回得分最高的分类，如果都没有匹配或得分太低则返回 'all'
    if (Object.keys(scores).length === 0) {
        return 'all'
    }
    
    const maxScore = Math.max(...Object.values(scores))
    // 如果最高分太低（< 2），可能是误匹配，返回 'all'
    if (maxScore < 2) {
        return 'all'
    }
    
    const topCategory = Object.keys(scores).find(cat => scores[cat] === maxScore)
    return topCategory || 'all'
}

// Computed
const filteredTopics = computed(() => {
    let result = topics.value

    // Local platform filter (avoid re-requesting backend when switching tabs)
    if (selectedPlatform.value !== 'all') {
        const pid = selectedPlatform.value
        result = result.filter(t => {
            const ev = Array.isArray(t.evidence) ? t.evidence : []
            const pd = Array.isArray(t.platforms_data) ? t.platforms_data : []
            return ev.some(x => x && x.platform_id === pid) || pd.some(x => x && x.platform_id === pid)
        })
    }

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
    // 直接设置平台，'all' 表示全榜
    selectedPlatform.value = platformId
    // 切换平台不再触发后端采集，直接本地过滤
}

const selectTopic = (topic) => {
    selectedTopic.value = topic
    topicInsight.value = null
    interpretError.value = ''
    // 点击后请求“演化解读卡”
    fetchTopicInsight(topic)
}

const fetchTopicInsight = async (topic) => {
    if (!topic) return
    isInterpreting.value = true
    interpretError.value = ''
    try {
        const apiUrl = 'http://127.0.0.1:8000/api'
        const body = {
            id: topic.id,
            title: topic.title,
            collection_time: topic.timestamp,
            hot_value: topic.heat_display,
            hot_score: topic.heat_score,
            growth: topic.growth,
            hot_score_delta: topic.hot_score_delta,
            is_new: topic.is_new,
            platforms_data: topic.platforms_data || [],
            evidence: topic.evidence || [],
        }
        const resp = await fetch(`${apiUrl}/hot-news/interpret`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        })
        const data = await resp.json()
        if (!data || data.success === false) {
            interpretError.value = (data && data.diffusion_summary) ? data.diffusion_summary : '解读生成失败'
            topicInsight.value = null
        } else {
            topicInsight.value = data
        }
    } catch (e) {
        interpretError.value = e?.message || '解读生成失败'
        topicInsight.value = null
    } finally {
        isInterpreting.value = false
    }
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

// 实际的刷新函数（内部实现）
const _refreshTrending = async ({ forceRefresh = false } = {}) => {
    // 如果正在加载中，直接返回
    if (isLoading.value) {
        console.log('⏸️ 刷新请求已在进行中，跳过本次请求')
        return
    }

    isLoading.value = true
    lastRefreshTime.value = Date.now()
    
    try {
        const apiUrl = 'http://127.0.0.1:8000/api'
        // 构建请求体，包含选中的平台
        const requestBody = {
            // 永远取全量（含对齐信息），前端本地按平台过滤
            platforms: ['all'],
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

        // 使用后端返回的对齐数据（news_list）
        if (data.news_list && Array.isArray(data.news_list)) {
            const allNews = data.news_list.map((news, idx) => {
                const topicId = news.id || `${news.source_id}-${news.rank}`
                const heatDisplay = news.hot_value || ''
                const heat = parseHeatValue(heatDisplay)
                const platformDisplay = news.platform || '多平台对齐'
                const evidenceList = Array.isArray(news.evidence) ? news.evidence : []
                const platformsData = Array.isArray(news.platforms_data) ? news.platforms_data : []
                const conflicts = Array.isArray(news.conflicts) ? news.conflicts : []
                const keywords = Array.isArray(news.keywords) ? news.keywords : []
                const primaryUrl = (evidenceList[0] && evidenceList[0].url) ? evidenceList[0].url : (news.url || '')
                let sourceHost = platformDisplay
                try {
                    sourceHost = primaryUrl ? new URL(primaryUrl).hostname : platformDisplay
                } catch (e) {
                    sourceHost = platformDisplay
                }

                const newsTitle = news.title || `话题 #${idx + 1}`
                // 使用关键词匹配自动分类
                const autoCategory = classifyTopic(newsTitle)
                
                return {
                    id: topicId,
                    title: newsTitle,
                    description: keywords.length ? `关键词：${keywords.slice(0, 6).join(' / ')}` : '',
                    platform_id: news.source_id || 'aligned',
                    platform: platformDisplay,
                    heat_score: Number.isFinite(news.hot_score) ? news.hot_score : heat.score,
                    heat_display: heatDisplay || heat.display,
                    rank: news.rank || (idx + 1),
                    category: autoCategory, // 使用自动分类结果
                    source: sourceHost,
                    url: primaryUrl,
                    growth: typeof news.growth === 'number' ? news.growth : 0,
                    controversy: typeof news.controversy === 'number' ? news.controversy : 0,
                    hot_score_delta: typeof news.hot_score_delta === 'number' ? news.hot_score_delta : 0,
                    is_new: Boolean(news.is_new),
                    keywords,
                    evidence: evidenceList,
                    conflicts,
                    platforms_data: platformsData,
                    timestamp: news.timestamp || data.collection_time
                }
            })

            topics.value = allNews
            selectedTopic.value = null
            topicInsight.value = null
        }
    } catch (error) {
        console.error('Failed to fetch trending:', error)
        alert('加载热榜失败: ' + error.message)
    } finally {
        isLoading.value = false
    }
}

// 带防抖的刷新函数（对外暴露）
const refreshTrending = ({ forceRefresh = false } = {}) => {
    // 如果正在加载中，直接返回
    if (isLoading.value) {
        console.log('⏸️ 刷新请求已在进行中，跳过本次请求')
        return
    }

    // 清除之前的定时器
    if (debounceTimer.value) {
        clearTimeout(debounceTimer.value)
        debounceTimer.value = null
    }

    const now = Date.now()
    const timeSinceLastRefresh = now - lastRefreshTime.value

    // 如果距离上次刷新时间超过防抖延迟，立即执行
    if (timeSinceLastRefresh >= DEBOUNCE_DELAY) {
        _refreshTrending({ forceRefresh })
    } else {
        // 否则延迟执行，等待防抖时间
        const remainingTime = DEBOUNCE_DELAY - timeSinceLastRefresh
        console.log(`⏳ 防抖中，将在 ${remainingTime}ms 后执行刷新`)
        debounceTimer.value = setTimeout(() => {
            _refreshTrending({ forceRefresh })
            debounceTimer.value = null
        }, remainingTime)
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
        'zhihu': '知乎',
        'hn': 'Hacker News'
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

/* 排序标签样式增强 */
.scale-102 {
    transform: scale(1.02);
}

/* 前3名标签的微妙闪烁动画 */
@keyframes rankPulse {
    0%, 100% {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    50% {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
}

/* 为前3名添加微妙的脉冲效果（可选，如果觉得太花哨可以去掉） */
</style>
