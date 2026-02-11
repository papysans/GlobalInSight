<template>
  <div class="view-section animate-fade-in">
    <!-- Header: 顶部输入区 (复制 HomeView header 结构) -->
    <header class="relative bg-white border-b border-slate-100 pt-12 pb-8 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mb-4">
          股票行情推演与<span class="gradient-text">内容创作</span>引擎
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
                placeholder="输入股票名称、事件描述或推演主题..." @keyup.enter="handleStart" />

              <div class="h-8 border-l border-slate-200 mx-2"></div>

              <!-- 大盘情绪迷你仪表盘 -->
              <div class="flex items-center" title="大盘情绪指数">
                <SentimentGauge
                  v-if="sentimentStore.marketIndex"
                  :index-value="sentimentStore.marketIndex.index_value ?? 50"
                  :label="sentimentStore.marketIndex.label || ''"
                  size="mini"
                />
                <div v-else class="flex items-center gap-1 px-2 text-xs text-slate-400 whitespace-nowrap">
                  <BarChart3 class="w-3.5 h-3.5" />
                  <span class="font-bold text-slate-600">--</span>
                </div>
              </div>

              <div class="h-8 border-l border-slate-200 mx-2"></div>

              <div class="flex items-center gap-2 pr-2" title="辩论轮数">
                <span class="text-xs text-slate-400 font-bold whitespace-nowrap">轮数:</span>
                <input v-model.number="debateRounds" type="number" min="1" max="5"
                  class="w-12 py-1 px-2 text-center text-sm border border-slate-200 rounded-lg outline-none focus:border-blue-500" />
              </div>

              <button @click="handleStart" :class="[
                'px-6 py-2 text-white font-medium rounded-lg transition-colors flex items-center gap-2 shadow-md whitespace-nowrap min-w-[120px] justify-center',
                isAnalyzing ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
              ]">
                <component :is="isAnalyzing ? Square : Sparkles" class="w-4 h-4" />
                {{ isAnalyzing ? '停止推演' : '启动推演' }}
              </button>
            </div>
          </div>

          <!-- 热搜标签行 -->
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
    <div v-if="isAnalyzing && workflowRunning"
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
      <div v-show="isAnalyzing && workflowRunning" class="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
        <h3 class="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
          <Activity class="w-4 h-4 text-blue-600" /> 工作流进度
        </h3>
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
              <span class="line-clamp-1">{{ step.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 主内容区：左右分栏 -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <!-- Left: Debate & Insight -->
        <div class="lg:col-span-7 flex flex-col gap-6">
          <!-- Agent 协作面板 -->
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between px-1 h-8">
              <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Cpu class="w-5 h-5 text-blue-600" /> 智能体协作 (Multi-Agent Debate)
              </h2>
              <div v-if="isAnalyzing" class="flex items-center gap-2">
                <div
                  class="px-3 py-1 bg-green-50 text-green-700 rounded-full border border-green-100 text-xs font-medium flex items-center gap-2">
                  <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
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
                <span>AI 多空辩论实时推演</span>
                <span class="text-slate-400 font-normal text-[10px]">{{ activeModelDisplay }}</span>
              </div>
              <div
                ref="debateContainerRef"
                class="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-4 text-sm bg-white/50 relative scroll-smooth">
                <div v-if="debateLogs.length === 0"
                  class="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
                  <Bot class="w-16 h-16 mb-4 stroke-1" />
                  <p>等待指令启动推演...</p>
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

          <!-- 核心洞察 (Grand Insight) -->
          <div class="flex flex-col gap-2">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2 px-1">
              <Lightbulb class="w-5 h-5 text-yellow-500" /> 核心洞察 (Grand Insight)
            </h2>
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-yellow-400 min-h-[140px] flex flex-col">
              <div class="text-sm text-slate-600 leading-relaxed flex-1 flex flex-col">
                <div v-if="!insight"
                  class="h-full flex items-center justify-center text-slate-400 border border-dashed border-slate-200 rounded-lg p-3 bg-slate-50/50 italic text-xs">
                  等待推演结论产出...
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

          <!-- 情绪上下文数据 (Sentiment Context) -->
          <div v-if="sentimentContext" class="flex flex-col gap-2">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2 px-1">
              <BarChart3 class="w-5 h-5 text-blue-500" /> 情绪数据 (Sentiment Context)
            </h2>
            <div class="glass-card rounded-xl p-5 shadow-md border-l-4 border-l-blue-400">
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <!-- 综合指数 -->
                <div class="bg-blue-50 rounded-lg p-3 text-center">
                  <div class="text-[10px] font-bold text-blue-500 uppercase tracking-wider mb-1">综合指数</div>
                  <div class="text-2xl font-black" :style="{ color: sentimentLabelColor }">
                    {{ Math.round(sentimentContext.index_value ?? 0) }}
                  </div>
                  <div class="text-xs font-semibold mt-0.5" :style="{ color: sentimentLabelColor }">
                    {{ sentimentContext.label || '—' }}
                  </div>
                </div>
                <!-- 趋势方向 -->
                <div class="bg-slate-50 rounded-lg p-3 text-center">
                  <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">趋势方向</div>
                  <div class="text-lg font-bold text-slate-700">
                    {{ sentimentContext.trend_direction === 'up' ? '↑ 上升' : sentimentContext.trend_direction === 'down' ? '↓ 下降' : '→ 持平' }}
                  </div>
                  <div class="text-[10px] text-slate-400 mt-0.5">
                    样本量: {{ sentimentContext.sample_count ?? '—' }}
                  </div>
                </div>
                <!-- 分项得分 -->
                <div v-if="sentimentContext.sub_scores" class="bg-slate-50 rounded-lg p-3 col-span-2 sm:col-span-1">
                  <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">分项得分</div>
                  <div class="space-y-1.5">
                    <div v-for="(score, key) in sentimentContext.sub_scores" :key="key" class="flex items-center justify-between text-xs">
                      <span class="text-slate-500">{{ subScoreLabel(key) }}</span>
                      <span class="font-bold text-slate-700">{{ score != null ? Math.round(score) : '—' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


        <!-- Right: 多平台预览区 -->
        <div class="lg:col-span-5 flex flex-col gap-2">
          <div class="flex items-center justify-between px-1">
            <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Smartphone class="w-5 h-5 text-purple-600" /> 实时生成预览 (Preview)
            </h2>
          </div>

          <!-- 平台选择器 Tab -->
          <div class="flex items-center gap-2 px-1">
            <button v-for="p in platforms" :key="p.id"
              @click="analysisStore.switchPlatform(p.id)"
              :class="[
                'px-3 py-1 rounded-full border text-xs font-semibold transition-all',
                selectedPlatform === p.id
                  ? 'bg-blue-50 border-blue-300 text-blue-600'
                  : 'border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600'
              ]">
              {{ p.label }}
            </button>
          </div>

          <!-- 小红书手机模拟器预览 -->
          <div v-if="selectedPlatform === 'xhs'" class="glass-card p-6 rounded-xl shadow-lg flex justify-center bg-slate-100/50">
            <div
              class="phone-preview rounded-[3rem] overflow-hidden shadow-2xl bg-white w-full max-w-[320px] h-[680px] flex flex-col transform transition hover:scale-[1.02] duration-300"
              style="border: 8px solid #000000; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
              <!-- Status Bar -->
              <div class="relative bg-white px-5 h-10 flex items-center justify-between z-10 flex-shrink-0 select-none">
                <span class="text-[10px] font-bold text-slate-900 w-8">09:41</span>
                <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-6 bg-black rounded-full flex justify-center items-center">
                  <div class="w-1.5 h-1.5 bg-gray-800 rounded-full absolute right-4"></div>
                </div>
                <div class="w-8 flex justify-end">
                  <Wifi class="w-3 h-3 text-slate-900" />
                </div>
              </div>

              <!-- App Header (XHS-like) -->
              <div class="h-12 px-4 bg-white flex items-center justify-between border-b border-slate-100 flex-shrink-0 select-none">
                <div class="flex items-center gap-2 min-w-0">
                  <ChevronLeft class="w-5 h-5 text-slate-900" />
                  <div class="w-7 h-7 rounded-full bg-slate-200 overflow-hidden flex items-center justify-center flex-shrink-0">
                    <Bot class="w-4 h-4 text-slate-500" />
                  </div>
                  <div class="min-w-0">
                    <div class="text-xs font-bold text-slate-900 truncate">{{ xhsPreview.title ? 'StockBot' : '预览' }}</div>
                    <div class="text-[10px] text-slate-400 truncate">已关注</div>
                  </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button class="px-3 py-1 rounded-full text-[10px] font-bold border border-slate-200 text-slate-700 bg-white">已关注</button>
                  <Share2 class="w-4 h-4 text-slate-700" />
                </div>
              </div>

              <!-- Screen Content -->
              <div class="relative cursor-pointer group flex-1 flex flex-col overflow-hidden bg-white"
                @click="switchPhoneImage" title="点击切换配图">
                <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
                  <!-- 图片区域 -->
                  <div class="relative overflow-hidden flex-shrink-0 transition-colors duration-500 aspect-[3/4] bg-slate-100">
                    <div class="relative w-full h-full" style="touch-action: pan-y;"
                      @pointerdown="onPhonePointerDown" @pointermove="onPhonePointerMove"
                      @pointerup="onPhonePointerUp" @pointercancel="onPhonePointerUp">
                      <transition name="image-fade" mode="out-in">
                        <!-- Title Card -->
                        <XiaohongshuCard
                          v-if="displayImages[currentDisplayIndex] === null"
                          key="title-card"
                          ref="xiaohongshuCardRef"
                          :title="xhsPreview.title"
                          :emoji="analysisStore.titleEmoji"
                          :theme="analysisStore.titleTheme"
                          :emoji-pos="emojiPosition"
                          @emoji-click="randomizeEmojiPosition"
                          class="absolute inset-0"
                        />
                        <!-- AI Images -->
                        <img v-else :key="'img-' + currentDisplayIndex"
                          :src="displayImages[currentDisplayIndex]"
                          class="absolute inset-0 w-full h-full object-cover block"
                          alt="AI Generated" draggable="false" loading="lazy" decoding="async" />
                      </transition>

                      <!-- AI 生成提示 -->
                      <div v-if="displayImages[currentDisplayIndex] !== null"
                        class="absolute top-2 left-2 flex items-center gap-1 bg-white/80 text-slate-700 text-[10px] px-2 py-1 rounded-full backdrop-blur-sm border border-slate-100">
                        <AlertTriangle class="w-3 h-3 text-slate-700" />
                        <span>内容可能使用AI技术生成</span>
                      </div>

                      <!-- 多图指示器 -->
                      <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5 z-20">
                        <div v-for="(_, i) in displayImages" :key="i" :class="[
                          'w-1.5 h-1.5 rounded-full transition-all duration-300',
                          currentDisplayIndex === i ? 'bg-white scale-125' : 'bg-white/50'
                        ]"></div>
                      </div>
                      <div class="absolute bottom-2 right-2 bg-black/50 text-white text-[10px] px-2 py-1 rounded-full backdrop-blur-sm">
                        {{ currentDisplayIndex + 1 }} / {{ displayImages.length }}
                      </div>
                    </div>
                  </div>

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
                </div>

                <!-- 底部固定互动栏 -->
                <div class="px-4 py-3 border-t border-slate-100 flex items-center justify-between text-slate-500 text-[10px] bg-white z-10 flex-shrink-0">
                  <div class="flex-1 mr-3">
                    <div class="w-full rounded-full bg-slate-100 text-slate-400 px-3 py-2 text-[10px] border border-slate-100">说点什么...</div>
                  </div>
                  <div class="flex items-center gap-3 text-slate-500">
                    <span class="whitespace-nowrap"><Heart class="w-3 h-3 inline" /> 57</span>
                    <span class="whitespace-nowrap"><Star class="w-3 h-3 inline" /> 15</span>
                    <span class="whitespace-nowrap"><MessageCircle class="w-3 h-3 inline" /> 44</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 微博/雪球/知乎 占位预览 (PlatformPreview 组件将在 Task 14A 中实现) -->
          <div v-else class="glass-card p-6 rounded-xl shadow-lg bg-slate-50/50 min-h-[400px] flex flex-col items-center justify-center text-slate-400">
            <Smartphone class="w-12 h-12 mb-3 stroke-1" />
            <p class="text-sm font-medium">{{ currentPlatformLabel }} 预览</p>
            <p class="text-xs mt-1">平台预览组件将在后续任务中实现</p>
          </div>
        </div>
      </div>


      <!-- 文案生成区 (Copywriting Section) -->
      <div class="flex flex-col gap-2">
        <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2 px-1">
          <PenTool class="w-5 h-5 text-emerald-600" /> 文案生成 (Copywriting)
        </h2>
        <div class="glass-card rounded-xl p-6 shadow-lg border-t-4 border-t-emerald-500">
          <div v-if="isAnalyzing" class="flex items-center gap-2 mb-4 text-sm font-bold text-emerald-600 animate-pulse">
            <Loader2 class="w-4 h-4 animate-spin" /> 正在后台处理信息，生成最终文案...
          </div>

          <div class="relative">
            <textarea :value="finalCopyText" readonly
              class="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 font-mono resize-none focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="等待推演结束后，在此生成可直接发布的文案..."></textarea>
            <div class="absolute top-3 right-3 flex items-center gap-2">
              <button @click="analysisStore.startEditing()"
                :disabled="!finalCopyText"
                class="px-3 py-1.5 bg-blue-600 border border-blue-600 hover:bg-blue-700 text-white rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
                <Edit class="w-3 h-3" /> 编辑
              </button>
              <button @click="copyToClipboard" :disabled="!finalCopyText"
                class="px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
                <Copy class="w-3 h-3" /> 复制全文
              </button>
            </div>
          </div>

          <!-- 编辑面板 (CopywritingEditor) -->
          <CopywritingEditor />

          <!-- 底部栏：导出图片 + 状态指示 + 发布/复制按钮 -->
          <div class="mt-2 flex items-center justify-between px-1">
            <!-- 左侧：导出图片按钮 -->
            <button @click="exportAllImages"
              :disabled="isExportingImages || !(analysisStore.imageUrls && analysisStore.imageUrls.length)"
              class="px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
              <Download class="w-3 h-3" />
              {{ isExportingImages ? '导出中...' : '导出全部图片' }}
            </button>

            <!-- 右侧：平台操作按钮 -->
            <div class="flex items-center gap-3">
              <!-- 小红书模式：MCP 状态 + 发布按钮 -->
              <template v-if="selectedPlatform === 'xhs'">
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
                <button @click="publishToXhs"
                  :disabled="!finalCopyText || isPublishing || !xhsStatus.mcp_available || !xhsStatus.login_status"
                  :class="[
                    'px-3 py-1.5 rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed',
                    (!xhsStatus.mcp_available || !xhsStatus.login_status) ? 'bg-slate-100 text-slate-400 border border-slate-200' : 'bg-red-500 hover:bg-red-600 text-white border border-red-500'
                  ]">
                  <Upload v-if="!isPublishing" class="w-3 h-3" />
                  <Loader2 v-else class="w-3 h-3 animate-spin" />
                  {{ isPublishing ? '发布中...' : '发布到小红书' }}
                </button>
              </template>

              <!-- 微博/雪球/知乎模式：一键复制到剪贴板 -->
              <template v-else>
                <button @click="copyToClipboard" :disabled="!finalCopyText"
                  class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
                  <Copy class="w-3 h-3" /> 一键复制到剪贴板
                </button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史推演记录 -->
      <div class="flex flex-col gap-2">
        <div class="flex items-center justify-between px-1">
          <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <FileText class="w-5 h-5 text-slate-500" /> 历史推演记录
          </h2>
          <button @click="loadHistory" class="text-xs text-blue-600 hover:text-blue-700 font-medium">
            刷新
          </button>
        </div>
        <div v-if="analysisStore.history.length === 0"
          class="glass-card rounded-xl p-6 text-center text-slate-400 text-sm">
          暂无历史推演记录
        </div>
        <div v-else class="space-y-2">
          <div v-for="item in analysisStore.history" :key="item.id"
            class="glass-card rounded-xl p-4 cursor-pointer hover:shadow-md transition-all border-l-4 border-l-slate-200 hover:border-l-blue-400"
            @click="viewHistoryDetail(item)">
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-bold text-slate-800 truncate">{{ item.topic || '未命名推演' }}</h4>
                <p class="text-xs text-slate-400 mt-1">{{ formatTime(item.created_at) }}</p>
              </div>
              <ChevronRight class="w-4 h-4 text-slate-400 flex-shrink-0" />
            </div>
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
  Smartphone, Wifi, Heart, Star, MessageCircle, PenTool,
  ChevronLeft, ChevronRight, Share2, AlertTriangle, Download, Upload, Check, XCircle,
  Loader2, Copy, Shield, ThumbsUp, ThumbsDown, Glasses, Activity,
  Database, FileText, Brain, MessageSquare, PenLine, BarChart3, Edit
} from 'lucide-vue-next'
import { useStockAnalysisStore } from '../stores/stockAnalysis'
import { useStockNewsStore } from '../stores/stockNews'
import { useConfigStore } from '../stores/config'
import { useSentimentStore } from '../stores/sentiment'
import { api } from '../api'
import MarkdownIt from 'markdown-it'
import XiaohongshuCard from '../components/XiaohongshuCard.vue'
import CopywritingEditor from '../components/CopywritingEditor.vue'
import SentimentGauge from '../components/SentimentGauge.vue'

const md = new MarkdownIt()
const analysisStore = useStockAnalysisStore()
const stockNewsStore = useStockNewsStore()
const configStore = useConfigStore()
const sentimentStore = useSentimentStore()

const isDark = computed(() => configStore.isDarkMode)

const { analysisSteps, isEditing, editableContent } = storeToRefs(analysisStore)

const topic = ref('')
const xiaohongshuCardRef = ref(null)
const debateContainerRef = ref(null)

// 平台列表
const platforms = [
  { id: 'xhs', label: '小红书' },
  { id: 'weibo', label: '微博' },
  { id: 'xueqiu', label: '雪球' },
  { id: 'zhihu', label: '知乎' },
]

const selectedPlatform = computed(() => analysisStore.selectedPlatform)
const currentPlatformLabel = computed(() => {
  const p = platforms.find(p => p.id === selectedPlatform.value)
  return p ? p.label : ''
})

// 推演状态
const isAnalyzing = computed(() => analysisStore.isAnalyzing)
const insight = ref('')
const debateLogs = ref([])
const xhsPreview = ref({ title: '', content: '' })
const isExportingImages = ref(false)
const isPublishing = ref(false)
const activeModelDisplay = ref('')

// Sentiment context from analysis result
const sentimentContext = computed(() => {
  const result = analysisStore.currentAnalysis
  if (result?.sentiment_context) return result.sentiment_context
  // Fallback to market index from sentiment store
  if (sentimentStore.marketIndex) {
    return {
      index_value: sentimentStore.marketIndex.index_value,
      label: sentimentStore.marketIndex.label,
      trend_direction: sentimentStore.marketIndex.trend_direction || 'flat',
      sample_count: sentimentStore.marketIndex.sample_count,
      sub_scores: sentimentStore.marketIndex.sub_scores || null,
    }
  }
  return null
})

const sentimentLabelColor = computed(() => {
  const v = sentimentContext.value?.index_value ?? 50
  if (v <= 20) return '#dc2626'
  if (v <= 40) return '#ea580c'
  if (v <= 60) return '#ca8a04'
  if (v <= 80) return '#65a30d'
  return '#16a34a'
})

const subScoreLabel = (key) => {
  const map = {
    comment_sentiment_score: '评论情绪',
    baidu_vote_score: '百度投票',
    akshare_aggregate_score: 'AKShare',
    news_sentiment_score: '新闻情绪',
    margin_trading_score: '融资融券',
  }
  return map[key] || key
}

const finalCopyText = computed(() => {
  const fc = analysisStore.finalCopy
  if (fc.title && fc.body) return `${fc.title}\n\n${fc.body}`
  return ''
})

// 工作流进度追踪
const workflowRunning = ref(false)
const currentStep = ref('')
const maxStepIndex = ref(-1)
const maxProgress = ref(0)
const startedAt = ref(null)

const displayProgress = computed(() => Math.max(maxProgress.value, 0))

// 图片相关
const currentDisplayIndex = ref(0)
const emojiPosition = ref('bottom-right')

const displayImages = computed(() => {
  const allImages = [null, ...analysisStore.imageUrls]
  if (analysisStore.isEditing && editableContent.value.selectedImageIndices.length > 0
    && editableContent.value.selectedImageIndices.length < allImages.length) {
    return editableContent.value.imageOrder
      .filter(idx => editableContent.value.selectedImageIndices.includes(idx))
      .map(idx => allImages[idx])
  }
  return allImages
})

// 热搜标签
const trendingDate = ref('')
const trendingTopics = ref([])
const hotItemsAll = ref([])
const hotWindowIndex = ref(0)
const HOT_WINDOW_SIZE = 3

// 辩论轮数
const loadDebateRounds = () => {
  const saved = localStorage.getItem('grandchart_debate_rounds')
  if (saved) {
    try {
      const rounds = parseInt(saved, 10)
      if (rounds >= 1 && rounds <= 5) return rounds
    } catch (e) { /* ignore */ }
  }
  return 2
}
const debateRounds = ref(loadDebateRounds())

watch(debateRounds, (v) => {
  if (v >= 1 && v <= 5) localStorage.setItem('grandchart_debate_rounds', String(v))
})

// 工作流步骤配置（行情推演版）
const workflowSteps = [
  { key: 'sentiment', name: '情绪数据', description: '获取散户情绪', icon: BarChart3, progress: 5 },
  { key: 'news_summary', name: '资讯汇总', description: '提取核心事实', icon: FileText, progress: 15 },
  { key: 'impact_analysis', name: '影响分析', description: '分析行情影响', icon: Brain, progress: 30 },
  { key: 'bull_debate', name: '多头激辩', description: '看多论证', icon: ThumbsUp, progress: 45 },
  { key: 'bear_debate', name: '空头激辩', description: '看空论证', icon: ThumbsDown, progress: 60 },
  { key: 'writer', name: '文案生成', description: '生成社交内容', icon: PenLine, progress: 85 },
]

// 步骤状态类
const getStepClass = (stepKey) => {
  if (maxProgress.value >= 100) return 'border-green-200 bg-green-50'
  if (!currentStep.value) return 'border-slate-200 bg-slate-50'
  const stepIndex = workflowSteps.findIndex(s => s.key === stepKey)
  const currentIndex = workflowSteps.findIndex(s => s.key === currentStep.value)
  if (stepIndex === currentIndex) return 'border-blue-500 bg-blue-50 shadow-md'
  if (stepIndex < currentIndex || stepIndex <= maxStepIndex.value) return 'border-green-200 bg-green-50'
  return 'border-slate-200 bg-slate-50'
}

const getStepIconClass = (stepKey) => {
  if (maxProgress.value >= 100) return 'text-green-600'
  if (!currentStep.value) return 'text-slate-400'
  const stepIndex = workflowSteps.findIndex(s => s.key === stepKey)
  const currentIndex = workflowSteps.findIndex(s => s.key === currentStep.value)
  if (stepIndex === currentIndex) return 'text-blue-600 animate-pulse'
  if (stepIndex < currentIndex || stepIndex <= maxStepIndex.value) return 'text-green-600'
  return 'text-slate-400'
}

const getStepTextClass = (stepKey) => {
  if (maxProgress.value >= 100) return 'text-green-700'
  if (!currentStep.value) return 'text-slate-500'
  const stepIndex = workflowSteps.findIndex(s => s.key === stepKey)
  const currentIndex = workflowSteps.findIndex(s => s.key === currentStep.value)
  if (stepIndex === currentIndex) return 'text-blue-700'
  if (stepIndex < currentIndex || stepIndex <= maxStepIndex.value) return 'text-green-700'
  return 'text-slate-500'
}

const currentStepText = computed(() => {
  const step = workflowSteps.find(s => s.key === currentStep.value)
  return step ? `正在${step.name}...` : '准备中...'
})

const elapsedTime = computed(() => {
  if (!startedAt.value) return ''
  const diff = Math.floor((Date.now() - startedAt.value) / 1000)
  if (diff < 60) return `已用时 ${diff}秒`
  return `已用时 ${Math.floor(diff / 60)}分${diff % 60}秒`
})

// Markdown 渲染
const renderMarkdown = (text) => text ? md.render(text) : ''

// 辩论气泡样式
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
  const map = { moderator: Shield, pro: ThumbsUp, con: ThumbsDown, analyst: Glasses, system: Bot }
  return map[role] || Bot
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (debateContainerRef.value) {
      debateContainerRef.value.scrollTop = debateContainerRef.value.scrollHeight
    }
  })
}

// 热搜相关
const shortenHotTitle = (title, maxLen = 18) => {
  if (!title) return ''
  const clean = String(title).trim()
  return clean.length <= maxLen ? clean : clean.slice(0, maxLen) + '…'
}

const formatHotItems = (items = [], maxCount = 12) => {
  return items.slice(0, maxCount).map(i => ({
    title: i.title || '',
    short: shortenHotTitle(i.title || ''),
  }))
}

const setTrendingWindow = (start = 0) => {
  const list = hotItemsAll.value || []
  if (!list.length) { trendingTopics.value = []; return }
  const len = list.length
  const s = ((start % len) + len) % len
  const out = []
  for (let i = 0; i < Math.min(HOT_WINDOW_SIZE, len); i++) {
    out.push(list[(s + i) % len])
  }
  trendingTopics.value = out
  hotWindowIndex.value = s
}

const rotateTrending = () => {
  if (!hotItemsAll.value.length) { refreshTrending(); return }
  setTrendingWindow(hotWindowIndex.value + HOT_WINDOW_SIZE)
}

const refreshTrending = async () => {
  try {
    // 使用股票热榜 API
    if (stockNewsStore.clusters.length === 0) {
      await stockNewsStore.fetchNews()
    }
    const items = stockNewsStore.trendingTopics || []
    if (items.length > 0) {
      hotItemsAll.value = formatHotItems(items, 12)
      setTrendingWindow(0)
      const today = new Date()
      trendingDate.value = `${today.getMonth() + 1}月${today.getDate()}日`
      return
    }
  } catch (e) {
    console.warn('[StockAnalysisView] 获取热榜失败', e)
  }
  const today = new Date()
  trendingDate.value = `${today.getMonth() + 1}月${today.getDate()}日`
  hotItemsAll.value = formatHotItems([
    { title: '贵州茅台业绩预告' }, { title: '新能源车降价潮' }, { title: '半导体板块异动' },
    { title: 'AI 算力需求暴增' }, { title: '银行股集体拉升' }, { title: '港股科技股反弹' }
  ], 6)
  setTrendingWindow(0)
}

// 图片切换
const switchPhoneImage = () => {
  const total = displayImages.value.length
  currentDisplayIndex.value = (currentDisplayIndex.value + 1) % total
}

// 手势滑动
let swipePointerId = null
let swipeStartX = 0
let swipeStartY = 0
let swipeLastX = 0
let swipeLock = null

const onPhonePointerDown = (e) => {
  swipePointerId = e.pointerId; swipeStartX = e.clientX; swipeStartY = e.clientY; swipeLastX = e.clientX; swipeLock = null
  try { e.currentTarget.setPointerCapture(e.pointerId) } catch (_) { /* ignore */ }
}
const onPhonePointerMove = (e) => {
  if (swipePointerId == null || e.pointerId !== swipePointerId) return
  swipeLastX = e.clientX
  const dx = e.clientX - swipeStartX, dy = e.clientY - swipeStartY
  if (!swipeLock) { if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return; swipeLock = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y' }
  if (swipeLock === 'x') e.preventDefault?.()
}
const onPhonePointerUp = (e) => {
  if (swipePointerId == null || e.pointerId !== swipePointerId) return
  const dx = swipeLastX - swipeStartX
  if (swipeLock === 'x' && Math.abs(dx) >= 50) {
    const total = displayImages.value.length
    if (total > 1) {
      currentDisplayIndex.value = dx < 0
        ? (currentDisplayIndex.value + 1) % total
        : (currentDisplayIndex.value - 1 + total) % total
    }
  }
  swipePointerId = null; swipeLock = null
}

const randomizeEmojiPosition = () => {
  const positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
  let next = emojiPosition.value
  while (next === emojiPosition.value) next = positions[Math.floor(Math.random() * positions.length)]
  emojiPosition.value = next
}

// 从热榜一键推演的缓存填充搜索框
const hydrateHotTopicDraft = () => {
  try {
    const cached = sessionStorage.getItem('stock_topic_draft')
    if (cached) {
      const parsed = JSON.parse(cached)
      if (parsed && parsed.title) topic.value = parsed.title
      // 消费后清除，避免重复填入
      sessionStorage.removeItem('stock_topic_draft')
    }
  } catch (e) {
    console.warn('failed to hydrate stock_topic_draft', e)
  }
}

// 启动/停止推演
const handleStart = async () => {
  if (!topic.value.trim()) { alert('请输入推演主题！'); return }

  if (isAnalyzing.value) {
    analysisStore.stopAnalysis()
    workflowRunning.value = false
    return
  }

  // 清空旧数据
  debateLogs.value = []
  xhsPreview.value = { title: '', content: '' }
  insight.value = ''
  maxStepIndex.value = -1
  maxProgress.value = 0
  currentStep.value = ''
  workflowRunning.value = true
  startedAt.value = Date.now()
  currentDisplayIndex.value = 0
  randomizeEmojiPosition()

  try {
    await analysisStore.startAnalysis({
      topic: topic.value,
      debate_rounds: debateRounds.value,
    })
  } catch (err) {
    console.error('[StockAnalysisView] 推演错误:', err)
    alert('推演失败: ' + err.message)
  } finally {
    workflowRunning.value = false
  }
}

// 监听推演步骤变化
watch(analysisSteps, (newSteps, oldSteps) => {
  const oldLen = oldSteps?.length || 0
  const newLen = newSteps?.length || 0
  if (newLen <= oldLen) return

  const newLogsToProcess = newSteps.slice(oldLen)
  newLogsToProcess.forEach((log) => {
    // 映射 agent 角色
    const roleMap = {
      'SentimentAgent': 'system', 'NewsSummary': 'system', 'ImpactAnalysis': 'analyst',
      'BullDebater': 'pro', 'BearDebater': 'con', 'Crossfire': 'moderator',
      'ControversialConclusion': 'analyst', 'Writer': 'system', 'ImageGenerator': 'pro',
      'Moderator': 'moderator', 'Crawler': 'system', 'Reporter': 'system',
      'Analyst': 'analyst', 'Debater': 'con', 'System': 'system',
    }
    const role = roleMap[log.agent_name] || 'system'
    debateLogs.value.push({ role, name: log.agent_name, content: log.step_content || '', model: log.model || '' })
    scrollToBottom()

    // 更新活跃模型显示
    if (log.model) activeModelDisplay.value = log.model

    // 更新工作流进度
    const stepMap = {
      'SentimentAgent': 'sentiment', 'NewsSummary': 'news_summary', 'ImpactAnalysis': 'impact_analysis',
      'BullDebater': 'bull_debate', 'BearDebater': 'bear_debate', 'Writer': 'writer',
    }
    const mappedStep = stepMap[log.agent_name]
    if (mappedStep) {
      currentStep.value = mappedStep
      const stepDef = workflowSteps.find(s => s.key === mappedStep)
      if (stepDef && stepDef.progress > maxProgress.value) maxProgress.value = stepDef.progress
      const idx = workflowSteps.findIndex(s => s.key === mappedStep)
      if (idx > maxStepIndex.value) maxStepIndex.value = idx
    }

    // 处理 Writer 输出 → 更新预览
    if (log.agent_name === 'Writer' && log.step_content) {
      const content = log.step_content
      if (content.includes('TITLE:') && content.includes('CONTENT:')) {
        const titleMatch = content.match(/TITLE:\s*(.+?)(?:\n|CONTENT:)/s)
        const contentMatch = content.match(/CONTENT:\s*([\s\S]*)$/)
        if (titleMatch) xhsPreview.value.title = titleMatch[1].trim()
        if (contentMatch) xhsPreview.value.content = contentMatch[1].trim()
      } else {
        xhsPreview.value.content = content
      }
    }

    // 处理 Analyst 输出 → 更新洞察
    if ((log.agent_name === 'Analyst' || log.agent_name === 'ControversialConclusion') && log.step_content) {
      insight.value = log.step_content
    }

    // 推演完成
    if (log.status === 'completed') {
      maxProgress.value = 100
    }
  })
}, { deep: true, immediate: true })

// 监听最终文案变化 → 同步到预览
watch(() => analysisStore.finalCopy, (newCopy) => {
  if (newCopy?.title) xhsPreview.value.title = newCopy.title
  if (newCopy?.body) xhsPreview.value.content = newCopy.body
}, { deep: true, immediate: true })

// 监听编辑内容变化 → 实时同步到预览
watch(() => editableContent.value, (newContent) => {
  if (isEditing.value && newContent) {
    xhsPreview.value.title = newContent.title || ''
    xhsPreview.value.content = newContent.body || ''
  }
}, { deep: true })

// 复制到剪贴板
const copyToClipboard = async () => {
  const text = finalCopyText.value
  if (!text) { alert('暂无内容可复制'); return }
  try {
    await navigator.clipboard.writeText(text)
    alert('已复制到剪贴板')
  } catch (err) {
    console.error('Copy failed:', err)
    alert('复制失败，请手动复制')
  }
}

// 导出图片
const exportAllImages = async () => {
  isExportingImages.value = true
  try {
    const urls = analysisStore.imageUrls || []
    for (let i = 0; i < urls.length; i++) {
      try {
        const res = await fetch(urls[i])
        if (!res.ok) continue
        const blob = await res.blob()
        const downloadUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = `stock_analysis_${i + 1}.jpg`
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(downloadUrl)
      } catch (err) {
        console.error(`Export image ${i + 1} failed:`, err)
      }
    }
    if (urls.length > 0) alert(`成功导出 ${urls.length} 张图片`)
  } finally {
    isExportingImages.value = false
  }
}

// 小红书发布
const xhsStatus = ref({ mcp_available: false, login_status: false, message: '', loading: false })

const checkXhsStatus = async () => {
  xhsStatus.value.loading = true
  try {
    const res = await api.getXhsStatus()
    xhsStatus.value = { mcp_available: res.mcp_available, login_status: res.login_status, message: res.message, loading: false }
  } catch (e) {
    xhsStatus.value = { mcp_available: false, login_status: false, message: '无法连接到后端服务', loading: false }
  }
}

const publishToXhs = async () => {
  const titleToPublish = editableContent.value.title || analysisStore.finalCopy.title
  const bodyToPublish = editableContent.value.body || analysisStore.finalCopy.body
  if (!titleToPublish || !bodyToPublish) return
  if (!confirm('确定要发布到小红书吗？')) return

  isPublishing.value = true
  try {
    // Extract hashtags
    const hashtagRegex = /#([^\s#]+)/g
    const matches = [...bodyToPublish.matchAll(hashtagRegex)]
    const tags = matches.map(m => m[1])
    let contentWithoutTags = bodyToPublish
    const lines = bodyToPublish.split('\n')
    const lastLine = lines[lines.length - 1]?.trim() || ''
    if (lastLine.match(/^(#[^\s#]+\s*)+$/)) {
      contentWithoutTags = lines.slice(0, -1).join('\n').trim()
    }

    const allImages = analysisStore.imageUrls || []
    const res = await api.publishToXhs({
      title: titleToPublish,
      content: contentWithoutTags,
      images: allImages,
      tags: tags.length > 0 ? tags : undefined,
    })
    if (res.success) alert(`发布成功！\n${res.message}`)
    else alert(`发布失败：${res.message}`)
  } catch (e) {
    alert(`发布请求出错: ${e.message || e}`)
  } finally {
    isPublishing.value = false
  }
}

// 历史记录
const loadHistory = () => analysisStore.fetchHistory()

const viewHistoryDetail = async (item) => {
  const detail = await analysisStore.fetchDetail(item.id)
  if (detail) {
    // 可以展示详情弹窗或填充到当前页面
    console.log('History detail loaded:', detail)
  }
}

const formatTime = (ts) => {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return ts }
}

// 生命周期
onMounted(() => {
  refreshTrending()
  hydrateHotTopicDraft()
  checkXhsStatus()
  loadHistory()
  // Fetch market sentiment for mini gauge
  sentimentStore.fetchMarketIndex()
})
</script>


<style scoped>
.debate-bubble {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
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

/* 深色模式 */
:global(html.dark) .debate-bubble {
  background: #1e293b;
  border-color: #334155;
}
:global(html.dark) .debate-bubble.border-yellow-200 {
  background: rgba(234, 179, 8, 0.15);
  border-color: rgba(234, 179, 8, 0.4);
}
:global(html.dark) .debate-bubble.border-blue-200 {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}
:global(html.dark) .debate-bubble.border-red-200 {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
}
:global(html.dark) .debate-bubble.border-purple-200 {
  background: rgba(168, 85, 247, 0.15);
  border-color: rgba(168, 85, 247, 0.4);
}
:global(html.dark) .debate-bubble.border-slate-100,
:global(html.dark) .debate-bubble.border-slate-200 {
  background: rgba(71, 85, 105, 0.3);
  border-color: rgba(71, 85, 105, 0.5);
}
</style>
