<template>
  <div class="view-section animate-fade-in py-12 px-4">
    <div class="max-w-3xl mx-auto">
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
              <button
                @click="openEditModal()"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1"
              >
                <Plus class="w-3 h-3" /> 添加 API
              </button>
            </div>
            <div class="space-y-3">
              <div
                v-for="api in userApis"
                :key="api.id"
                class="bg-white p-4 rounded-lg border border-blue-200 shadow-sm flex justify-between items-center animate-fade-in"
              >
                <div class="flex gap-3 items-center overflow-hidden">
                  <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
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
                  <button
                    @click="openEditModal(api.id)"
                    class="p-1.5 text-slate-400 hover:text-blue-600 bg-slate-50 rounded transition-colors"
                  >
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button
                    @click="removeApi(api.id)"
                    class="p-1.5 text-slate-400 hover:text-red-500 bg-slate-50 rounded transition-colors"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            <div
              v-if="userApis.length === 0"
              class="text-center py-8 border-2 border-dashed border-slate-100 rounded-xl text-slate-400 text-xs"
            >
              暂无配置的 API 接口，系统无法运行。
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for API Editing -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      @click.self="closeEditModal"
    >
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
            <select
              v-model="formData.providerKey"
              @change="updateBaseUrl"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 bg-white"
            >
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
            <input
              v-model="formData.url"
              type="text"
              placeholder="https://api.example.com/v1"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono text-xs"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">API Key</label>
            <input
              v-model="formData.key"
              type="password"
              placeholder="sk-..."
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">模型代号 (Model ID)</label>
            <div class="relative">
              <input
                v-model="formData.model"
                type="text"
                list="modelOptions"
                placeholder="选择或手动输入模型ID"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-blue-500 font-mono"
              />
              <datalist id="modelOptions">
                <option v-for="model in modelPresets[formData.providerKey] || []" :key="model" :value="model" />
              </datalist>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 bg-slate-50 flex justify-end gap-2 border-t border-slate-100">
          <button
            @click="closeEditModal"
            class="px-4 py-2 text-slate-500 text-xs font-bold hover:bg-slate-200 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="saveApi"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1"
          >
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
  Server, PlusCircle, Plus, Edit2, Trash2, Settings2, X, Save
} from 'lucide-vue-next'
import { useConfigStore } from '../stores/config'

const emit = defineEmits(['api-updated'])

const configStore = useConfigStore()
const showModal = ref(false)
const editingApiId = ref(null)
const userApis = ref([])

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

onMounted(() => {
  loadApiSettings()
})
</script>