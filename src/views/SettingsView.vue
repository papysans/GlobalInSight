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
                      <span v-if="api.model" class="text-slate-500 font-normal">
                        - {{ getModelDisplayName(api.providerKey, api.model) }}
                      </span>
                      <span v-else class="text-slate-400 font-normal text-xs">(默认)</span>
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
            <p class="text-xs text-slate-500 mb-4">
              为每个 Agent 选择已配置的 API；未选择则使用后端默认（.env + 后端策略）。
              <span class="text-blue-600 font-semibold">只能选择上方已配置的 API。</span>
            </p>
            
            <!-- 紧凑卡片式布局 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <div v-for="a in agentList" :key="a.key" 
                class="bg-white rounded-lg border border-slate-200 p-3 hover:border-blue-300 transition-colors">
                <!-- Agent 名称和描述 -->
                <div class="flex items-center gap-2 mb-2">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                    {{ a.name.substring(0, 2).toUpperCase() }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-bold text-slate-800">{{ a.name }}</div>
                    <div class="text-[10px] text-slate-400 truncate">{{ a.desc }}</div>
                  </div>
                </div>
                
                <!-- API 选择（从已配置的 API 中选择） -->
                <div>
                  <label class="text-[10px] text-slate-500 font-semibold mb-1 block">选择 API 配置</label>
                  <select 
                    v-model="agentOverrides[a.key].apiId"
                    class="w-full px-2 py-1.5 border border-slate-200 rounded text-xs outline-none focus:border-blue-500 bg-white">
                    <option value="">后端默认（.env 配置）</option>
                    <option v-for="api in userApis" :key="api.id" :value="api.id">
                      {{ api.provider }} - {{ getModelDisplayName(api.providerKey, api.model) }} (...{{ api.key.slice(-4) }})
                    </option>
                  </select>
                  <p class="text-[9px] text-slate-400 mt-1">
                    {{ getSelectedApiInfo(agentOverrides[a.key].apiId) }}
                  </p>
                </div>
              </div>
            </div>
            
            <!-- 提示：如果没有配置 API -->
            <div v-if="userApis.length === 0" 
              class="mt-3 p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-700 flex items-center gap-2">
              <AlertTriangle class="w-4 h-4" />
              <span>请先在上方"API 接口配置"中添加 API Key，然后才能为 Agent 绑定。</span>
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

          <!-- 新增：AI生图张数选择 -->
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">AI生图张数</label>
            <select v-model.number="volcengine.image_count" @change="saveVolcengineConfig"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-purple-500 bg-white">
              <option :value="0">0 张（不生图）</option>
              <option :value="1">1 张</option>
              <option :value="2">2 张（默认）</option>
              <option :value="3">3 张</option>
              <option :value="4">4 张</option>
              <option :value="5">5 张</option>
              <option :value="6">6 张</option>
              <option :value="7">7 张</option>
              <option :value="8">8 张</option>
              <option :value="9">9 张</option>
            </select>
            <p class="text-[10px] text-slate-400 mt-1">
              每次工作流生成的图片数量（0-9张）。生成更多图片会增加耗时和费用。选择后自动保存。
            </p>
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

      <!-- 小红书 MCP 配置 -->
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div class="bg-slate-50 px-6 py-4 border-b border-slate-100 flex items-center gap-2 justify-between">
          <div class="flex items-center gap-2">
            <Share2 class="w-5 h-5 text-red-500" />
            <h2 class="font-bold text-slate-800">小红书 MCP 配置</h2>
          </div>
          <span class="text-xs text-slate-400">配置发布服务连接</span>
        </div>
        <div class="p-6 md:p-8 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">MCP 服务地址 (HTTP)</label>
            <div class="flex gap-2">
              <input v-model="xhsConfig.mcp_url" type="text" placeholder="默认: http://localhost:18060/mcp"
                class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-red-500 font-mono" />
              <button @click="testXhsConnection" :disabled="xhsTesting"
                class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1 disabled:opacity-50">
                <Plug class="w-3.5 h-3.5" v-if="!xhsTesting"/>
                <Loader2 class="w-3.5 h-3.5 animate-spin" v-else/>
                测试连接
              </button>
            </div>
            <p class="text-[10px] text-slate-400 mt-1">
              请确保已启动 xiaohongshu-mcp 服务。默认运行在端口 18060。
            </p>
          </div>

          <!-- 连接状态反馈 -->
          <div v-if="xhsTestResult" :class="[
            'p-3 rounded-lg text-xs flex items-center gap-2 border',
            xhsTestResult.success ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'
          ]">
            <component :is="xhsTestResult.success ? Check : AlertTriangle" class="w-4 h-4" />
            <span>{{ xhsTestResult.message }}</span>
          </div>

          <div class="flex items-center justify-between pt-2">
             <!-- 自动发布暂未完全实现，先隐藏开关，只提供 URL 配置 -->
             <div></div>
            <button @click="saveXhsConfig"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1">
              <Save class="w-4 h-4" /> 保存小红书配置
            </button>
          </div>

           <div v-if="xhsConfigSaved"
            class="p-3 rounded-lg bg-green-50 border border-green-200 text-xs text-green-700 flex items-center gap-2">
            <Check class="w-4 h-4" />
            <span>小红书配置已保存</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for API Editing -->
    <Teleport to="body">
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
            <label class="block text-xs font-semibold text-slate-500 mb-1">选择模型</label>
            <select v-model="formData.model"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 bg-white">
              <option value="">使用默认模型</option>
              <option 
                v-for="model in configStore.getModelsForProvider(formData.providerKey)" 
                :key="model.id"
                :value="model.id"
              >
                {{ model.name }}
                <template v-if="model.is_default">(默认)</template>
                <template v-if="model.description"> - {{ model.description }}</template>
              </option>
            </select>
            <p class="text-[10px] text-slate-400 mt-1">
              未选择时将使用该厂商的默认模型
            </p>
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
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Server, PlusCircle, Plus, Edit2, Trash2, Settings2, X, Save, Globe, Flame, Check, Image, Share2, Plug, Loader2, AlertTriangle
} from 'lucide-vue-next'
import { useConfigStore } from '../stores/config'
import { useAnalysisStore } from '../stores/analysis'
import { api } from '../api'

// 设置页
// - 管理 LLM Provider Key + 模型配置（本地保存并同步到后端）
// - 选择数据采集平台（会影响分析与数据洞察生成）
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
  model: '',  // 新增：选中的模型
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
  let apis = configStore.getUserApis
  
  // 向后兼容：为旧配置自动添加默认模型
  let needsMigration = false
  apis = apis.map(api => {
    if (!api.model && api.providerKey) {
      needsMigration = true
      const defaultModel = configStore.getDefaultModel(api.providerKey)
      console.log(`[Settings] 迁移旧配置: ${api.provider} -> 默认模型: ${defaultModel}`)
      return {
        ...api,
        model: defaultModel || ''
      }
    }
    return api
  })
  
  // 如果有迁移，保存更新后的配置
  if (needsMigration) {
    console.log('[Settings] 检测到旧格式配置，已自动迁移到新格式')
    configStore.saveUserApis(apis)
    syncUserApisToBackend()
  }
  
  userApis.value = apis
}

const updateProviderMeta = () => {
  formData.value.provider = providerNames[formData.value.providerKey] || 'Deepseek'
  // 切换提供商时，重置为该提供商的默认模型
  const defaultModel = configStore.getDefaultModel(formData.value.providerKey)
  formData.value.model = defaultModel || ''
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
        model: api.model || '',  // 加载已保存的模型
        key: api.key,
      }
      updateProviderMeta()
    }
  } else {
    formData.value = {
      providerKey: 'deepseek',
      provider: 'Deepseek',
      model: '',
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
    model: formData.value.model || '',  // 保存模型字段
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
  image_count: 2,  // 默认生成2张图片
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

const agentOverrides = ref({
  reporter: { apiId: '' },
  analyst: { apiId: '' },
  debater: { apiId: '' },
  writer: { apiId: '' },
  hotnews_interpretation_agent: { apiId: '' },
  translator: { apiId: '' }
})

// 获取选中 API 的信息
const getSelectedApiInfo = (apiId) => {
  if (!apiId) return '使用后端默认配置'
  const api = userApis.value.find(a => a.id === apiId)
  if (!api) return '未找到对应的 API 配置'
  const modelName = getModelDisplayName(api.providerKey, api.model)
  return `将使用: ${api.provider} - ${modelName}`
}

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
      const override = agentOverrides.value?.[a.key]
      if (override && override.apiId) {
        // 找到对应的 API 配置
        const api = userApis.value.find(item => item.id === override.apiId)
        if (api) {
          // 保存提供商和模型信息（后端需要这些信息来调用 LLM）
          payload[a.key] = {
            provider: api.providerKey,
            model: api.model || '',
            apiId: api.id  // 保存 API ID 用于前端回显
          }
          console.log(`[Settings] Agent ${a.key} -> API:`, {
            provider: api.providerKey,
            model: api.model,
            apiId: api.id
          })
        }
      }
    }
    console.log('[Settings] 完整 payload:', JSON.stringify(payload, null, 2))
    await api.updateUserSettings({ agent_llm_overrides: payload })
    agentOverridesSaved.value = true
    console.log('[Settings] Agent 绑定已保存:', payload)
    setTimeout(() => {
      agentOverridesSaved.value = false
    }, 3000)
  } catch (e) {
    console.error('[Settings] 保存 Agent 绑定失败:', e)
    console.error('[Settings] 错误详情:', e.message, e.stack)
    alert('保存 Agent 绑定失败: ' + (e?.message || e))
  }
}

const loadUserSettings = async () => {
  try {
    console.log('[Settings] 开始加载用户设置...')
    const data = await api.getUserSettings()
    console.log('[Settings] 后端返回的数据:', data)
    
    // LLM apis
    if (Array.isArray(data.llm_apis) && data.llm_apis.length > 0) {
      userApis.value = data.llm_apis
      configStore.saveUserApis(userApis.value)
    } else if (Array.isArray(userApis.value) && userApis.value.length > 0) {
      // 后端还没保存过，但本地已有配置：自动补写一次，确保后端能拿到 key
      await api.updateUserSettings({ llm_apis: userApis.value })
    }
    // volcengine
    console.log('[Settings] 加载前 volcengine.value:', JSON.parse(JSON.stringify(volcengine.value)))
    if (data.volcengine) {
      console.log('[Settings] 后端返回的 volcengine:', data.volcengine)
      volcengine.value = { ...volcengine.value, ...data.volcengine }
      console.log('[Settings] 已加载火山引擎配置:', volcengine.value)
    } else {
      console.log('[Settings] 后端没有返回 volcengine 配置')
    }
    // agent overrides - 新逻辑：通过 apiId 关联
    if (data.agent_llm_overrides && typeof data.agent_llm_overrides === 'object') {
      for (const agentKey in data.agent_llm_overrides) {
        const override = data.agent_llm_overrides[agentKey]
        
        if (typeof override === 'string') {
          // 旧格式：只有提供商字符串 - 尝试找到匹配的 API
          console.log(`[Settings] 迁移旧格式 Agent 配置: ${agentKey} -> ${override}`)
          const matchedApi = userApis.value.find(a => a.providerKey === override)
          agentOverrides.value[agentKey] = {
            apiId: matchedApi ? matchedApi.id : ''
          }
        } else if (typeof override === 'object') {
          // 新格式：包含 provider, model, apiId
          if (override.apiId) {
            // 有 apiId，直接使用
            agentOverrides.value[agentKey] = {
              apiId: override.apiId
            }
          } else if (override.provider && override.model) {
            // 没有 apiId，但有 provider 和 model - 尝试匹配
            const matchedApi = userApis.value.find(a => 
              a.providerKey === override.provider && a.model === override.model
            )
            agentOverrides.value[agentKey] = {
              apiId: matchedApi ? matchedApi.id : ''
            }
          }
        }
      }
    }
  } catch (e) {
    console.warn('[Settings] 加载后端 user-settings 失败，将使用本地设置:', e?.message || e)
  }
}

const saveVolcengineConfig = async () => {
  try {
    console.log('[Settings] 正在保存火山引擎配置:', volcengine.value)
    await api.updateUserSettings({ volcengine: volcengine.value })
    volcengineSaved.value = true
    console.log('[Settings] 火山引擎配置已保存')
    setTimeout(() => {
      volcengineSaved.value = false
    }, 3000)
  } catch (e) {
    console.error('[Settings] 保存即梦配置失败:', e)
    alert('保存即梦配置失败: ' + (e?.message || e))
  }
}

// 小红书配置
const xhsConfig = ref({
  mcp_url: 'http://localhost:18060/mcp'
})
const xhsConfigSaved = ref(false)
const xhsTesting = ref(false)
const xhsTestResult = ref(null)

const saveXhsConfig = async () => {
  try {
    // 暂时还没有对应的 API 更新方法，这里只是模拟保存并在本地生效
    // 实际项目中应该有对应的后端配置更新接口
    // 这里我们先保存到 localStorage 作为演示
    localStorage.setItem('grandchart_xhs_config', JSON.stringify(xhsConfig.value))
    
    xhsConfigSaved.value = true
    setTimeout(() => {
      xhsConfigSaved.value = false
    }, 3000)
  } catch (e) {
    console.error('[Settings] 保存小红书配置失败:', e)
    alert('保存小红书配置失败: ' + (e?.message || e))
  }
}

const testXhsConnection = async () => {
  xhsTesting.value = true
  xhsTestResult.value = null
  try {
    // 尝试调用后端检查接口
    // 这里假设后端通过环境变量等方式知道了 mcp_url，或者我们在请求头/体中传过去
    // 为了简单起见，这里复用 getXhsStatus，它目前是直接调用后端默认配置的
    const res = await api.getXhsStatus()
    if (res.mcp_available) {
      xhsTestResult.value = {
        success: true,
        message: `连接成功 (已登录: ${res.login_status ? '是' : '否'})`
      }
    } else {
      xhsTestResult.value = {
        success: false,
        message: '连接失败: 服务未启动或不可达'
      }
    }
  } catch (e) {
    xhsTestResult.value = {
      success: false,
      message: '连接请求出错: ' + (e.message || '未知错误')
    }
  } finally {
    xhsTesting.value = false
  }
}

const loadXhsConfig = () => {
  const saved = localStorage.getItem('grandchart_xhs_config')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (parsed.mcp_url) {
        xhsConfig.value.mcp_url = parsed.mcp_url
      }
    } catch (e) {
      // ignore
    }
  }
}

// 获取模型显示名称
const getModelDisplayName = (providerKey, modelId) => {
  if (!modelId) return '默认'
  const models = configStore.getModelsForProvider(providerKey)
  const model = models.find(m => m.id === modelId)
  return model ? model.name : modelId
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
    localStorage.removeItem('grandchart_xhs_config')

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
      image_count: 2,
    }
    agentOverrides.value = {}
    xhsConfig.value = { mcp_url: 'http://localhost:18060/mcp' }

    // 清空后端设置
    await api.updateUserSettings({
      llm_apis: [],
      volcengine: { access_key: '', secret_key: '', image_count: 2 },
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

onMounted(async () => {
  loadApiSettings()
  loadUserSettings()
  loadPlatformSelection()
  loadHotNewsConfig()
  loadXhsConfig()
  
  // 加载模型列表
  try {
    await configStore.fetchModels()
  } catch (e) {
    console.error('[Settings] 加载模型列表失败:', e)
  }
})
</script>
