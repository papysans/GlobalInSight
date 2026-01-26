<template>
  <div class="min-h-screen flex flex-col transition-colors duration-300" 
       :class="[
         isDark ? 'bg-slate-900' : 'bg-slate-50',
         currentTab === 'vision' && !isDark ? 'bg-transparent' : ''
       ]">
    <!-- Navigation Bar -->
    <nav class="sticky top-0 z-50 backdrop-blur-md border-b shadow-sm transition-colors duration-300"
         :class="isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/90 border-slate-200'">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <div class="flex items-center gap-2 cursor-pointer" @click="switchTab('home')">
            <img :src="logo" alt="Logo" class="w-16 h-16 object-cover" :class="isDark ? '' : 'mix-blend-multiply'" />
            <span class="text-xl font-bold tracking-tight transition-colors" :class="isDark ? 'text-white' : 'text-slate-800'">
              观潮 <span :class="isDark ? 'text-blue-400' : 'text-blue-600'" class="font-mid">GlobalInSight</span>
            </span>
          </div>

          <div
            class="hidden md:flex items-center gap-2 text-sm font-medium p-1 rounded-full border transition-colors duration-300"
            :class="isDark ? 'text-slate-300 bg-slate-800/50 border-slate-600' : 'text-slate-600 bg-slate-100/50 border-slate-200/50'">
            <button @click="switchTab('hot')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1', 
                       currentTab === 'hot' ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <Flame class="w-3 h-3" /> 热榜
            </button>
            <button @click="switchTab('home')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1', 
                       currentTab === 'home' ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <Zap class="w-3 h-3" /> 舆情推演
            </button>
            <button @click="switchTab('data')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1', 
                       currentTab === 'data' ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <PieChart class="w-3 h-3" /> 数据洞察
            </button>
            <button @click="switchTab('arch')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1', 
                       currentTab === 'arch' ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <Network class="w-3 h-3" /> 系统架构
            </button>
            <button @click="switchTab('vision')"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1', 
                       currentTab === 'vision' ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <Flag class="w-3 h-3" /> 愿景与价值
            </button>
          </div>

          <div class="flex items-center gap-2">
            <!-- 主题切换按钮 -->
            <button @click="toggleTheme"
              class="p-2 rounded-full transition-all duration-300 flex items-center justify-center"
              :class="isDark 
                ? 'text-amber-400 hover:text-amber-300 hover:bg-slate-700' 
                : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'"
              :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
              <Sun v-if="isDark" class="w-5 h-5" />
              <Moon v-else class="w-5 h-5" />
            </button>
            
            <button @click="switchTab('settings')"
              class="p-2 rounded-full transition-colors flex items-center gap-1"
              :class="isDark ? 'text-slate-400 hover:text-blue-400 hover:bg-slate-700' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'"
              title="设置">
              <Settings class="w-5 h-5" />
              <span class="text-xs font-bold hidden sm:inline">设置</span>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow relative">
      <!-- Hot View: 热榜 -->
      <HotView v-if="currentTab === 'hot'" @switch-tab="switchTab" :dark-mode="isDark" />

      <!-- Home View: 舆情推演 -->
      <HomeView v-if="currentTab === 'home'" :dark-mode="isDark" />

      <!-- Data View: 数据洞察 (使用 v-show 保持组件挂载，以便接收事件) -->
      <DataView v-show="currentTab === 'data'" ref="dataViewRef" data-view="data" :dark-mode="isDark" />

      <!-- Arch View: 系统架构 -->
      <ArchView v-if="currentTab === 'arch'" :dark-mode="isDark" />

      <!-- Vision View: 愿景与价值 (始终深色) -->
      <VisionView v-if="currentTab === 'vision'" />

      <!-- Settings View: 设置 -->
      <SettingsView v-if="currentTab === 'settings'" @api-updated="handleApiUpdated" :dark-mode="isDark" />
    </main>

    <!-- Global Footer -->
    <footer class="border-t py-4 transition-colors duration-300" 
            :class="isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white border-slate-200'">
      <div class="max-w-7xl mx-auto px-4 text-center">
        <p class="text-xs font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          观潮 GlobalInSight · Powered by Multi-Agent Debate + LangGraph
        </p>
        <p class="text-xs mt-1" :class="isDark ? 'text-slate-500' : 'text-slate-400'">
          © 2026 Napstablook · 
          <a href="https://github.com/papysans/GlobalInSight" target="_blank" 
             class="hover:text-blue-500 transition-colors inline-flex items-center gap-1">
            <Github class="w-3 h-3" /> GitHub
          </a>
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Zap, PieChart, Network, Flag, Settings, Flame, Github, Sun, Moon } from 'lucide-vue-next'
import logo from './logo/logo-light.png'
import HomeView from './views/HomeView.vue'
import HotView from './views/HotView.vue'
import DataView from './views/DataView.vue'
import ArchView from './views/ArchView.vue'
import VisionView from './views/VisionView.vue'
import SettingsView from './views/SettingsView.vue'
import { useConfigStore } from './stores/config'

const currentTab = ref('home')
const dataViewRef = ref(null)
const configStore = useConfigStore()

// 计算是否为深色模式
const isDark = computed(() => configStore.isDarkMode)

// 切换主题
const toggleTheme = () => {
  configStore.toggleDarkMode()
}

const switchTab = (tab) => {
  currentTab.value = tab
  window.scrollTo(0, 0)
}

const handleApiUpdated = () => {
  // API更新后的处理
}

// 初始化深色模式
onMounted(() => {
  configStore.initDarkMode()
})
</script>

<style scoped>
.nav-link.active {
  color: #2563eb;
  background-color: #eff6ff;
}

.nav-link.active-dark {
  color: #60a5fa;
  background-color: rgba(59, 130, 246, 0.2);
}
</style>