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
      <!--
        使用 Vue Router 统一承载页面视图：
        - 不改变现有导航 UI：仍由顶部按钮触发 switchTab
        - 仅让 URL 与当前页面保持同步，支持刷新/直达链接
      -->
      <router-view v-slot="{ Component }">
        <!--
          保持 DataView 的实例不被销毁（对应之前 v-show 的“保持挂载”语义）
          include 依赖组件的 name，这里通过 DataView.vue 的 defineOptions({ name: 'DataView' }) 保证命中
        -->
        <keep-alive include="DataView">
          <component 
            :is="Component" 
            v-bind="currentViewProps" 
            @switch-tab="switchTab" 
            @api-updated="handleApiUpdated" 
          />
        </keep-alive>
      </router-view>
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
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Zap, PieChart, Network, Flag, Settings, Flame, Github, Sun, Moon } from 'lucide-vue-next'
import logo from './logo/logo-light.png'
import { useConfigStore } from './stores/config'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()

// 允许切换的页面（与路由 name 对齐），用于保证 switchTab 输入安全
const TABS = ['home', 'hot', 'data', 'arch', 'vision', 'settings']
const isTab = (value) => typeof value === 'string' && TABS.includes(value)

const isDark = computed(() => configStore.isDarkMode)

// 当前页面：来源于路由 name（避免再维护一份本地 tab 状态）
const currentTab = computed(() => (isTab(route.name) ? route.name : 'home'))

// 向路由页面透传的 props：
// - vision 页面原本“始终深色/不接收 darkMode”，因此不传 darkMode
// - 其他页面沿用 :dark-mode="isDark" 的行为（对应 prop 名 darkMode）
const currentViewProps = computed(() => {
  if (currentTab.value === 'vision') return {}
  return { darkMode: isDark.value }
})

const toggleTheme = () => {
  configStore.toggleDarkMode()
}

// 顶部导航切换：通过 push 跳转路由，从而同步 URL
const switchTab = (tab) => {
  const nextTab = isTab(tab) ? tab : 'home'
  if (route.name !== nextTab) {
    router.push({ name: nextTab })
  }
  window.scrollTo(0, 0)
}

const handleApiUpdated = () => {
  // API更新后的处理
}

onMounted(() => {
  configStore.initDarkMode()
  
  // 首次访问自动进入“愿景与价值”，之后保持用户上次访问路径（支持直达链接）
  const hasVisited = localStorage.getItem('globalinsight_has_visited')
  if (!hasVisited) {
    localStorage.setItem('globalinsight_has_visited', 'true')
    if (route.name !== 'vision') {
      router.replace({ name: 'vision' })
    }
  }
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
