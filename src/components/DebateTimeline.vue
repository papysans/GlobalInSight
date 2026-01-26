<template>
  <div class="debate-timeline">
    <div v-for="(item, index) in timeline" :key="index" class="timeline-item mb-6 last:mb-0">
      <!-- 时间线节点 -->
      <div class="flex items-start gap-4">
        <!-- 左侧：轮次标记 -->
        <div class="flex flex-col items-center flex-shrink-0">
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-lg">
            R{{ item.round }}
          </div>
          <div v-if="index < timeline.length - 1" class="w-0.5 h-16 bg-gradient-to-b from-blue-500 to-purple-600 mt-2"></div>
        </div>

        <!-- 右侧：内容 -->
        <div class="flex-1 pt-1">
          <div class="bg-slate-50 dark:bg-slate-700 rounded-lg p-4 border-l-4 border-blue-500">
            <div class="text-sm font-bold text-slate-800 dark:text-slate-100 mb-2">{{ item.title }}</div>
            
            <!-- 内容区域 -->
            <div class="relative">
              <div 
                :class="[
                  'overflow-hidden transition-all duration-300 ease-in-out',
                  expandedStates[index] ? 'max-h-[1000px]' : 'max-h-20'
                ]"
              >
                <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{{ item.insight }}</p>
              </div>
              
              <!-- 渐变遮罩 -->
              <div 
                v-if="!expandedStates[index] && needsExpansion(item.insight)" 
                class="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-slate-50 dark:from-slate-700 to-transparent pointer-events-none"
              ></div>
            </div>
            
            <!-- 展开/收起按钮 -->
            <button 
              v-if="needsExpansion(item.insight)"
              @click="toggleExpand(index)"
              class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-xs mt-2 flex items-center gap-1 transition-colors"
            >
              {{ expandedStates[index] ? '收起' : '展开全文' }}
              <ChevronDown 
                :class="{ 'rotate-180': expandedStates[index] }" 
                class="w-3 h-3 transition-transform duration-300" 
              />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 总结 -->
    <div v-if="timeline.length > 0" class="summary mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-slate-700 dark:to-slate-800 rounded-lg border border-blue-200 dark:border-slate-600">
      <div class="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
        <CheckCircle class="w-4 h-4 text-green-600 dark:text-green-400" />
        <span>经过 <strong>{{ timeline.length }}轮</strong> 辩论，AI推理最终收敛</span>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="timeline.length === 0" class="text-center py-8 text-slate-500 dark:text-slate-400">
      <div class="text-sm">暂无辩论数据</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CheckCircle, ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  timeline: {
    type: Array,
    default: () => []
  }
})

// 展开状态
const expandedStates = ref({})

// 判断是否需要展开按钮（内容超过80字符）
const needsExpansion = (text) => {
  return text && text.length > 80
}

// 切换展开/收起状态
const toggleExpand = (index) => {
  expandedStates.value[index] = !expandedStates.value[index]
}
</script>
