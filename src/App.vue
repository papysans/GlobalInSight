<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <!-- Navigation Bar -->
    <nav class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <div class="flex items-center gap-2 cursor-pointer" @click="switchTab('home')">
            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <Waves class="w-5 h-5" />
            </div>
            <span class="text-xl font-bold text-slate-800 tracking-tight">
              观潮 <span class="font-light text-blue-600">GrandChart</span>
            </span>
          </div>
          
          <div class="hidden md:flex items-center gap-2 text-sm font-medium text-slate-600 bg-slate-100/50 p-1 rounded-full border border-slate-200/50">
            <button
              @click="switchTab('home')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all hover:text-blue-600 flex items-center gap-1', currentTab === 'home' ? 'active' : '']"
            >
              <Zap class="w-3 h-3" /> 舆情推演
            </button>
            <button
              @click="switchTab('data')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all hover:text-blue-600 flex items-center gap-1', currentTab === 'data' ? 'active' : '']"
            >
              <PieChart class="w-3 h-3" /> 数据洞察
            </button>
            <button
              @click="switchTab('arch')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all hover:text-blue-600 flex items-center gap-1', currentTab === 'arch' ? 'active' : '']"
            >
              <Network class="w-3 h-3" /> 系统架构
            </button>
            <button
              @click="switchTab('vision')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all hover:text-blue-600 flex items-center gap-1', currentTab === 'vision' ? 'active' : '']"
            >
              <Flag class="w-3 h-3" /> 愿景与价值
            </button>
          </div>

          <div class="flex items-center gap-3">
            <button
              @click="switchTab('settings')"
              class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors flex items-center gap-1"
              title="接口管理"
            >
              <Plug class="w-5 h-5" />
              <span class="text-xs font-bold hidden sm:inline">接口配置</span>
              <span v-if="apiCount > 0" class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow relative pb-20">
      <!-- Home View: 舆情推演 -->
      <HomeView v-if="currentTab === 'home'" />
      
      <!-- Data View: 数据洞察 -->
      <DataView v-if="currentTab === 'data'" />
      
      <!-- Arch View: 系统架构 -->
      <ArchView v-if="currentTab === 'arch'" />
      
      <!-- Vision View: 愿景与价值 -->
      <VisionView v-if="currentTab === 'vision'" />
      
      <!-- Settings View: 接口配置 -->
      <SettingsView v-if="currentTab === 'settings'" @api-updated="handleApiUpdated" />
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Waves, Zap, PieChart, Network, Flag, Plug } from 'lucide-vue-next'
import HomeView from './views/HomeView.vue'
import DataView from './views/DataView.vue'
import ArchView from './views/ArchView.vue'
import VisionView from './views/VisionView.vue'
import SettingsView from './views/SettingsView.vue'
import { useConfigStore } from './stores/config'

const currentTab = ref('home')
const configStore = useConfigStore()

const apiCount = computed(() => {
  const apis = configStore.getUserApis
  return apis.length
})

const switchTab = (tab) => {
  currentTab.value = tab
  window.scrollTo(0, 0)
}

const handleApiUpdated = () => {
  // API更新后的处理
}
</script>

<style scoped>
.nav-link.active {
  color: #2563eb;
  background-color: #eff6ff;
}
</style>