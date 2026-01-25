<template>
  <div class="view-section animate-fade-in">
    <header class="relative bg-white border-b border-slate-100 pt-12 pb-8 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mb-4">
          舆情洞察与<span class="gradient-text">爆款文案生成</span>引擎
        </h1>

        <div class="max-w-2xl mx-auto mt-8 relative z-10">
          <div class="relative group">
            <div
              class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200">
            </div>
            <div class="relative flex items-center bg-white rounded-xl shadow-xl border border-slate-200 p-1">
              <div class="pl-4 text-slate-400">
                <Search class="w-5 h-5" />
              </div>
              <input v-model="topic" type="text"
                class="w-full py-3 px-4 text-slate-700 bg-transparent outline-none placeholder:text-slate-400"
                placeholder="输入您想了解的任何议题..." @keyup.enter="handleStart" />

              <div class="h-8 border-l border-slate-200 mx-2"></div>

              <div class="flex items-center gap-2 pr-2" title="辩论轮数">
                <span class="text-xs text-slate-400 font-bold whitespace-nowrap">轮数:</span>
                <input v-model.number="debateRounds" type="number" min="1" max="5"
                  class="w-12 py-1 px-2 text-center text-sm border border-slate-200 rounded-lg outline-none focus:border-blue-500" />
              </div>

              <button @click="handleStart" :class="[
                'px-6 py-2 text-white font-medium rounded-lg transition-colors flex items-center gap-2 shadow-md whitespace-nowrap min-w-[120px] justify-center',
                isLoading ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
              ]">
                <component :is="isLoading ? Square : Sparkles" class="w-4 h-4" />
                {{ isLoading ? '停止分析' : '启动分析' }}
              </button>
              
               <!-- Debug/Preview Button -->
               <!-- Debug/Preview Button (Hidden for production but kept for dev) -->
               <!-- <button
                @click="debugPreviewTheme"
                class="ml-2 px-3 py-2 text-slate-500 hover:text-blue-600 bg-white border border-slate-200 hover:border-blue-300 rounded-lg transition-all text-xs flex items-center gap-1 shadow-sm whitespace-nowrap"
                title="调试：随机生成标题卡样式"
              >
                <span>🎨</span>
                <span>换样式</span>
              </button> -->
            </div>
          </div>

          <div class="mt-4 flex flex-nowrap justify-center items-center gap-2 text-xs text-slate-500">
            <div class="flex items-center gap-1 font-bold text-red-500 whitespace-nowrap">
              <TrendingUp class="w-3 h-3" />
              <span>{{ trendingDate }}热搜:</span>
            </div>
            <div class="flex gap-2 flex-nowrap items-center">
              <button v-for="(t, idx) in trendingTopics" :key="idx" @click="topic = t.title"
                class="px-3 py-1 bg-white border border-slate-200 rounded-full hover:border-blue-300 hover:text-blue-600 transition-colors animate-fade-in text-xs whitespace-nowrap">
                {{ t.short || t.title }}
              </button>
            </div>
            <button @click="rotateTrending"
              class="ml-1 p-1 hover:bg-slate-100 rounded-full text-slate-400 transition-colors shrink-0" title="刷新热搜">
              <RefreshCw class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- 顶部进度条 -->
    <div v-if="isLoading && workflowStatus.running"
      class="sticky top-16 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-3">
        <div class="flex items-center gap-4">
          <div class="flex-1">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-medium text-slate-700">{{ currentStepText }}</span>
              <span class="text-xs font-bold text-blue-600">{{ displayProgress }}%</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div
                class="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full transition-all duration-500 ease-out"
                :style="{ width: displayProgress + '%' }"></div>
            </div>
          </div>
          <div class="text-xs text-slate-500 whitespace-nowrap">
            {{ elapsedTime }}
          </div>
        </div>
      </div>
    </div>

    <section class="py-8 px-4 max-w-7xl mx-auto space-y-8">
      <!-- 步骤列表卡片 -->
      <div v-show="isLoading && workflowStatus.running" class="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
        <h3 class="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
          <Activity class="w-4 h-4 text-blue-600" /> 工作流进度
        </h3>
        <!-- 6步仍保持一行：提高列数 + 压缩卡片尺寸 -->
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          <div v-for="step in workflowSteps" :key="step.key" :class="[
            'px-2 py-2.5 min-h-[64px] rounded-lg border-2 transition-all',
            getStepClass(step.key)
          ]">
            <div class="flex items-center gap-1.5 mb-0.5">
              <component :is="step.icon" :class="['w-3.5 h-3.5', getStepIconClass(step.key)]" />
              <span class="text-[11px] font-bold leading-tight" :class="getStepTextClass(step.key)">
                {{ step.name }}
              </span>
            </div>
            <div class="text-[9px] text-slate-400 mt-1.5 leading-tight">
              <span
                v-if="step.key === 'crawler_agent' && workflowStatus.current_step === 'crawler_agent' && workflowStatus.current_platform"
                class="text-blue-600 font-bold platform-crawling line-clamp-1">
                正在爬取 {{ workflowStatus.current_platform }}...
              </span>
              <span v-else class="line-clamp-1">{{ step.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <!-- Left: Debate & Insight -->
        <div class="lg:col-span-7 flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between px-1 h-8">
              <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Cpu class="w-5 h-5 text-blue-600" /> 智能体协作 (Multi-Agent Debate)
              </h2>
              <div v-if="isLoading" class="flex items-center gap-2">
                <div
                  class="px-3 py-1 bg-green-50 text-green-700 rounded-full border border-green-100 text-xs font-medium flex items-center gap-2">
                  <span class="relative flex h-2 w-2">
                    <span
                      class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  <span>Real-time Inference</span>
                </div>
              </div>
            </div>

            <div
              class="glass-card rounded-xl flex flex-col border-t-4 border-t-blue-500 h-[450px] shadow-lg relative overflow-hidden">
              <div
                class="p-3 bg-slate-50/80 border-b border-slate-100 flex justify-between items-center backdrop-blur text-xs font-bold text-slate-600 z-10">
                <span>AI 辩论过程实时推演</span>
                <span class="text-slate-400 font-normal text-[10px]">{{ activeModelDisplay }}</span>
              </div>
              <div
                ref="debateContainerRef"
                class="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-4 text-sm bg-white/50 relative scroll-smooth">
                <!-- 调试信息 -->
                <div v-if="false" class="text-xs text-red-500 p-2 bg-red-50 mb-2">
                  调试: debateLogs.length={{ debateLogs.length }}, storeLogs.length={{ storeLogs.length }}
                </div>
                <div v-if="debateLogs.length === 0"
                  class="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
                  <Bot class="w-16 h-16 mb-4 stroke-1" />
                  <p>等待指令启动...</p>
                  <p class="text-xs mt-2 text-slate-300">Store日志数: {{ storeLogs.length }} | 显示日志数: {{ debateLogs.length
                  }}</p>
                </div>
                <div v-for="(log, idx) in debateLogs" :key="`log-${idx}-${log.name}`" :class="[
                  'debate-bubble p-3 rounded-lg border text-xs leading-relaxed mb-3 shadow-sm bg-white animate-fade-in',
                  getBubbleClass(log.role)
                ]">
                  <div
                    class="font-bold mb-1 opacity-80 flex justify-between items-center border-b border-slate-200/50 pb-1 mb-2">
                    <span class="flex items-center gap-1">
                      <component :is="getIcon(log.role)" class="w-3 h-3" />
                      {{ log.name }}
                    </span>
                    <span v-if="log.model" class="text-[9px] font-normal text-slate-400 bg-slate-50 px-1 rounded">
                      {{ log.model }}
                    </span>
                  </div>
                  <div class="text-slate-700 prose prose-xs max-w-none" v-html="renderMarkdown(log.content)"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2 px-1">
              <Lightbulb class="w-5 h-5 text-yellow-500" /> 核心洞察 (Grand Insight)
            </h2>
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-yellow-400 min-h-[140px] flex flex-col">
              <div class="text-sm text-slate-600 leading-relaxed flex-1 flex flex-col">
                <div v-if="!insight"
                  class="h-full flex items-center justify-center text-slate-400 border border-dashed border-slate-200 rounded-lg p-3 bg-slate-50/50 italic text-xs">
                  等待辩论结论产出...
                </div>
                <div v-else
                  class="animate-fade-in p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg border border-yellow-100 text-slate-700 shadow-sm h-full overflow-y-auto">
                  <strong class="text-orange-600 block mb-2 flex items-center gap-1 text-sm uppercase tracking-wider">
                    <Zap class="w-4 h-4" /> Grand Insight
                  </strong>
                  <p class="text-sm leading-relaxed">{{ insight }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: XHS Preview -->
        <div class="lg:col-span-5 flex flex-col gap-2">
          <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2 px-1">
            <Smartphone class="w-5 h-5 text-purple-600" /> 实时生成预览 (Preview)
          </h2>


          <div class="glass-card p-6 rounded-xl shadow-lg flex justify-center bg-slate-100/50">
            <div
              class="glass-card rounded-[3rem] overflow-hidden shadow-2xl bg-white w-full max-w-[320px] h-[680px] flex flex-col transform transition hover:scale-[1.02] duration-300"
              style="border: 8px solid #1e293b;">
              <!-- Status Bar -->
              <div class="relative bg-white px-5 h-10 flex items-center justify-between z-10 flex-shrink-0 select-none">
                <span class="text-[10px] font-bold text-slate-900 w-8">09:41</span>
                <div
                  class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-6 bg-black rounded-full flex justify-center items-center">
                  <div class="w-1.5 h-1.5 bg-gray-800 rounded-full absolute right-4"></div>
                </div>
                <div class="w-8 flex justify-end">
                  <Wifi class="w-3 h-3 text-slate-900" />
                </div>
              </div>

              <!-- App Header (XHS-like) -->
              <div
                class="h-12 px-4 bg-white flex items-center justify-between border-b border-slate-100 flex-shrink-0 select-none">
                <div class="flex items-center gap-2 min-w-0">
                  <ChevronLeft class="w-5 h-5 text-slate-900" />
                  <div
                    class="w-7 h-7 rounded-full bg-slate-200 overflow-hidden flex items-center justify-center flex-shrink-0">
                    <Bot class="w-4 h-4 text-slate-500" />
                  </div>
                  <div class="min-w-0">
                    <div class="text-xs font-bold text-slate-900 truncate">{{ xhsPreview.title ? 'Napstablook' : '预览' }}
                    </div>
                    <div class="text-[10px] text-slate-400 truncate">已关注</div>
                  </div>
                </div>

                <div class="flex items-center gap-2 flex-shrink-0">
                  <button
                    class="px-3 py-1 rounded-full text-[10px] font-bold border border-slate-200 text-slate-700 bg-white">
                    已关注
                  </button>
                  <Share2 class="w-4 h-4 text-slate-700" />
                </div>
              </div>

              <!-- Screen Content -->
              <div class="relative cursor-pointer group flex-1 flex flex-col overflow-hidden bg-white"
                @click="switchPhoneImage" title="点击切换配图风格">

                <!-- 可滚动内容区 -->
                <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
                  <!-- 图片区域：位于文案上方 -->
                  <div 
                    class="relative overflow-hidden flex-shrink-0 transition-colors duration-500 aspect-[3/4] bg-slate-100"
                  >
                    <!-- 优先显示生成的 AI 图片（固定容器比例 + 图片铺满，消除布局抖动） -->
                    <div
                      class="relative w-full h-full"
                      style="touch-action: pan-y;"
                      @pointerdown="onPhonePointerDown"
                      @pointermove="onPhonePointerMove"
                      @pointerup="onPhonePointerUp"
                      @pointercancel="onPhonePointerUp"
                    >
                      <transition name="image-fade" mode="out-in">
                        <!-- Case 1: Title Card (Index 0) -->
                        <!-- Case 1: Title Card (Index 0) -->
                        <!-- Case 1: Title Card (Index 0) -->
                        <XiaohongshuCard 
                            v-if="currentDisplayIndex === 0" 
                            key="title-card"
                            ref="xiaohongshuCardRef"
                            :title="xhsPreview.title"
                            :emoji="analysisStore.titleEmoji"
                            :theme="analysisStore.titleTheme"
                            :emoji-pos="emojiPosition"
                            @emoji-click="randomizeEmojiPosition"
                            class="absolute inset-0"
                        />

                        <!-- Case 2: AI Images (Index > 0) -->
                        <img
                          v-else
                          :key="'img-' + currentDisplayIndex"
                          :src="analysisStore.imageUrls[currentDisplayIndex - 1]"
                          class="absolute inset-0 w-full h-full object-cover block"
                          alt="AI Generated"
                          draggable="false"
                          loading="lazy"
                          decoding="async"
                          @load="imageLoading = false"
                          @error="imageLoading = false"
                        />
                      </transition>
                      
                      <!-- 加载指示器 -->
                      <div v-if="imageLoading && currentDisplayIndex > 0" 
                        class="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm z-10">
                        <Loader2 class="w-6 h-6 text-blue-600 animate-spin" />
                      </div>

                      <!-- AI 生成提示 (Only for AI Images) -->
                      <div v-if="currentDisplayIndex > 0"
                        class="absolute top-2 left-2 flex items-center gap-1 bg-white/80 text-slate-700 text-[10px] px-2 py-1 rounded-full backdrop-blur-sm border border-slate-100">
                        <AlertTriangle class="w-3 h-3 text-slate-700" />
                        <span>内容可能使用AI技术生成</span>
                      </div>

                      <!-- 多图指示器 (Title Card + AI Images) -->
                       <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5 z-20">
                        <!-- Dot for Title Card -->
                        <div :class="[
                          'w-1.5 h-1.5 rounded-full transition-all duration-300',
                          currentDisplayIndex === 0 ? 'bg-white scale-125' : 'bg-white/50'
                        ]"></div>
                        <!-- Dots for AI Images -->
                        <div v-for="(_, i) in analysisStore.imageUrls" :key="i" :class="[
                          'w-1.5 h-1.5 rounded-full transition-all duration-300',
                          currentDisplayIndex === (i + 1) ? 'bg-white scale-125' : 'bg-white/50'
                        ]"></div>
                      </div>

                      <div
                        class="absolute bottom-2 right-2 bg-black/50 text-white text-[10px] px-2 py-1 rounded-full backdrop-blur-sm">
                        {{ currentDisplayIndex + 1 }} / {{ (analysisStore.imageUrls?.length || 0) + 1 }}
                      </div>
                    </div><!-- End of phone image container -->
                  </div><!-- End of aspect ratio container -->

                  <!-- 文案区域 -->
                  <div class="p-4 flex-1 flex flex-col">
                    <h4 class="font-bold text-sm text-slate-900 mb-2">
                      {{ xhsPreview.title || '标题生成中...' }}
                    </h4>
                    <div class="text-xs text-slate-600 space-y-2 flex-1">
                      <div v-if="!xhsPreview.content" class="space-y-2">
                        <div class="h-2 bg-slate-100 rounded w-full animate-pulse"></div>
                        <div class="h-2 bg-slate-100 rounded w-5/6 animate-pulse"></div>
                        <div class="h-2 bg-slate-100 rounded w-4/6 animate-pulse"></div>
                      </div>
                      <div v-else class="prose prose-xs max-w-none" v-html="renderMarkdown(xhsPreview.content)"></div>
                    </div>
                  </div>
                </div><!-- End of scrollable content -->

                <!-- 底部固定互动栏 -->
                <div
                  class="px-4 py-3 border-t border-slate-100 flex items-center justify-between text-slate-500 text-[10px] bg-white z-10 flex-shrink-0">
                  <div class="flex-1 mr-3">
                    <div
                      class="w-full rounded-full bg-slate-100 text-slate-400 px-3 py-2 text-[10px] border border-slate-100">
                      说点什么...
                    </div>
                  </div>
                  <div class="flex items-center gap-3 text-slate-500">
                    <span class="whitespace-nowrap">
                      <Heart class="w-3 h-3 inline" /> 57
                    </span>
                    <span class="whitespace-nowrap">
                      <Star class="w-3 h-3 inline" /> 15
                    </span>
                    <span class="whitespace-nowrap">
                      <MessageCircle class="w-3 h-3 inline" /> 44
                    </span>
                  </div>
                </div>
              </div><!-- End of Screen Content -->
            </div><!-- End of Phone Frame -->
          </div><!-- End of Glass Card -->
        </div><!-- End of Right Column -->
      </div>

      <!-- Copywriting Section -->
      <div class="flex flex-col gap-2">
        <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2 px-1">
          <PenTool class="w-5 h-5 text-emerald-600" /> 文案生成 (Copywriting)
        </h2>
        <div class="glass-card rounded-xl p-6 shadow-lg border-t-4 border-t-emerald-500">
          <div v-if="isLoading" class="flex items-center gap-2 mb-4 text-sm font-bold text-emerald-600 animate-pulse">
            <Loader2 class="w-4 h-4 animate-spin" /> 正在后台处理信息，生成最终文案...
          </div>

          <div class="relative">
            <textarea :value="finalCopy" readonly
              class="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 font-mono resize-none focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="等待辩论结束后，在此生成可直接发布的文案..."></textarea>
            <button @click="analysisStore.startEditing"
              :disabled="!finalCopy || finalCopy.length === 0"
              class="absolute top-3 right-64 px-3 py-1.5 bg-blue-600 border border-blue-600 hover:bg-blue-700 text-white rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
              <Edit class="w-3 h-3" />
              编辑
            </button>
            <button @click="exportAllImages"
              :disabled="isExportingImages || !(analysisStore.imageUrls && analysisStore.imageUrls.length)"
              class="absolute top-3 right-28 px-3 py-1.5 bg-blue-600 border border-blue-600 hover:bg-blue-700 text-white rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
              <Download class="w-3 h-3" />
              {{ isExportingImages ? '导出中...' : '导出全部图片' }}
            </button>
            <button @click="copyToClipboard" :disabled="!finalCopy || finalCopy.length === 0"
              class="absolute top-3 right-3 px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
              <Copy class="w-3 h-3" /> 复制全文
            </button>
          </div>

          <!-- 编辑面板 -->
          <CopywritingEditor />

          <!-- 底部栏：状态指示 + 发布按钮 -->
          <div class="mt-2 flex items-center justify-between px-1">
            <!-- 小红书 MCP 状态指示 -->
            <div class="flex items-center gap-2 text-[10px]">
              <div v-if="xhsStatus.loading" class="text-slate-400 flex items-center gap-1">
                <Loader2 class="w-2.5 h-2.5 animate-spin" /> 检查服务...
              </div>
              <div v-else-if="xhsStatus.mcp_available && xhsStatus.login_status" class="text-green-600 flex items-center gap-1" title="服务正常，已登录">
                <Check class="w-2.5 h-2.5" /> 小红书已连接
              </div>
              <div v-else-if="xhsStatus.mcp_available && !xhsStatus.login_status" class="text-orange-500 flex items-center gap-1 cursor-help" title="MCP服务已启动，但需要登录小红书">
                <AlertTriangle class="w-2.5 h-2.5" /> 需登录小红书
              </div>
              <div v-else class="text-slate-400 flex items-center gap-1 cursor-help" title="请先启动 xiaohongshu-mcp 服务">
                <XCircle class="w-2.5 h-2.5" /> 服务未连接
              </div>
            </div>

            <!-- 小红书发布按钮 -->
            <button @click="publishToXhs" 
              :disabled="!finalCopy || finalCopy.length === 0 || isPublishing || !xhsStatus.mcp_available || !xhsStatus.login_status"
              :class="[
                'px-3 py-1.5 rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed',
                (!xhsStatus.mcp_available || !xhsStatus.login_status) ? 'bg-slate-100 text-slate-400 border border-slate-200' : 'bg-red-500 hover:bg-red-600 text-white border border-red-500'
              ]"
              :title="(!xhsStatus.mcp_available ? 'MCP服务未启动' : (!xhsStatus.login_status ? '小红书未登录' : '点击发布'))"
            >
              <Upload v-if="!isPublishing" class="w-3 h-3" />
              <Loader2 v-else class="w-3 h-3 animate-spin" />
              {{ isPublishing ? '发布中...' : '发布到小红书' }}
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Search, Sparkles, Square, TrendingUp, RefreshCw, Cpu, Bot, Lightbulb, Zap,
  Smartphone, Wifi, Image as ImageIcon, RefreshCcw, Heart, Star, MessageCircle, PenTool,
  ChevronLeft, Share2, AlertTriangle, Download, Upload, Check, XCircle,
  Loader2, Copy, Shield, ThumbsUp, ThumbsDown, Glasses, Activity,
  Database, FileText, Brain, MessageSquare, PenLine, CheckCircle2, Circle, Loader, Edit
} from 'lucide-vue-next'
import { useAnalysisStore } from '../stores/analysis'
import { useConfigStore } from '../stores/config'
import { useWorkflowStore } from '../stores/workflow'
import { api } from '../api'
import MarkdownIt from 'markdown-it'
import XiaohongshuCard from '../components/XiaohongshuCard.vue'
import CopywritingEditor from '../components/CopywritingEditor.vue'

const md = new MarkdownIt()
const analysisStore = useAnalysisStore()
const configStore = useConfigStore()
const workflowStore = useWorkflowStore()

// 使用 storeToRefs 确保响应式
const { logs: storeLogs, isEditing, editableContent } = storeToRefs(analysisStore)
const { status: workflowStatus } = storeToRefs(workflowStore)

const topic = ref('')
const xiaohongshuCardRef = ref(null)

const generateTitleCardImage = async () => {
  // Ensure component is mounted
  if (currentDisplayIndex.value !== 0) {
    currentDisplayIndex.value = 0
    await nextTick()
    // Give it a bit more time to mount and render
    await new Promise(resolve => setTimeout(resolve, 300))
  }
  
  // Polling for ref availability (max 5 attempts, 100ms interval)
  for (let i = 0; i < 5; i++) {
    if (xiaohongshuCardRef.value) {
      return await xiaohongshuCardRef.value.generateImage()
    }
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  throw new Error('XiaohongshuCard component not ready after waiting')
}

// 从热榜一键推演的缓存填充搜索框
const hydrateHotTopicDraft = () => {
  try {
    const cached = sessionStorage.getItem('hot_topic_draft')
    if (cached) {
      const parsed = JSON.parse(cached)
      if (parsed && parsed.title) {
        topic.value = parsed.title
      }
    }
  } catch (e) {
    console.warn('failed to hydrate hot_topic_draft', e)
  }
}

// 从 localStorage 恢复辩论轮数，如果没有则使用默认值 2
const loadDebateRounds = () => {
  const saved = localStorage.getItem('grandchart_debate_rounds')
  if (saved) {
    try {
      const rounds = parseInt(saved, 10)
      if (rounds >= 1 && rounds <= 5) {
        return rounds
      }
    } catch (e) {
      console.error('Failed to load debate rounds from localStorage:', e)
    }
  }
  return 2
}

const debateRounds = ref(loadDebateRounds())

// 监听辩论轮数变化，保存到 localStorage
watch(debateRounds, (newValue) => {
  if (newValue >= 1 && newValue <= 5) {
    localStorage.setItem('grandchart_debate_rounds', String(newValue))
    console.log('[HomeView] 辩论轮数已保存到 localStorage:', newValue)
  }
})
const isLoading = computed(() => analysisStore.isLoading)
const debateLogs = ref([])
const insight = computed(() => analysisStore.insight)
const xhsPreview = ref({ title: '', content: '' })
const isExportingImages = ref(false)
const finalCopy = computed(() => {
  if (analysisStore.finalCopy.title && analysisStore.finalCopy.body) {
    return `${analysisStore.finalCopy.title}\n\n${analysisStore.finalCopy.body}`
  }
  return ''
})
const activeModelDisplay = ref('')
const trendingDate = ref('')
const trendingTopics = ref([])
const trendingLoading = ref(false)
const hotItemsAll = ref([])
const hotWindowIndex = ref(0)
const HOT_WINDOW_SIZE = 3
const currentDisplayIndex = ref(0) // 0: Title Card, 1+: AI Images
const emojiPosition = ref('bottom-right') // top-left, top-right, bottom-left, bottom-right
const maxStepIndex = ref(-1)
const maxProgress = ref(0)
const preloadedImages = ref(new Set()) // 已预加载的图片URL集合
const imageLoading = ref(false) // 当前图片加载状态
const debateContainerRef = ref(null) // 辩论日志容器 ref

// 滚动到辩论日志底部
const scrollToBottom = () => {
  nextTick(() => {
    if (debateContainerRef.value) {
      debateContainerRef.value.scrollTop = debateContainerRef.value.scrollHeight
    }
  })
}

// 监听进度变化，记录达到的最高进度，防止在循环步骤中跳跃
watch(() => workflowStatus.value.progress, (newProgress) => {
  if (newProgress > maxProgress.value) {
    maxProgress.value = newProgress
  }
})

// 计算显示的进度，取当前进度和历史最高进度的最大值
const displayProgress = computed(() => {
  return Math.max(workflowStatus.value.progress || 0, maxProgress.value)
})

// 监听步骤变化，记录达到的最高步骤，防止在循环步骤中跳跃
watch(() => workflowStatus.value.current_step, (newStep) => {
  if (!newStep) return
  const idx = workflowSteps.findIndex(s => s.key === newStep)
  if (idx > maxStepIndex.value) {
    maxStepIndex.value = idx
  }
})



// Title Card Logic delegated to XiaohongshuCard component

// Title Card Customization Logic (Moved minimal logic, core logic in component)
// emojiPosition ref is kept for parent control if needed, but component handles its own display
// Actually we need emojiPosition state here because it's passed to component
// And randomizeEmojiPosition is used by the component event


// 随机化Emoji位置
const randomizeEmojiPosition = () => {
    const positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
    // 避免和当前位置一样
    let nextPos = emojiPosition.value
    while (nextPos === emojiPosition.value) {
        nextPos = positions[Math.floor(Math.random() * positions.length)]
    }
    emojiPosition.value = nextPos
}


// 工作流步骤配置
const workflowSteps = [
  { key: 'crawler_agent', name: '数据爬取', description: '收集多平台数据', icon: Database, progress: 10 },
  { key: 'reporter', name: '事实提取', description: '提取核心事实', icon: FileText, progress: 30 },
  { key: 'analyst', name: '舆情分析', description: '深度洞察分析', icon: Brain, progress: 40 },
  { key: 'debater', name: '智能辩论', description: '多角度辩论', icon: MessageSquare, progress: 60 },
  { key: 'writer', name: '文案生成', description: '生成爆款文案', icon: PenLine, progress: 80 },
  { key: 'image_generator', name: '配图生成', description: 'AI生成组图', icon: ImageIcon, progress: 95 }
]

// 获取步骤状态类
const getStepClass = (stepKey) => {
  const currentStep = workflowStatus.value.current_step
  const progress = workflowStatus.value.progress
  const stepIndex = workflowSteps.findIndex(s => s.key === stepKey)

  // 如果进度是100，所有步骤都显示完成
  if (progress === 100) {
    return 'border-green-200 bg-green-50'
  }

  if (!currentStep) {
    return 'border-slate-200 bg-slate-50'
  }

  const currentIndex = workflowSteps.findIndex(s => s.key === currentStep)

  if (stepIndex === currentIndex) {
    // 进行中
    return 'border-blue-500 bg-blue-50 shadow-md'
  } else if (stepIndex < currentIndex || stepIndex <= maxStepIndex.value) {
    // 已完成或已达到过
    return 'border-green-200 bg-green-50'
  } else {
    // 待执行
    return 'border-slate-200 bg-slate-50'
  }
}

// 获取步骤图标类
const getStepIconClass = (stepKey) => {
  const currentStep = workflowStatus.value.current_step
  const progress = workflowStatus.value.progress
  const stepIndex = workflowSteps.findIndex(s => s.key === stepKey)

  if (progress === 100) return 'text-green-600'
  if (!currentStep) return 'text-slate-400'

  const currentIndex = workflowSteps.findIndex(s => s.key === currentStep)

  if (stepIndex === currentIndex) {
    return 'text-blue-600 animate-pulse'
  } else if (stepIndex < currentIndex || stepIndex <= maxStepIndex.value) {
    return 'text-green-600'
  } else {
    return 'text-slate-400'
  }
}

// 获取步骤文字类
const getStepTextClass = (stepKey) => {
  const currentStep = workflowStatus.value.current_step
  const progress = workflowStatus.value.progress
  const stepIndex = workflowSteps.findIndex(s => s.key === stepKey)

  if (progress === 100) return 'text-green-700'
  if (!currentStep) return 'text-slate-500'

  const currentIndex = workflowSteps.findIndex(s => s.key === currentStep)

  if (stepIndex === currentIndex) {
    return 'text-blue-700'
  } else if (stepIndex < currentIndex || stepIndex <= maxStepIndex.value) {
    return 'text-green-700'
  } else {
    return 'text-slate-500'
  }
}

// 当前步骤文本
const currentStepText = computed(() => {
  const step = workflowSteps.find(s => s.key === workflowStatus.value.current_step)
  if (step) {
    return `正在${step.name}...`
  }
  return '准备中...'
})

// 已用时间
const elapsedTime = computed(() => {
  if (!workflowStatus.value.started_at) return ''

  const start = new Date(workflowStatus.value.started_at)
  const now = new Date()
  const diff = Math.floor((now - start) / 1000)

  if (diff < 60) {
    return `已用时 ${diff}秒`
  } else {
    const minutes = Math.floor(diff / 60)
    const seconds = diff % 60
    return `已用时 ${minutes}分${seconds}秒`
  }
})

const renderMarkdown = (text) => {
  if (!text) return ''
  return md.render(text)
}

const getBubbleClass = (role) => {
  const map = {
    moderator: 'border-yellow-200 bg-yellow-50',
    pro: 'border-blue-200 bg-blue-50',
    con: 'border-red-200 bg-red-50',
    analyst: 'border-purple-200 bg-purple-50',
    system: 'border-slate-100 bg-slate-50'
  }
  return map[role] || 'border-slate-200 bg-slate-50'
}

const getIcon = (role) => {
  const map = {
    moderator: Shield,
    pro: ThumbsUp,
    con: ThumbsDown,
    analyst: Glasses,
    system: Bot
  }
  return map[role] || Bot
}

const shortenHotTitle = (title, maxLen = 18) => {
  if (!title) return ''
  const clean = String(title).trim()
  if (clean.length <= maxLen) return clean
  return clean.slice(0, maxLen) + '…'
}

const formatHotItems = (items = [], maxCount = 12) => {
  return items.slice(0, maxCount).map((i) => ({
    title: i.title || '',
    short: shortenHotTitle(i.title || ''),
  }))
}

const setTrendingWindow = (start = 0) => {
  const list = hotItemsAll.value || []
  if (!list.length) {
    trendingTopics.value = []
    return
  }
  const len = list.length
  const s = ((start % len) + len) % len
  const out = []
  for (let i = 0; i < Math.min(HOT_WINDOW_SIZE, len); i += 1) {
    out.push(list[(s + i) % len])
  }
  trendingTopics.value = out
  hotWindowIndex.value = s
}

const rotateTrending = () => {
  if (!hotItemsAll.value || hotItemsAll.value.length === 0) {
    refreshTrending()
    return
  }
  setTrendingWindow(hotWindowIndex.value + HOT_WINDOW_SIZE)
}

const refreshTrending = async () => {
  trendingLoading.value = true
  try {
    const res = await api.getHotNews(8, 'hot', false)
    const items = (res && res.items) ? res.items : []
    if (items.length > 0) {
      hotItemsAll.value = formatHotItems(items, 12)
      setTrendingWindow(0)
      const t = res.collection_time ? new Date(res.collection_time) : new Date()
      trendingDate.value = `${t.getMonth() + 1}月${t.getDate()}日`
      return
    }
  } catch (e) {
    console.warn('[HomeView] 获取热榜失败，使用本地占位', e)
  } finally {
    trendingLoading.value = false
  }
  const today = new Date()
  trendingDate.value = `${today.getMonth() + 1}月${today.getDate()}日`
  const topics = ['OpenAI Sora 2.0 发布', '国内油价调整', '高考分数线公布', '星舰第五次发射', 'DeepSeek V3 开源', '新能源车降价潮']
  hotItemsAll.value = formatHotItems(topics.map((t) => ({ title: t })), 6)
  setTrendingWindow(0)
}

const switchPhoneImage = () => {
  const total = (analysisStore.imageUrls?.length || 0) + 1
  const nextIndex = (currentDisplayIndex.value + 1) % total
  
  if (nextIndex > 0) {
     // Preload if next is an image
     const nextUrl = analysisStore.imageUrls[nextIndex - 1]
     if (nextUrl && !preloadedImages.value.has(nextUrl)) {
       imageLoading.value = true
       preloadImages([nextUrl]).then(() => {
          imageLoading.value = false
       }).catch(err => console.warn('[HomeView] 预加载下一张图片失败:', err))
     }
  }
  currentDisplayIndex.value = nextIndex
}

// 手势：在图片区域左右拖拽/滑动切换图片（尽量模拟小红书的体验）
let swipePointerId = null
let swipeStartX = 0
let swipeStartY = 0
let swipeLastX = 0
let swipeLock = null // 'x' | 'y' | null

const onPhonePointerDown = (e) => {
  // Always enable swipe even if only title card (though swipe on 1 item does nothing, logic handles it)
  swipePointerId = e.pointerId
  swipeStartX = e.clientX
  swipeStartY = e.clientY
  swipeLastX = e.clientX
  swipeLock = null
  try {
    e.currentTarget.setPointerCapture(e.pointerId)
  } catch (_) {
    // ignore
  }
}

const onPhonePointerMove = (e) => {
  if (swipePointerId == null || e.pointerId !== swipePointerId) return
  swipeLastX = e.clientX
  const dx = e.clientX - swipeStartX
  const dy = e.clientY - swipeStartY

  // 首次判定方向，尽量不影响垂直滚动
  if (!swipeLock) {
    if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return
    swipeLock = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y'
  }

  if (swipeLock === 'x') {
    // 阻止水平滑动触发页面滚动
    e.preventDefault?.()
  }
}

const onPhonePointerUp = (e) => {
  if (swipePointerId == null || e.pointerId !== swipePointerId) return

  const dx = swipeLastX - swipeStartX
  const threshold = 50
  if (swipeLock === 'x' && Math.abs(dx) >= threshold) {
    const total = (analysisStore.imageUrls?.length || 0) + 1
    if (total > 1) {
      // dx < 0 向左滑：下一张；dx > 0 向右滑：上一张
      const next = dx < 0
        ? (currentDisplayIndex.value + 1) % total
        : (currentDisplayIndex.value - 1 + total) % total
      
      if (next > 0) {
         const nextUrl = analysisStore.imageUrls[next - 1]
         if (nextUrl && !preloadedImages.value.has(nextUrl)) {
           preloadImages([nextUrl]).catch(err => console.warn('[HomeView] 手势切换预加载失败:', err))
         }
      }
      
      currentDisplayIndex.value = next
    }
  }

  swipePointerId = null
  swipeLock = null
}

const handleStart = async () => {
  if (!topic.value.trim()) {
    alert('请输入议题！')
    return
  }

  // 暂时不检查 API Key，使用后端配置的 API Key
  // 如需使用前端配置的 API Key，可以在 SettingsView 中配置
  // const userApis = configStore.getUserApis
  // if (userApis.length === 0) {
  //   alert('请先配置 API Key')
  //   return
  // }

  if (isLoading.value) {
    // 停止分析
    isLoading.value = false
    debateLogs.value = []
    insight.value = ''
    xhsPreview.value = { title: '', content: '' }
    finalCopy.value = ''
    return
  }

  // 清空旧数据
  debateLogs.value = []
  xhsPreview.value = { title: '', content: '' }
  maxStepIndex.value = -1
  maxProgress.value = 0
  
  // 随机化 emoji 位置
  randomizeEmojiPosition()
  console.log('[HomeView] 🎲 随机化 emoji 位置:', emojiPosition.value)
  
  console.log('[HomeView] 🧹 已清空旧日志和预览数据，debateLogs长度:', debateLogs.value.length)
  console.log('[HomeView] 📊 当前store logs长度:', analysisStore.logs.length)

  try {
    console.log('[HomeView] 开始分析，议题:', topic.value, '辩论轮数:', debateRounds.value)

    await analysisStore.startAnalysis({
      topic: topic.value,
      debate_rounds: debateRounds.value
    })

    console.log('[HomeView] 分析已启动，等待SSE数据...')
  } catch (err) {
    console.error('[HomeView] 分析错误:', err)
    alert('分析失败: ' + err.message)
  }
}

// 监听分析日志变化 - 使用 storeToRefs 确保响应式
watch(storeLogs, (newLogs, oldLogs) => {
  const oldLength = (oldLogs && oldLogs.length) || 0
  const newLength = (newLogs && newLogs.length) || 0
  console.log(`[HomeView] ⚡ watch触发: ${oldLength} -> ${newLength} (新增 ${newLength - oldLength} 条)`)
  console.log('[HomeView] 当前debateLogs长度:', debateLogs.value.length)

  if (newLogs && newLogs.length > 0) {
    // 只处理新增的日志
    const startIndex = oldLength
    const newLogsToProcess = newLogs.slice(startIndex)

    if (newLogsToProcess.length > 0) {
      console.log('[HomeView] ✅ 处理新日志，数量:', newLogsToProcess.length)

      newLogsToProcess.forEach((log, index) => {
        const globalIndex = startIndex + index
        console.log(`[HomeView] 📝 处理日志 #${globalIndex}:`, {
          agent_name: log.agent_name,
          status: log.status,
          content_preview: (log.step_content || '').substring(0, 100),
          content_length: (log.step_content || '').length,
          has_model: !!log.model
        })

        // 添加辩论日志
        const roleMap = {
          'Moderator': 'moderator',
          'Crawler': 'system',
          'Reporter': 'system',
          'Analyst': 'analyst',
          'Debater': 'con',
          'Writer': 'writer',
          'Image Generator': 'pro',
          'System': 'system'
        }

        const role = roleMap[log.agent_name] || 'system'
        const logEntry = {
          role: role,
          name: log.agent_name,
          content: log.step_content || '',
          model: log.model || ''
        }

        console.log('[HomeView] ➕ 添加辩论日志:', logEntry.name, '到数组，当前长度:', debateLogs.value.length)
        debateLogs.value.push(logEntry)
        console.log('[HomeView] ✅ 添加后数组长度:', debateLogs.value.length, '最新条目:', debateLogs.value[debateLogs.value.length - 1])
        // 自动滚动到底部
        scrollToBottom()

        // 处理Writer输出，更新预览
        if (log.agent_name === 'Writer' && log.step_content) {
          console.log('[HomeView] ✍️ 处理Writer输出，更新预览，原始内容长度:', log.step_content.length)
          const content = log.step_content

          // 尝试解析 TITLE: 和 CONTENT: 格式
          if (content.includes('TITLE:') && content.includes('CONTENT:')) {
            const titleMatch = content.match(/TITLE:\s*(.+?)(?:\n|CONTENT:)/s)
            // 内容可能包含多段落（多次空行），这里必须拿到 CONTENT: 之后的全部内容
            const contentMatch = content.match(/CONTENT:\s*([\s\S]*)$/)

            if (titleMatch) {
              xhsPreview.value.title = titleMatch[1].trim()
              console.log('[HomeView] 📌 解析到标题:', xhsPreview.value.title)
            }
            if (contentMatch) {
              xhsPreview.value.content = contentMatch[1].trim()
              console.log('[HomeView] 📄 解析到内容，长度:', xhsPreview.value.content.length)
            } else if (content.includes('CONTENT:')) {
              // 如果只有 CONTENT: 标记，提取后面的内容
              const parts = content.split('CONTENT:')
              if (parts.length > 1) {
                xhsPreview.value.content = parts.slice(1).join('CONTENT:').trim()
                console.log('[HomeView] 🔧 使用split解析内容，长度:', xhsPreview.value.content.length)
              }
            }
          } else {
            // 如果没有格式标记，直接使用全部内容
            xhsPreview.value.content = content
            console.log('[HomeView] 📋 预览内容（无格式标记）长度:', content.length)
          }
        }

        
        // 检测额度耗尽错误 (50400 Access Denied)
        if (log.step_content && (log.step_content.includes('"code":50400') || log.step_content.includes('Access Denied'))) {
           // 使用 setTimeout 避免阻塞当前渲染循环
           setTimeout(() => {
             alert('⚠️ 警告：火山引擎（即梦）绘图服务额度已耗尽或密钥无效！\n\n请检查 user_settings.json 中的密钥配置，或登录火山引擎控制台查看资源包余量。');
           }, 500);
        }
      })
    } else {
      console.log('[HomeView] ⚠️ 没有新日志需要处理')
    }
  } else {
    console.log('[HomeView] ⚠️ newLogs为空或长度为0')
  }
}, { deep: true, immediate: true })

// 监听最终文案变化
watch(() => analysisStore.finalCopy, (newCopy) => {
  console.log('[HomeView] 📱 最终文案更新:', {
    has_title: !!newCopy.title,
    has_body: !!newCopy.body,
    title: newCopy.title,
    title_length: (newCopy.title || '').length,
    body_length: (newCopy.body || '').length,
    body_preview: (newCopy.body || '').substring(0, 100),
    current_xhsPreview_title: xhsPreview.value.title,
    current_xhsPreview_content_length: xhsPreview.value.content.length
  })

  // 🐛 修复：应该始终更新预览，而不是只在为空时更新
  if (newCopy && (newCopy.title || newCopy.body)) {
    if (newCopy.title) {
      xhsPreview.value.title = newCopy.title
      console.log('[HomeView] ✅ 更新预览标题:', newCopy.title)
    }
    if (newCopy.body) {
      xhsPreview.value.content = newCopy.body
      console.log('[HomeView] ✅ 更新预览内容，长度:', newCopy.body.length)
    }
  }
}, { deep: true, immediate: true })

// 监听编辑内容变化，实时同步到预览
watch(() => editableContent.value, (newContent) => {
  if (isEditing.value && newContent) {
    xhsPreview.value.title = newContent.title || ''
    xhsPreview.value.content = newContent.body || ''
    console.log('[HomeView] 编辑内容同步到预览:', {
      title: newContent.title,
      body_length: (newContent.body || '').length
    })
  }
}, { deep: true })

// 图片预加载函数
const preloadImages = async (urls) => {
  if (!urls || urls.length === 0) return
  
  console.log('[HomeView] 🖼️ 开始预加载图片，数量:', urls.length)
  const promises = urls.map((url) => {
    if (preloadedImages.value.has(url)) {
      return Promise.resolve() // 已预加载，跳过
    }
    
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        preloadedImages.value.add(url)
        resolve()
      }
      img.onerror = () => {
        console.warn('[HomeView] 图片预加载失败:', url)
        resolve() // 即使失败也继续，避免阻塞
      }
      img.src = url
    })
  })
  
  await Promise.all(promises)
  console.log('[HomeView] ✅ 图片预加载完成，已缓存:', preloadedImages.value.size, '张')
}

// 监听图片列表变化：新一批图片到达时从第一张开始展示并预加载
// 监听图片列表变化：新一批图片到达时，保持当前显示（如果是Title）或者切到第一张AI？
// 需求：AI生图完成之后，题图依旧作为第一张图片，然后AI生图的图片排列在后面
// 所以默认 currentDisplayIndex = 0 (Title Card) 是对的，无需改变
watch(() => analysisStore.imageUrls.length, async (newLen, oldLen) => {
  if (newLen > 0 && newLen !== oldLen) {
    // 图片更新了，预加载一下
    await preloadImages(analysisStore.imageUrls)
  }
})

// 监听图片URL数组变化（深度监听，确保URL变化时也触发预加载）
watch(() => analysisStore.imageUrls, async (newUrls) => {
  if (newUrls && newUrls.length > 0) {
    await preloadImages(newUrls)
  }
}, { deep: true })

const copyToClipboard = async () => {
  try {
    const text = finalCopy.value || ''
    if (!text) {
      alert('暂无内容可复制')
      return
    }
    await navigator.clipboard.writeText(text)
    alert('已复制到剪贴板')
  } catch (err) {
    console.error('Copy failed:', err)
    alert('复制失败，请手动复制')
  }
}

const exportAllImages = async () => {
  const originalIndex = currentDisplayIndex.value
  isExportingImages.value = true

  try {
    // 获取用户编辑后的图片选择和顺序
    const selectedIndices = editableContent.value.selectedImageIndices || []
    const imageOrder = editableContent.value.imageOrder || []
    
    // 构建所有图片数组（索引0=标题卡，索引1+=AI图片）
    const allImages = [null, ...analysisStore.imageUrls] // null 代表标题卡
    
    // 按用户定义的顺序导出选中的图片
    const imagesToExport = imageOrder
      .filter(idx => selectedIndices.includes(idx))
      .map(idx => ({ index: idx, source: allImages[idx] }))
    
    console.log('[Export] 导出图片:', {
      selectedIndices,
      imageOrder,
      imagesToExport: imagesToExport.map(img => ({ index: img.index, hasSource: !!img.source }))
    })
    
    if (imagesToExport.length === 0) {
      alert('没有选中的图片可导出')
      return
    }
    
    // 导出每张图片
    for (let i = 0; i < imagesToExport.length; i++) {
      const { index, source } = imagesToExport[i]
      
      try {
        if (index === 0) {
          // 导出标题卡（使用 Canvas API）
          const titleCardDataUrl = await generateTitleCardImage({
            title: editableContent.value.title || xhsPreview.value.title,
            emoji: analysisStore.titleEmoji,
            theme: analysisStore.titleTheme,
            emojiPos: emojiPosition.value
          })
          const response = await fetch(titleCardDataUrl)
          const titleBlob = await response.blob()
          const titleUrl = URL.createObjectURL(titleBlob)
          const a = document.createElement('a')
          a.href = titleUrl
          a.download = `xhs_image_${i + 1}_title_card.png`
          document.body.appendChild(a)
          a.click()
          a.remove()
          URL.revokeObjectURL(titleUrl)
          console.log(`[Export] 已导出标题卡 (${i + 1}/${imagesToExport.length})`)
        } else {
          // 导出 AI 图片
          const res = await fetch(source)
          if (!res.ok) throw new Error(`下载失败: ${res.status}`)
          const blob = await res.blob()
          const downloadUrl = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = downloadUrl
          a.download = `xhs_image_${i + 1}_ai.jpg`
          document.body.appendChild(a)
          a.click()
          a.remove()
          URL.revokeObjectURL(downloadUrl)
          console.log(`[Export] 已导出 AI 图片 (${i + 1}/${imagesToExport.length})`)
        }
      } catch (err) {
        console.error(`[Export] 导出图片 ${i + 1} 失败:`, err)
      }
    }
    
    alert(`成功导出 ${imagesToExport.length} 张图片`)
  } finally {
    currentDisplayIndex.value = originalIndex
    isExportingImages.value = false
  }
}

// --- 小红书发布相关 ---
const xhsStatus = ref({
  mcp_available: false,
  login_status: false,
  message: '',
  loading: false
})
const isPublishing = ref(false)

const checkXhsStatus = async () => {
  xhsStatus.value.loading = true
  try {
    const res = await api.getXhsStatus()
    xhsStatus.value = {
      mcp_available: res.mcp_available,
      login_status: res.login_status,
      message: res.message,
      loading: false
    }
  } catch (e) {
    console.warn('[HomeView] Failed to check XHS status', e)
    xhsStatus.value = {
      mcp_available: false,
      login_status: false,
      message: '无法连接到后端服务',
      loading: false
    }
  }
}

const debugPreviewTheme = () => {
    // 1. Set Title
    xhsPreview.value.title = topic.value || '地球引力消失7秒？NASA连夜辟谣🚀'
    
    // 2. Random Emoji
    const emojis = ['🤔', '🚀', '💡', '🔥', '✨', '🎉', '🤖', '👀', '🌈', '🎨']
    analysisStore.titleEmoji = emojis[Math.floor(Math.random() * emojis.length)]
    
    // 3. Random Theme
    const themes = ['warm', 'cool', 'alert', 'dark']
    analysisStore.titleTheme = themes[Math.floor(Math.random() * themes.length)]
    
    // 4. Random Position
    randomizeEmojiPosition()
    
    // 5. Switch to Title Card View
    currentDisplayIndex.value = 0
}

const publishToXhs = async () => {
  // 使用编辑后的内容
  const titleToPublish = editableContent.value.title || analysisStore.finalCopy.title
  const bodyToPublish = editableContent.value.body || analysisStore.finalCopy.body
  
  if (!titleToPublish || !bodyToPublish) return
  
  // 获取选中的图片（按用户排序）
  const allImages = [null, ...analysisStore.imageUrls] // null 代表标题卡
  const selectedImages = editableContent.value.imageOrder
    .filter(idx => editableContent.value.selectedImageIndices.includes(idx))
    .map(idx => allImages[idx])
    .filter(img => img !== null) // 过滤掉标题卡（暂时）
  
  if (selectedImages.length === 0) {
    alert('发布失败：至少需要一张配图')
    return
  }

  if (!confirm('确定要根据当前标题、正文和配图发布到小红书吗？')) return

  isPublishing.value = true
  const originalIndex = currentDisplayIndex.value
  
  try {
    // Step 1: Generate Title Card using Canvas API (if selected)
    let titleCardDataUrl = null
    const titleCardSelected = editableContent.value.selectedImageIndices.includes(0)
    
    if (titleCardSelected) {
      try {
        titleCardDataUrl = await generateTitleCardImage({
          title: titleToPublish,
          emoji: analysisStore.titleEmoji,
          theme: analysisStore.titleTheme,
          emojiPos: emojiPosition.value
        })
        console.log('[Publish] Title Card generated successfully via Canvas API')
      } catch (e) {
        console.error('[Publish] Title Card generation failed:', e)
      }
    }
    
    // Step 2: Build final images list
    let allImagesToPublish = [...selectedImages]
    if (titleCardDataUrl) {
      // Prepend title card if it was selected
      allImagesToPublish = [titleCardDataUrl, ...selectedImages]
      console.log('[Publish] Title Card prepended to images list')
    }
    
    // Extract hashtags from body and pass them separately
    const body = bodyToPublish || ''
    const hashtagRegex = /#([^\s#]+)/g
    const matches = [...body.matchAll(hashtagRegex)]
    const tags = matches.map(m => m[1])
    
    // Remove hashtags from content
    let contentWithoutTags = body
    const lines = body.split('\n')
    const lastLine = lines[lines.length - 1]?.trim() || ''
    if (lastLine.match(/^(#[^\s#]+\s*)+$/)) {
      contentWithoutTags = lines.slice(0, -1).join('\n').trim()
    }
    
    console.log('[Publish] Extracted tags:', tags)
    console.log('[Publish] Content (hashtags removed):', contentWithoutTags.substring(0, 100) + '...')
    console.log('[Publish] Images count:', allImagesToPublish.length)
    
    const res = await api.publishToXhs({
      title: titleToPublish,
      content: contentWithoutTags,
      images: allImagesToPublish,
      tags: tags.length > 0 ? tags : undefined
    })

    if (res.success) {
      alert(`发布成功！\n${res.message}`)
    } else {
      alert(`发布失败：${res.message}`)
    }
  } catch (e) {
    console.error('[HomeView] Publish to XHS failed', e)
    alert(`发布请求出错: ${e.message || e}`)
  } finally {
    currentDisplayIndex.value = originalIndex
    isPublishing.value = false
  }
}

onMounted(() => {
  refreshTrending()
  hydrateHotTopicDraft()
  checkXhsStatus()
})
</script>

<style scoped>
.debate-bubble {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 平台爬取闪烁动画 - 2秒循环，缓慢闪烁 */
.platform-crawling {
  animation: platformBlink 2s ease-in-out infinite;
}

@keyframes platformBlink {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.4;
  }
}

/* 图片切换过渡效果 */
.image-fade-enter-active,
.image-fade-leave-active {
  transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out;
}

.image-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.image-fade-leave-to {
  opacity: 0;
  transform: scale(1.05);
}

.image-fade-enter-to,
.image-fade-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>