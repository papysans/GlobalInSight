<template>
  <div class="insight-card bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
    <!-- 标题 -->
    <div class="flex items-center gap-2 mb-4">
      <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
        <Lightbulb class="w-5 h-5 text-blue-600" />
      </div>
      <h3 class="text-xl font-bold text-slate-900">核心洞察</h3>
    </div>

    <!-- 结论 -->
    <div class="conclusion-section mb-6">
      <p class="text-base text-slate-700 leading-relaxed">
        {{ conclusion }}
      </p>
    </div>

    <!-- 数据概览 -->
    <div class="overview-section mb-6 bg-slate-50 rounded-lg p-4">
      <h4 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
        <BarChart3 class="w-4 h-4 text-slate-600" />
        数据概览
      </h4>
      <div class="grid grid-cols-2 gap-3">
        <div class="stat-item">
          <div class="text-xs text-slate-500">话题覆盖</div>
          <div class="text-lg font-bold text-blue-600">{{ coverage.platforms }}个平台</div>
        </div>
        <div v-if="coverage.debateRounds" class="stat-item">
          <div class="text-xs text-slate-500">辩论轮次</div>
          <div class="text-lg font-bold text-purple-600">{{ coverage.debateRounds }}轮推演</div>
        </div>
        <div v-if="coverage.growth" class="stat-item">
          <div class="text-xs text-slate-500">生命周期</div>
          <div class="text-lg font-bold text-green-600">{{ coverage.growth }}</div>
        </div>
        <div class="stat-item">
          <div class="text-xs text-slate-500">争议程度</div>
          <div class="text-lg font-bold" :class="controversyColor">
            {{ formatControversy(coverage.controversy) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 关键发现 -->
    <div v-if="keyFinding" class="key-finding-section">
      <div class="flex items-start gap-2">
        <Target class="w-4 h-4 text-orange-500 mt-1 flex-shrink-0" />
        <div>
          <div class="text-xs font-bold text-slate-700 mb-1">关键发现</div>
          <p class="text-sm text-slate-600">{{ keyFinding }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Lightbulb, BarChart3, Target } from 'lucide-vue-next'

const props = defineProps({
  dataSource: {
    type: String,
    default: 'workflow'
  },
  conclusion: {
    type: String,
    default: '暂无洞察'
  },
  coverage: {
    type: Object,
    default: () => ({
      platforms: 0,
      debateRounds: 0,
      growth: '',
      controversy: 0
    })
  },
  keyFinding: {
    type: String,
    default: ''
  }
})

const controversyColor = computed(() => {
  const c = props.coverage.controversy
  if (typeof c === 'number') {
    return c > 7 ? 'text-red-600' : c > 4 ? 'text-orange-600' : 'text-green-600'
  }
  return c === '高' ? 'text-red-600' : c === '中' ? 'text-orange-600' : 'text-green-600'
})

const formatControversy = (c) => {
  if (typeof c === 'number') {
    return `${c.toFixed(1)}/10`
  }
  return c
}
</script>
