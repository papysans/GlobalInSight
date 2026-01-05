<template>
  <div class="view-section animate-fade-in py-12 px-4">
    <div class="max-w-3xl mx-auto space-y-6">

      <!-- 热榜配置 -->
      <!-- <div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex items-center gap-2">
          <Flame class="w-5 h-5 text-orange-600" />
          <h2 class="font-bold text-slate-800">热榜数据源配置</h2>
        </div>
        <div class="p-6 md:p-8 space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-bold text-slate-700">启用热榜功能</h3>
              <p class="text-xs text-slate-500 mt-1">开启后，系统将定期收集热点话题数据</p>
            </div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="hotNewsConfig.enabled" type="checkbox" @change="saveHotNewsConfig"
                class="rounded border-slate-300 text-orange-600 focus:ring-orange-500" />
              <span class="text-sm font-semibold text-slate-600">{{ hotNewsConfig.enabled ? '已启用' : '已禁用' }}</span>
            </label>
          </div>

          <div>
            <h3 class="text-sm font-bold text-slate-700 mb-3">平台数据源选择</h3>
            <p class="text-xs text-slate-500 mb-4">不选择则表示收集所有平台的数据</p>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
              <label v-for="platform in hotPlatforms" :key="platform.id"
                class="flex items-center space-x-2 p-3 rounded-lg border-2 cursor-pointer transition-all hover:bg-orange-50"
                :class="hotNewsConfig.platform_sources.includes(platform.id)
                  ? 'border-orange-500 bg-orange-50'
                  : 'border-slate-200 bg-white'">
                <input type="checkbox" :value="platform.id"
                  :checked="hotNewsConfig.platform_sources.includes(platform.id)"
                  @change="(e) => toggleHotPlatform(platform.id, e.target.checked)"
                  class="rounded border-slate-300 text-orange-600 focus:ring-orange-500" />
                <span class="text-sm font-medium text-slate-700">{{ platform.name }}</span>
              </label>
            </div>
            <div class="mt-3 text-xs text-slate-400">
              <p>已选择: {{ hotNewsConfig.platform_sources.length === 0 ? '全部平台（默认）' :
                hotNewsConfig.platform_sources.join('、') }}</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-bold text-slate-700 mb-2">更新频率</label>
              <div class="flex items-center gap-2">
                <input v-model.number="hotNewsConfig.fetch_interval_hours" type="number" min="1" max="24"
                  class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-orange-400"
                  @change="saveHotNewsConfig" />
                <span class="text-sm text-slate-600 whitespace-nowrap">小时/次</span>
              </div>
              <p class="text-xs text-slate-400 mt-1">系统将每隔指定时间自动收集一次热榜数据</p>
            </div>

            <div>
              <label class="block text-sm font-bold text-slate-700 mb-2">数据缓存时间</label>
              <div class="flex items-center gap-2">
                <input v-model.number="hotNewsConfig.cache_ttl_minutes" type="number" min="5" max="480"
                  class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-orange-400"
                  @change="saveHotNewsConfig" />
                <span class="text-sm text-slate-600 whitespace-nowrap">分钟</span>
              </div>
              <p class="text-xs text-slate-400 mt-1">同一数据在此时间内不会重复收集</p>
            </div>
          </div>

          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2">每平台最大条数</label>
            <input v-model.number="hotNewsConfig.max_items_per_platform" type="number" min="10" max="500"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-orange-400"
              @change="saveHotNewsConfig" />
            <p class="text-xs text-slate-400 mt-1">每个平台每次收集的最大话题条数</p>
          </div>

          <div v-if="hotNewsConfigSaved"
            class="p-3 rounded-lg bg-green-50 border border-green-200 text-xs text-green-700 flex items-center gap-2">
            <Check class="w-4 h-4" />
            <span>热榜配置已保存</span>
          </div>
        </div>
      </div> -->

      <!-- 平台选择设置 -->
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex items-center gap-2">
          <Globe class="w-5 h-5 text-blue-600" />
          <h2 class="font-bold text-slate-800">数据源平台选择</h2>
        </div>
        <div class="p-6 md:p-8">
          <p class="text-sm text-slate-600 mb-4">选择要爬取数据的平台（未选择则默认爬取所有平台）</p>
          <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            <label v-for="platform in availablePlatforms" :key="platform.code"
              class="flex items-center space-x-2 p-3 rounded-lg border-2 cursor-pointer transition-all hover:bg-slate-50"
              :class="selectedPlatforms.includes(platform.code)
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-200 bg-white'">
              <input type="checkbox" :value="platform.code" v-model="selectedPlatforms"
                class="rounded border-slate-300 text-blue-600 focus:ring-blue-500" @change="savePlatformSelection" />
              <span class="text-sm font-medium text-slate-700">{{ platform.name }}</span>
            </label>
          </div>
          <div class="mt-4 text-xs text-slate-400">
            <p>已选择: {{ selectedPlatforms.length === 0 ? '全部平台（默认）' : selectedPlatforms.join('、') }}</p>
          </div>
        </div>
      </div>

      <!-- API 接口配置 -->
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex items-center gap-2 justify-between">
          <div class="flex items-center gap-2">
            <Server class="w-5 h-5 text-blue-600" />
            <h2 class="font-bold text-slate-800">API 接口配置</h2>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-slate-400">已配置 <span>{{ userApis.length }}</span> 个模型</span>
            <button @click="clearAllSettings"
              class="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors flex items-center gap-1.5 text-xs font-bold">
              <Trash2 class="w-3.5 h-3.5" />
              清除缓存
            </button>
          </div>
        </div>
        <div class="p-6 md:p-8 space-y-8">
          <div class="bg-slate-50 p-5 rounded-xl border border-slate-100">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2">
                <PlusCircle class="w-4 h-4" /> 配置新模型
              </h3>
              <button @click="openEditModal()"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1">
                <Plus class="w-3 h-3" /> 添加 API
              </button>
            </div>
            <div class="space-y-3">
              <div v-for="api in userApis" :key="api.id"
                class="bg-white p-4 rounded-lg border border-blue-200 shadow-sm flex justify-between items-center animate-fade-in">
                <div class="flex gap-3 items-center overflow-hidden">
                  <div
                    class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                    {{ api.provider.substring(0, 2).toUpperCase() }}
                  </div>
                  <div class="min-w-0">
                    <h4 class="font-bold text-sm truncate text-slate-800">
                      {{ api.provider }}
                    </h4>
                    <p class="text-xs text-slate-400 truncate font-mono">
                      ...{{ (api.key || '').substring(Math.max(0, (api.key || '').length - 4)) }}
                    </p>
                  </div>
                </div>
                <div class="flex gap-1">
                  <button @click="openEditModal(api.id)"
                    class="p-1.5 text-slate-400 hover:text-blue-600 bg-slate-50 rounded transition-colors">
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button @click="removeApi(api.id)"
                    class="p-1.5 text-slate-400 hover:text-red-500 bg-slate-50 rounded transition-colors">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            <div v-if="userApis.length === 0"
              class="text-center py-8 border-2 border-dashed border-slate-100 rounded-xl text-slate-400 text-xs">
              <p class="mb-2">暂无配置的 API 接口</p>
              <p class="text-[10px] text-slate-300">当前系统使用后端环境变量中的 API Key</p>
              <p class="text-[10px] text-slate-300 mt-1">如需使用自定义 API Key，请在此配置</p>
            </div>
          </div>

          <!-- Agent 绑定（最小操作：选择每个 Agent 用哪个厂商） -->
          <div class="bg-slate-50 p-5 rounded-xl border border-slate-100">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold text-slate-700">Agent 模型绑定</h3>
              <button @click="saveAgentOverrides"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1">
                <Save class="w-4 h-4" /> 保存绑定
              </button>
            </div>
            <p class="text-xs text-slate-500 mb-4">为每个 Agent 选择一个厂商；未选择则使用后端默认（.env + 后端策略）。</p>
            <div class="space-y-3">
              <div v-for="a in agentList" :key="a.key" class="flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <div class="text-sm font-bold text-slate-700">{{ a.name }}</div>
                  <div class="text-[10px] text-slate-400">{{ a.desc }}</div>
                </div>
                <select v-model="agentOverrides[a.key]"
                  class="min-w-[220px] px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 bg-white">
                  <option value="">后端默认（推荐）</option>
                  <option v-for="opt in providerOptions" :key="opt.key" :value="opt.key">
                    {{ opt.name }}
                  </option>
                </select>
              </div>
            </div>
            <div v-if="agentOverridesSaved"
              class="mt-4 p-3 rounded-lg bg-green-50 border border-green-200 text-xs text-green-700 flex items-center gap-2">
              <Check class="w-4 h-4" />
              <span>Agent 绑定已保存</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 即梦 / 火山引擎 文生图配置 -->
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex items-center gap-2 justify-between">
          <div class="flex items-center gap-2">
            <Image class="w-5 h-5 text-purple-600" />
            <h2 class="font-bold text-slate-800">即梦（火山引擎文生图）配置</h2>
          </div>
          <span class="text-xs text-slate-400">用于工作流的图片生成节点</span>
        </div>
        <div class="p-6 md:p-8 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">VOLC Access Key (AK)</label>
              <input v-model="volcengine.access_key" type="password" placeholder="填写 AK（可选，未填则用后端 .env）"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-purple-500 font-mono" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">VOLC Secret Key (SK)</label>
              <input v-model="volcengine.secret_key" type="password" placeholder="填写 SK（可选，未填则用后端 .env）"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-purple-500 font-mono" />
            </div>
          </div>

          <div class="flex items-center justify-between pt-2">
            <p class="text-[10px] text-slate-400">
              未填写 AK/SK 时，后端会继续使用 `.env` 中的 VOLC_ACCESS_KEY / VOLC_SECRET_KEY。
            </p>
            <button @click="saveVolcengineConfig"
              class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1">
              <Save class="w-4 h-4" /> 保存即梦配置
            </button>
          </div>

          <div v-if="volcengineSaved"
            class="p-3 rounded-lg bg-green-50 border border-green-200 text-xs text-green-700 flex items-center gap-2">
            <Check class="w-4 h-4" />
            <span>即梦配置已保存</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for API Editing -->
    <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      @click.self="closeEditModal">
      <div class="absolute inset-0 modal-overlay" @click="closeEditModal"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-fade-in z-10">
        <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h3 class="font-bold text-slate-800 flex items-center gap-2">
            <Settings2 class="w-4 h-4" /> {{ editingApiId ? '编辑模型配置' : '配置新模型' }}
          </h3>
          <button @click="closeEditModal" class="text-slate-400 hover:text-slate-600">
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">选择模型厂商</label>
            <select v-model="formData.providerKey" @change="updateProviderMeta"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 bg-white">
              <option value="gemini">Gemini (Google)</option>
              <option value="deepseek">Deepseek (深度求索)</option>
              <option value="doubao">Doubao (字节豆包)</option>
              <option value="kimi">Kimi (月之暗面)</option>
              <option value="zhipu">Zhipu AI (智谱清言)</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">API Key</label>
            <input v-model="formData.key" type="password" placeholder="sk-...（可用逗号或换行粘贴多条）"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono" />
          </div>
        </div>
        <div class="px-6 py-4 bg-slate-50 flex justify-end gap-2 border-t border-slate-100">
          <button @click="closeEditModal"
            class="px-4 py-2 text-slate-500 text-xs font-bold hover:bg-slate-200 rounded-lg transition-colors">
            取消
          </button>
          <button @click="saveApi"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1">
            <Save class="w-4 h-4" /> 保存配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Server, PlusCircle, Plus, Edit2, Trash2, Settings2, X, Save, Globe, Flame, Check, Image
} from 'lucide-vue-next'
import { useConfigStore } from '../stores/config'
import { useAnalysisStore } from '../stores/analysis'
import { api } from '../api'

const emit = defineEmits(['api-updated'])

const configStore = useConfigStore()
const analysisStore = useAnalysisStore()
const showModal = ref(false)
const editingApiId = ref(null)
const userApis = ref([])

// 平台选择
const availablePlatforms = computed(() => analysisStore.availablePlatforms)
const selectedPlatforms = ref([])

// 加载保存的平台选择
const loadPlatformSelection = () => {
  const saved = localStorage.getItem('grandchart_selected_platforms')
  if (saved) {
    try {
      selectedPlatforms.value = JSON.parse(saved)
      analysisStore.setSelectedPlatforms(selectedPlatforms.value)
    } catch (e) {
      console.error('Failed to load platform selection:', e)
      selectedPlatforms.value = []
    }
  } else {
    selectedPlatforms.value = []
  }
}

// 保存平台选择
const savePlatformSelection = () => {
  localStorage.setItem('grandchart_selected_platforms', JSON.stringify(selectedPlatforms.value))
  analysisStore.setSelectedPlatforms(selectedPlatforms.value)
  console.log('[Settings] 平台选择已保存:', selectedPlatforms.value)
}

const formData = ref({
  providerKey: 'deepseek',
  provider: 'Deepseek',
  key: '',
})

const providerNames = {
  deepseek: 'Deepseek',
  gemini: 'Gemini',
  doubao: 'Doubao',
  kimi: 'Kimi',
  zhipu: 'Zhipu AI',
  openai: 'OpenAI'
}

const loadApiSettings = () => {
  userApis.value = configStore.getUserApis
}

const updateProviderMeta = () => {
  formData.value.provider = providerNames[formData.value.providerKey] || 'Deepseek'
}

const openEditModal = (id = null) => {
  editingApiId.value = id
  if (id) {
    const api = userApis.value.find(a => a.id === id)
    if (api) {
      const allowed = Object.keys(providerNames)
      formData.value = {
        providerKey: allowed.includes(api.providerKey) ? api.providerKey : 'deepseek',
        provider: api.provider || providerNames[api.providerKey] || 'Deepseek',
        key: api.key,
      }
      updateProviderMeta()
    }
  } else {
    formData.value = {
      providerKey: 'deepseek',
      provider: 'Deepseek',
      key: '',
    }
    updateProviderMeta()
  }
  showModal.value = true
}

const closeEditModal = () => {
  showModal.value = false
  editingApiId.value = null
}

const saveApi = () => {
  if (!formData.value.key) {
    alert('请填写完整信息')
    return
  }

  const apiData = {
    provider: formData.value.provider,
    providerKey: formData.value.providerKey,
    key: formData.value.key,
    active: true
  }

  if (editingApiId.value) {
    const index = userApis.value.findIndex(a => a.id === editingApiId.value)
    if (index !== -1) {
      userApis.value[index] = { ...userApis.value[index], ...apiData }
    }
  } else {
    userApis.value.push({ id: Date.now(), ...apiData })
  }

  configStore.saveUserApis(userApis.value)
  syncUserApisToBackend()
  closeEditModal()
  emit('api-updated')
}

const removeApi = (id) => {
  if (!confirm('确定删除?')) return
  userApis.value = userApis.value.filter(a => a.id !== id)
  configStore.saveUserApis(userApis.value)
  syncUserApisToBackend()
  emit('api-updated')
}

const syncUserApisToBackend = async () => {
  try {
    await api.updateUserSettings({ llm_apis: userApis.value })
  } catch (e) {
    console.warn('[Settings] 同步 LLM API 到后端失败:', e?.message || e)
  }
}

// 热榜配置
const hotNewsConfig = ref({
  enabled: true,
  platform_sources: [],
  fetch_interval_hours: 4,
  cache_ttl_minutes: 30,
  max_items_per_platform: 100,
})

const hotNewsConfigSaved = ref(false)

const hotPlatforms = [
  { id: 'weibo', name: '微博' },
  { id: 'bilibili', name: 'B站' },
  { id: 'douyin', name: '抖音' },
  { id: 'xhs', name: '小红书' },
  { id: 'baidu', name: '百度' },
  { id: 'tieba', name: '贴吧' },
  { id: 'kuaishou', name: '快手' },
  { id: 'zhihu', name: '知乎' },
]

const loadHotNewsConfig = async () => {
  try {
    const data = await api.getConfig()
    if (data.hot_news_config) {
      hotNewsConfig.value = { ...hotNewsConfig.value, ...data.hot_news_config }
    }
  } catch (error) {
    console.error('Failed to load hot news config:', error)
  }
}

const toggleHotPlatform = (platformId, isChecked) => {
  if (isChecked) {
    if (!hotNewsConfig.value.platform_sources.includes(platformId)) {
      hotNewsConfig.value.platform_sources.push(platformId)
    }
  } else {
    hotNewsConfig.value.platform_sources = hotNewsConfig.value.platform_sources.filter(p => p !== platformId)
  }
  saveHotNewsConfig()
}

const saveHotNewsConfig = async () => {
  try {
    await api.updateConfig({ hot_news_config: hotNewsConfig.value })
      hotNewsConfigSaved.value = true
      console.log('[Settings] 热榜配置已保存:', hotNewsConfig.value)

      // 3 秒后隐藏保存提示
      setTimeout(() => {
        hotNewsConfigSaved.value = false
      }, 3000)
  } catch (error) {
    console.error('Failed to save hot news config:', error)
    alert('保存配置出错: ' + error.message)
  }
}

// 即梦 / 火山引擎文生图配置
const volcengine = ref({
  access_key: '',
  secret_key: '',
})

const volcengineSaved = ref(false)
const agentOverridesSaved = ref(false)

// Agent 绑定（前端只负责选择厂商，后端决定模型/URL/路由策略）
const agentList = [
  { key: 'reporter', name: 'Reporter', desc: '事实提炼/信息汇总' },
  { key: 'analyst', name: 'Analyst', desc: '舆论分析/洞察生成' },
  { key: 'debater', name: 'Debater', desc: '反驳/辩论视角' },
  { key: 'writer', name: 'Writer', desc: '文案生成/润色' },
  { key: 'hotnews_interpretation_agent', name: 'HotNews Interpreter', desc: '热榜单条“演化解读”' },
  { key: 'translator', name: 'Translator', desc: '中->英 搜索关键词' },
]

const agentOverrides = ref({})

const providerOptions = computed(() => {
  const allowed = Object.keys(providerNames)
  const uniq = new Map()
  for (const it of (userApis.value || [])) {
    const key = (it?.providerKey || '').trim()
    if (!key || !allowed.includes(key)) continue
    if (!uniq.has(key)) uniq.set(key, providerNames[key] || key)
  }
  return Array.from(uniq.entries()).map(([key, name]) => ({ key, name }))
})

const saveAgentOverrides = async () => {
  try {
    const payload = {}
    for (const a of agentList) {
      const v = (agentOverrides.value?.[a.key] || '').trim()
      if (v) payload[a.key] = v
    }
    await api.updateUserSettings({ agent_llm_overrides: payload })
    agentOverridesSaved.value = true
    setTimeout(() => {
      agentOverridesSaved.value = false
    }, 3000)
  } catch (e) {
    console.error('[Settings] 保存 Agent 绑定失败:', e)
    alert('保存 Agent 绑定失败: ' + (e?.message || e))
  }
}

const loadUserSettings = async () => {
  try {
    const data = await api.getUserSettings()
    // LLM apis
    if (Array.isArray(data.llm_apis) && data.llm_apis.length > 0) {
      userApis.value = data.llm_apis
      configStore.saveUserApis(userApis.value)
    } else if (Array.isArray(userApis.value) && userApis.value.length > 0) {
      // 后端还没保存过，但本地已有配置：自动补写一次，确保后端能拿到 key
      await api.updateUserSettings({ llm_apis: userApis.value })
    }
    // volcengine
    if (data.volcengine) {
      volcengine.value = { ...volcengine.value, ...data.volcengine }
    }
    // agent overrides
    if (data.agent_llm_overrides && typeof data.agent_llm_overrides === 'object') {
      agentOverrides.value = { ...data.agent_llm_overrides }
    }
  } catch (e) {
    console.warn('[Settings] 加载后端 user-settings 失败，将使用本地设置:', e?.message || e)
  }
}

const saveVolcengineConfig = async () => {
  try {
    await api.updateUserSettings({ volcengine: volcengine.value })
    volcengineSaved.value = true
    setTimeout(() => {
      volcengineSaved.value = false
    }, 3000)
  } catch (e) {
    console.error('[Settings] 保存即梦配置失败:', e)
    alert('保存即梦配置失败: ' + (e?.message || e))
  }
}

const clearAllSettings = async () => {
  if (!confirm('确定要清除所有本地缓存吗？这将删除所有保存的 API Keys、平台选择和其他设置。')) {
    return
  }
  
  try {
    // 清除所有相关的 localStorage
    localStorage.removeItem('grandchart_llm_apis')
    localStorage.removeItem('grandchart_selected_platforms')
    localStorage.removeItem('grandchart_hot_news_config')
    localStorage.removeItem('grandchart_volcengine_config')
    localStorage.removeItem('grandchart_agent_overrides')
    
    // 重置所有状态
    userApis.value = []
    selectedPlatforms.value = []
    hotNewsConfig.value = {
      enabled: true,
      platform_sources: [],
      fetch_interval_hours: 4,
      cache_ttl_minutes: 30,
      max_items_per_platform: 100,
    }
    volcengine.value = {
      access_key: '',
      secret_key: '',
    }
    agentOverrides.value = {}
    
    // 清空后端设置
    await api.updateUserSettings({ 
      llm_apis: [],
      volcengine: { access_key: '', secret_key: '' },
      agent_llm_overrides: {}
    })
    await api.updateConfig({ hot_news_config: hotNewsConfig.value })
    
    configStore.saveUserApis([])
    analysisStore.setSelectedPlatforms([])
    
    alert('所有设置已清除！页面即将刷新。')
    setTimeout(() => {
      location.reload()
    }, 500)
  } catch (e) {
    console.error('[Settings] 清除设置失败:', e)
    alert('清除设置时出错: ' + (e?.message || e))
  }
}

onMounted(() => {
  loadApiSettings()
  loadUserSettings()
  loadPlatformSelection()
  loadHotNewsConfig()
})
</script>