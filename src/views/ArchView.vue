<template>
  <div class="view-section animate-fade-in py-12 px-4">
    <div class="max-w-6xl mx-auto">
      <div class="text-center mb-12">
        <h2 class="text-3xl font-bold text-slate-900 mb-4">系统技术架构</h2>
        <p class="text-slate-500">基于多智能体（Multi-Agent）协作的端到端生成流水线</p>
      </div>
      
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 md:p-12">
        <div class="grid md:grid-cols-3 gap-8">
          <div class="space-y-4">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                <Satellite class="w-6 h-6" />
              </div>
              <h3 class="font-bold text-lg text-slate-800">1. 感知层 (Sensing)</h3>
            </div>
            <p class="text-sm text-slate-500 mb-2">分布式全网数据聚合</p>
            <div class="bg-slate-50 p-4 rounded-lg border border-slate-100 text-sm space-y-3 text-slate-600">
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>爬虫集群:</strong> Selenium + Scrapy 处理动态网页，实时抓取微博/Twitter数据。</span>
              </div>
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>数据清洗:</strong> NLP 去重与情感预标记，剔除无效噪点。</span>
              </div>
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>存储:</strong> Elasticsearch 异构数据库，支持毫秒级检索。</span>
              </div>
            </div>
          </div>

          <div class="space-y-4 relative">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600">
                <BrainCircuit class="w-6 h-6" />
              </div>
              <h3 class="font-bold text-lg text-slate-800">2. 协作层 (Core)</h3>
            </div>
            <p class="text-sm text-slate-500 mb-2">LLM 智能体编排中心</p>
            <div class="bg-slate-50 p-4 rounded-lg border border-slate-100 text-sm space-y-3 text-slate-600">
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-purple-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>Moderator:</strong> 辩论流程控制与防死循环机制。</span>
              </div>
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-purple-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>Debater:</strong> 模拟正反方多视角，进行事实核查与观点碰撞。</span>
              </div>
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-purple-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>CoStrict:</strong> 思维链(CoT)逻辑修正，减少幻觉。</span>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                <Layout class="w-6 h-6" />
              </div>
              <h3 class="font-bold text-lg text-slate-800">3. 交互层 (Interaction)</h3>
            </div>
            <p class="text-sm text-slate-500 mb-2">可视化与内容生成</p>
            <div class="bg-slate-50 p-4 rounded-lg border border-slate-100 text-sm space-y-3 text-slate-600">
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-green-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>后端:</strong> Python FastAPI + WebSocket 实现流式传输。</span>
              </div>
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-green-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>前端:</strong> Vue.js + ECharts + Tailwind 构建响应式界面。</span>
              </div>
              <div class="flex items-start gap-2">
                <div class="w-2 h-2 bg-green-500 rounded-full mt-1.5 flex-shrink-0"></div>
                <span><strong>输出:</strong> 小红书/抖音风格爆款文案一键生成。</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Satellite, BrainCircuit, Layout } from 'lucide-vue-next'
</script>