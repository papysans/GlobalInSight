<template>
  <div class="min-h-screen flex flex-col transition-colors duration-300"
       :class="isDark ? 'bg-slate-900' : 'bg-slate-50'">
    <!-- Navigation Bar -->
    <nav class="sticky top-0 z-50 backdrop-blur-md border-b shadow-sm transition-colors duration-300"
         :class="isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white/90 border-slate-200'">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <router-link to="/" class="flex items-center gap-2 cursor-pointer">
            <img :src="logo" alt="Logo" class="w-16 h-16 object-cover" :class="isDark ? '' : 'mix-blend-multiply'" />
            <span class="text-xl font-bold tracking-tight transition-colors" :class="isDark ? 'text-white' : 'text-slate-800'">
              股讯通 <span :class="isDark ? 'text-blue-400' : 'text-blue-600'" class="font-mid">StockPulse</span>
            </span>
          </router-link>

          <div
            class="hidden md:flex items-center gap-2 text-sm font-medium p-1 rounded-full border transition-colors duration-300"
            :class="isDark ? 'text-slate-300 bg-slate-800/50 border-slate-600' : 'text-slate-600 bg-slate-100/50 border-slate-200/50'">
            <router-link to="/"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1',
                       isActive('/') ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <Flame class="w-3 h-3" /> 股票热榜
            </router-link>
            <router-link to="/analysis"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1',
                       isActive('/analysis') ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <Zap class="w-3 h-3" /> 行情推演
            </router-link>
            <router-link to="/daily-report"
              :class="['nav-link px-4 py-1.5 rounded-full transition-all flex items-center gap-1',
                       isActive('/daily-report') ? (isDark ? 'active-dark' : 'active') : '',
                       isDark ? 'hover:text-blue-400' : 'hover:text-blue-600']">
              <FileText class="w-3 h-3" /> 每日速报
            </router-link>
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

            <router-link to="/settings"
              class="p-2 rounded-full transition-colors flex items-center gap-1"
              :class="isDark ? 'text-slate-400 hover:text-blue-400 hover:bg-slate-700' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'"
              title="设置">
              <Settings class="w-5 h-5" />
              <span class="text-xs font-bold hidden sm:inline">设置</span>
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow relative">
      <router-view />
    </main>

    <!-- Global Footer -->
    <footer class="border-t py-4 transition-colors duration-300"
            :class="isDark ? 'bg-slate-900/80 border-slate-700' : 'bg-white border-slate-200'">
      <div class="max-w-7xl mx-auto px-4 text-center">
        <p class="text-xs font-medium" :class="isDark ? 'text-slate-400' : 'text-slate-500'">
          股讯通 StockPulse · Powered by Multi-Agent Debate + LangGraph
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Zap, FileText, Settings, Flame, Github, Sun, Moon } from 'lucide-vue-next'
import logo from './logo/logo-light.png'
import { useConfigStore } from './stores/config'

const route = useRoute()
const configStore = useConfigStore()

const isDark = computed(() => configStore.isDarkMode)

const toggleTheme = () => {
  configStore.toggleDarkMode()
}

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

// Initialize dark mode on app load
configStore.initDarkMode()
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
