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
          <span class="text-xs text-slate-400">已配置 <span>{{ userApis.length }}</span> 个模型</span>
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
                      <span class="text-xs font-normal bg-slate-100 px-1 rounded text-slate-500">{{ api.model }}</span>
                    </h4>
                    <p class="text-xs text-slate-400 truncate font-mono">
                      ...{{ api.key.substring(Math.max(0, api.key.length - 4)) }}
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
            <select v-model="formData.providerKey" @change="updateBaseUrl"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 bg-white">
              <option value="gemini">Gemini (Google)</option>
              <option value="deepseek">Deepseek (深度求索)</option>
              <option value="doubao">Doubao (字节豆包)</option>
              <option value="kimi">Kimi (月之暗面)</option>
              <option value="zhipu">Zhipu AI (智谱清言)</option>
              <option value="qwen">Qwen (通义千问)</option>
              <option value="custom">自定义 / OpenAI Compatible</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">API Base URL</label>
            <input v-model="formData.url" type="text" placeholder="https://api.example.com/v1"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono text-xs" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">API Key</label>
            <input v-model="formData.key" type="password" placeholder="sk-..."
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">模型代号 (Model ID)</label>
            <div class="relative">
              <input v-model="formData.model" type="text" list="modelOptions" placeholder="选择或手动输入模型ID"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono" />
              <datalist id="modelOptions">
                <option v-for="model in modelPresets[formData.providerKey] || []" :key="model" :value="model" />
              </datalist>
            </div>
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
  Server, PlusCircle, Plus, Edit2, Trash2, Settings2, X, Save, Globe, Flame, Check
} from 'lucide-vue-next'
import { useConfigStore } from '../stores/config'
import { useAnalysisStore } from '../stores/analysis'

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
  url: '',
  key: '',
  model: ''
})

const apiProviders = {
  deepseek: 'https://api.deepseek.com',
  gemini: 'https://generativelanguage.googleapis.com/v1beta/models',
  doubao: 'https://ark.cn-beijing.volces.com/api/v3',
  kimi: 'https://api.moonshot.cn/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  custom: ''
}

const modelPresets = {
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
  gemini: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-3-pro-preview', 'gemini-3-flash-preview'],
  doubao: ['doubao-pro-32k', 'doubao-lite-4k'],
  kimi: ['moonshot-v1-8k', 'moonshot-v1-32k'],
  zhipu: ['glm-4', 'glm-4-air', 'glm-4-flash'],
  qwen: ['qwen-turbo', 'qwen-plus'],
  custom: []
}

const providerNames = {
  deepseek: 'Deepseek',
  gemini: 'Gemini',
  doubao: 'Doubao',
  kimi: 'Kimi',
  zhipu: 'Zhipu AI',
  qwen: 'Qwen',
  custom: 'Custom'
}

const loadApiSettings = () => {
  userApis.value = configStore.getUserApis
}

const updateBaseUrl = () => {
  formData.value.url = apiProviders[formData.value.providerKey] || ''
  formData.value.provider = providerNames[formData.value.providerKey] || 'Custom'
}

const openEditModal = (id = null) => {
  editingApiId.value = id
  if (id) {
    const api = userApis.value.find(a => a.id === id)
    if (api) {
      formData.value = {
        providerKey: api.providerKey || 'custom',
        provider: api.provider,
        url: api.url,
        key: api.key,
        model: api.model
      }
      updateBaseUrl()
      formData.value.model = api.model
    }
  } else {
    formData.value = {
      providerKey: 'deepseek',
      provider: 'Deepseek',
      url: '',
      key: '',
      model: ''
    }
    updateBaseUrl()
  }
  showModal.value = true
}

const closeEditModal = () => {
  showModal.value = false
  editingApiId.value = null
}

const saveApi = () => {
  if (!formData.value.url || !formData.value.key) {
    alert('请填写完整信息')
    return
  }

  const apiData = {
    provider: formData.value.provider,
    providerKey: formData.value.providerKey,
    url: formData.value.url,
    key: formData.value.key,
    model: formData.value.model || 'default',
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
  closeEditModal()
  emit('api-updated')
}

const removeApi = (id) => {
  if (!confirm('确定删除?')) return
  userApis.value = userApis.value.filter(a => a.id !== id)
  configStore.saveUserApis(userApis.value)
  emit('api-updated')
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
    const response = await fetch('http://127.0.0.1:8000/api/config')
    const data = await response.json()
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
    const response = await fetch('http://127.0.0.1:8000/api/config', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        hot_news_config: hotNewsConfig.value
      })
    })

    if (response.ok) {
      hotNewsConfigSaved.value = true
      console.log('[Settings] 热榜配置已保存:', hotNewsConfig.value)

      // 3 秒后隐藏保存提示
      setTimeout(() => {
        hotNewsConfigSaved.value = false
      }, 3000)
    } else {
      alert('保存配置失败: ' + response.statusText)
    }
  } catch (error) {
    console.error('Failed to save hot news config:', error)
    alert('保存配置出错: ' + error.message)
  }
}

onMounted(() => {
  loadApiSettings()
  loadPlatformSelection()
  loadHotNewsConfig()
})
</script>