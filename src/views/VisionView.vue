<template>
  <div class="view-section animate-fade-in py-12 px-4">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-16">
        <h2 class="text-3xl font-bold text-slate-900 mb-4">愿景与长期价值</h2>
        <p class="text-slate-500 max-w-2xl mx-auto">打破单一模型局限，构建跨语言、跨文化的事实核查与内容生产新范式。</p>
      </div>

      <div class="grid md:grid-cols-2 gap-8">
        <div class="bg-gradient-to-br from-blue-50 to-white p-8 rounded-2xl border border-blue-100 shadow-lg relative overflow-hidden group hover:shadow-xl transition-all">
          <div class="absolute top-0 right-0 w-32 h-32 bg-blue-100 rounded-bl-full opacity-50 transition-transform group-hover:scale-110"></div>
          <div class="relative z-10">
            <div class="w-10 h-10 bg-blue-600 text-white rounded-lg flex items-center justify-center mb-6">
              <Flag class="w-5 h-5" />
            </div>
            <h3 class="text-xl font-bold text-slate-900 mb-4">MVP 阶段目标</h3>
            <ul class="space-y-4 text-slate-600">
              <li class="flex items-start gap-3">
                <CheckCircle2 class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-slate-800">全链路跑通</span>
                  <p class="text-sm">实现微博与外媒（如CNN）对同一热点的自动聚合与对齐。</p>
                </div>
              </li>
              <li class="flex items-start gap-3">
                <CheckCircle2 class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-slate-800">可视化交互</span>
                  <p class="text-sm">前端直观展示"AI辩论团"寻找事实冲突的思考过程。</p>
                </div>
              </li>
              <li class="flex items-start gap-3">
                <CheckCircle2 class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-slate-800">生产力落地</span>
                  <p class="text-sm">实现"小红书"风格文案的一键生成，风格符合度达 90%。</p>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div class="bg-gradient-to-br from-purple-50 to-white p-8 rounded-2xl border border-purple-100 shadow-lg relative overflow-hidden group hover:shadow-xl transition-all">
          <div class="absolute top-0 right-0 w-32 h-32 bg-purple-100 rounded-bl-full opacity-50 transition-transform group-hover:scale-110"></div>
          <div class="relative z-10">
            <div class="w-10 h-10 bg-purple-600 text-white rounded-lg flex items-center justify-center mb-6">
              <Telescope class="w-5 h-5" />
            </div>
            <h3 class="text-xl font-bold text-slate-900 mb-4">长期战略展望</h3>
            <ul class="space-y-4 text-slate-600">
              <li class="flex items-start gap-3">
                <ArrowRightCircle class="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-slate-800">SaaS 创作工具</span>
                  <p class="text-sm">面向自媒体创作者，大幅提升热点追踪与内容生产效率。</p>
                </div>
              </li>
              <li class="flex items-start gap-3">
                <ArrowRightCircle class="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-slate-800">跨文化事实核查</span>
                  <p class="text-sm">构建开放平台，通过 AI 对抗虚假新闻，打破全球信息壁垒。</p>
                </div>
              </li>
              <li class="flex items-start gap-3">
                <ArrowRightCircle class="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-slate-800">API 生态开放</span>
                  <p class="text-sm">赋能第三方应用接入 GrandChart 的舆情分析能力。</p>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Flag, CheckCircle2, Telescope, ArrowRightCircle } from 'lucide-vue-next'
</script>