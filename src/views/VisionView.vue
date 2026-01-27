<template>
  <div class="vision-page relative min-h-screen overflow-x-hidden" :class="isDarkMode ? 'dark-theme' : 'light-theme'">
    <!-- Three.js 背景 - 根据主题切换 -->
    <CosmicBackground v-if="isDarkMode" />
    <OceanWaveBackground v-else />
    
    <div class="relative z-10">
      <!-- Hero 区域 -->
      <section class="hero-section min-h-screen flex flex-col items-center justify-center px-4 py-20 relative">
        <div class="text-center max-w-4xl mx-auto">
          <div ref="badgeRef" class="inline-flex items-center gap-2 px-4 py-2 backdrop-blur-sm rounded-full mb-6 opacity-0"
               :class="isDarkMode ? 'bg-white/10 border border-white/20' : 'bg-white/80 border border-slate-200 shadow-lg'">
            <Sparkles class="w-4 h-4" :class="isDarkMode ? 'text-blue-400' : 'text-blue-500'" />
            <span class="text-sm font-medium" :class="isDarkMode ? 'text-blue-300' : 'text-blue-600'">AI 舆情洞察 · 智能内容生成</span>
          </div>
          
          <h1 ref="titleRef" class="text-5xl md:text-7xl font-black mb-6 opacity-0" :class="isDarkMode ? 'text-white' : 'text-slate-900'">
            观潮 <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">GlobalInSight</span>
          </h1>
          
          <p ref="subtitleRef" class="text-xl md:text-2xl mb-12 opacity-0" :class="isDarkMode ? 'text-slate-300' : 'text-slate-600'">
            基于 Multi-Agent Debate 框架的新一代舆情分析系统<br/>
            让 AI 像专业分析师一样思考、辩论、创作
          </p>
          
          <!-- 核心数据展示 -->
          <div ref="statsRef" class="flex flex-wrap justify-center gap-6 md:gap-10 opacity-0">
            <div :class="isDarkMode ? 'stat-card' : 'stat-card-light'">
              <div class="stat-value" data-value="6">0</div>
              <div class="stat-label" :class="isDarkMode ? '' : 'text-slate-500'">专用 Agent</div>
            </div>
            <div :class="isDarkMode ? 'stat-card' : 'stat-card-light'">
              <div class="stat-value" data-value="7">0</div>
              <div class="stat-label" :class="isDarkMode ? '' : 'text-slate-500'">LLM 厂商</div>
            </div>
            <div :class="isDarkMode ? 'stat-card' : 'stat-card-light'">
              <div class="stat-value" data-value="9">0</div>
              <div class="stat-label" :class="isDarkMode ? '' : 'text-slate-500'">数据平台</div>
            </div>
            <div :class="isDarkMode ? 'stat-card' : 'stat-card-light'">
              <div class="stat-value">∞</div>
              <div class="stat-label" :class="isDarkMode ? '' : 'text-slate-500'">洞察可能</div>
            </div>
          </div>
        </div>
        
        <!-- 滚动提示 - 放在 flex 容器底部 -->
        <div ref="scrollHintRef" class="mt-auto pt-8 opacity-0">
          <div class="flex flex-col items-center" :class="isDarkMode ? 'text-slate-400' : 'text-slate-500'">
            <span class="text-sm mb-2">向下滚动探索</span>
            <ChevronDown class="w-6 h-6 animate-bounce" />
          </div>
        </div>
      </section>

      <!-- 核心价值主张 -->
      <section class="py-20 px-4">
        <div class="max-w-6xl mx-auto">
          <div class="text-center mb-16">
            <h2 ref="valuesTitleRef" class="text-3xl md:text-4xl font-bold mb-4" :class="isDarkMode ? 'text-white' : 'text-slate-900'">
              为什么选择 GlobalInSight？
            </h2>
            <p ref="valuesSubRef" class="text-lg" :class="isDarkMode ? 'text-slate-400' : 'text-slate-500'">三大核心差异化能力</p>
          </div>

          <div class="grid md:grid-cols-3 gap-8">
            <div ref="value1Ref" :class="isDarkMode ? 'value-card' : 'value-card-light'">
              <div class="value-icon bg-gradient-to-br from-blue-500 to-indigo-600">
                <MessageSquare class="w-8 h-8 text-white" />
              </div>
              <h3 class="value-title" :class="isDarkMode ? '' : 'text-slate-900'">Multi-Agent Debate</h3>
              <p class="value-desc" :class="isDarkMode ? '' : 'text-slate-600'">
                不是简单的 Prompt 调用，而是多个 AI Agent 之间的真实辩论。
                Reporter 提取事实，Analyst 深度分析，Debater 观点碰撞，Writer 文案输出。
              </p>
              <div class="value-tags">
                <span :class="isDarkMode ? '' : 'tag-light'">LangGraph 编排</span>
                <span :class="isDarkMode ? '' : 'tag-light'">状态图驱动</span>
              </div>
            </div>

            <div ref="value2Ref" :class="isDarkMode ? 'value-card' : 'value-card-light'">
              <div class="value-icon bg-gradient-to-br from-emerald-500 to-teal-600">
                <Workflow class="w-8 h-8 text-white" />
              </div>
              <h3 class="value-title" :class="isDarkMode ? '' : 'text-slate-900'">全链路自动化</h3>
              <p class="value-desc" :class="isDarkMode ? '' : 'text-slate-600'">
                从热点发现到内容发布的完整闭环。
                热榜采集 → 智能对齐 → 深度分析 → 文案生成 → 图片渲染 → 一键发布小红书。
              </p>
              <div class="value-tags">
                <span :class="isDarkMode ? '' : 'tag-light'">端到端</span>
                <span :class="isDarkMode ? '' : 'tag-light'">零人工干预</span>
              </div>
            </div>

            <div ref="value3Ref" :class="isDarkMode ? 'value-card' : 'value-card-light'">
              <div class="value-icon bg-gradient-to-br from-purple-500 to-pink-600">
                <Eye class="w-8 h-8 text-white" />
              </div>
              <h3 class="value-title" :class="isDarkMode ? '' : 'text-slate-900'">可解释 AI</h3>
              <p class="value-desc" :class="isDarkMode ? '' : 'text-slate-600'">
                每一步推理过程透明可见。
                实时展示 Agent 思考链路、辩论演化时间线、数据来源追溯，让 AI 决策不再是黑箱。
              </p>
              <div class="value-tags">
                <span :class="isDarkMode ? '' : 'tag-light'">思维链可视化</span>
                <span :class="isDarkMode ? '' : 'tag-light'">SSE 实时流</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 功能矩阵 -->
      <section class="py-20 px-4">
        <div class="max-w-6xl mx-auto">
          <div class="text-center mb-12">
            <h2 ref="featuresTitleRef" class="text-3xl font-bold mb-4" :class="isDarkMode ? 'text-white' : 'text-slate-900'">功能全景</h2>
            <p ref="featuresSubRef" :class="isDarkMode ? 'text-slate-400' : 'text-slate-500'">已实现的核心能力</p>
          </div>

          <div ref="featuresGridRef" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div v-for="(feature, index) in features" :key="feature.name" 
                 :class="[isDarkMode ? 'feature-tile' : 'feature-tile-light', 'feature-item']"
                 :style="{ transitionDelay: `${index * 50}ms` }">
              <component :is="feature.icon" class="feature-icon" :style="{ color: feature.color }" />
              <div class="feature-name" :class="isDarkMode ? '' : 'text-slate-700'">{{ feature.name }}</div>
              <div class="feature-status" :class="feature.status === 'done' ? 'status-done' : 'status-wip'">
                {{ feature.status === 'done' ? '✓ 已上线' : '🚧 开发中' }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 应用场景 -->
      <section class="py-20 px-4">
        <div class="max-w-6xl mx-auto">
          <div class="text-center mb-12">
            <h2 ref="personasTitleRef" class="text-3xl font-bold mb-4" :class="isDarkMode ? 'text-white' : 'text-slate-900'">谁在使用？</h2>
            <p ref="personasSubRef" :class="isDarkMode ? 'text-slate-400' : 'text-slate-500'">多元化的应用场景</p>
          </div>

          <div ref="personasGridRef" class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div :class="[isDarkMode ? 'persona-card' : 'persona-card-light', 'persona-item']">
              <div class="persona-avatar bg-gradient-to-br from-pink-400 to-rose-500">
                <PenTool class="w-8 h-8 text-white" />
              </div>
              <div class="persona-title" :class="isDarkMode ? '' : 'text-slate-900'">内容创作者</div>
              <div class="persona-desc" :class="isDarkMode ? '' : 'text-slate-500'">追热点、写爆款、一键发布</div>
            </div>

            <div :class="[isDarkMode ? 'persona-card' : 'persona-card-light', 'persona-item']">
              <div class="persona-avatar bg-gradient-to-br from-blue-400 to-indigo-500">
                <BarChart3 class="w-8 h-8 text-white" />
              </div>
              <div class="persona-title" :class="isDarkMode ? '' : 'text-slate-900'">舆情分析师</div>
              <div class="persona-desc" :class="isDarkMode ? '' : 'text-slate-500'">跨平台监控、趋势预警</div>
            </div>

            <div :class="[isDarkMode ? 'persona-card' : 'persona-card-light', 'persona-item']">
              <div class="persona-avatar bg-gradient-to-br from-emerald-400 to-teal-500">
                <GraduationCap class="w-8 h-8 text-white" />
              </div>
              <div class="persona-title" :class="isDarkMode ? '' : 'text-slate-900'">研究人员</div>
              <div class="persona-desc" :class="isDarkMode ? '' : 'text-slate-500'">数据采集、传播分析</div>
            </div>

            <div :class="[isDarkMode ? 'persona-card' : 'persona-card-light', 'persona-item']">
              <div class="persona-avatar bg-gradient-to-br from-amber-400 to-orange-500">
                <Building2 class="w-8 h-8 text-white" />
              </div>
              <div class="persona-title" :class="isDarkMode ? '' : 'text-slate-900'">企业决策者</div>
              <div class="persona-desc" :class="isDarkMode ? '' : 'text-slate-500'">市场洞察、风险预警</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 未来路线图 -->
      <section class="py-20 px-4">
        <div class="max-w-6xl mx-auto">
          <div :class="isDarkMode ? 'roadmap-container' : 'roadmap-container-light'" class="rounded-3xl p-8 md:p-12 relative overflow-hidden">
            <!-- 背景装饰 -->
            <div class="absolute inset-0 opacity-20">
              <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.4),transparent_50%)]"></div>
              <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.4),transparent_50%)]"></div>
            </div>

            <div class="relative z-10">
              <div class="text-center mb-12">
                <h2 ref="roadmapTitleRef" class="text-3xl font-bold mb-4" :class="isDarkMode ? 'text-white' : 'text-slate-900'">未来路线图</h2>
                <p ref="roadmapSubRef" :class="isDarkMode ? 'text-slate-300' : 'text-slate-600'">持续进化的 AI 舆情系统</p>
              </div>

              <div ref="roadmapGridRef" class="grid md:grid-cols-3 gap-6">
                <div :class="[isDarkMode ? 'roadmap-card' : 'roadmap-card-light', 'roadmap-item']">
                  <div class="roadmap-phase">Phase 1</div>
                  <div class="roadmap-title" :class="isDarkMode ? '' : 'text-slate-900'">能力增强</div>
                  <ul class="roadmap-list" :class="isDarkMode ? '' : 'list-light'">
                    <li>Twitter/Reddit 国际平台接入</li>
                    <li>向量数据库语义检索</li>
                    <li>多模态内容理解</li>
                  </ul>
                </div>

                <div :class="[isDarkMode ? 'roadmap-card' : 'roadmap-card-light', 'roadmap-item']">
                  <div class="roadmap-phase">Phase 2</div>
                  <div class="roadmap-title" :class="isDarkMode ? '' : 'text-slate-900'">生态扩展</div>
                  <ul class="roadmap-list" :class="isDarkMode ? '' : 'list-light'">
                    <li>开放 API 接口</li>
                    <li>插件化 Agent 市场</li>
                    <li>移动端 App</li>
                  </ul>
                </div>

                <div :class="[isDarkMode ? 'roadmap-card' : 'roadmap-card-light', 'roadmap-item']">
                  <div class="roadmap-phase">Phase 3</div>
                  <div class="roadmap-title" :class="isDarkMode ? '' : 'text-slate-900'">商业化</div>
                  <ul class="roadmap-list" :class="isDarkMode ? '' : 'list-light'">
                    <li>SaaS 平台上线</li>
                    <li>企业定制服务</li>
                    <li>社区生态建设</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  Sparkles, MessageSquare, Workflow, Eye, PenTool, BarChart3,
  GraduationCap, Building2, Database, BrainCircuit, Image, Send,
  TrendingUp, GitBranch, Zap, Shield, Clock, Globe, ChevronDown
} from 'lucide-vue-next'
import CosmicBackground from '@/components/CosmicBackground.vue'
import OceanWaveBackground from '@/components/OceanWaveBackground.vue'
import { useConfigStore } from '@/stores/config'

gsap.registerPlugin(ScrollTrigger)

// Store
const configStore = useConfigStore()
const isDarkMode = computed(() => configStore.isDarkMode)

// Refs
const badgeRef = ref(null)
const titleRef = ref(null)
const subtitleRef = ref(null)
const statsRef = ref(null)
const scrollHintRef = ref(null)
const valuesTitleRef = ref(null)
const valuesSubRef = ref(null)
const value1Ref = ref(null)
const value2Ref = ref(null)
const value3Ref = ref(null)
const featuresTitleRef = ref(null)
const featuresSubRef = ref(null)
const featuresGridRef = ref(null)
const personasTitleRef = ref(null)
const personasSubRef = ref(null)
const personasGridRef = ref(null)
const roadmapTitleRef = ref(null)
const roadmapSubRef = ref(null)
const roadmapGridRef = ref(null)

// 功能矩阵数据
const features = [
  { name: '多平台热榜', icon: Database, color: '#3b82f6', status: 'done' },
  { name: 'Multi-Agent', icon: BrainCircuit, color: '#10b981', status: 'done' },
  { name: 'AI 图片生成', icon: Image, color: '#f59e0b', status: 'done' },
  { name: '小红书发布', icon: Send, color: '#ec4899', status: 'done' },
  { name: '热度趋势', icon: TrendingUp, color: '#8b5cf6', status: 'done' },
  { name: '辩论时间线', icon: GitBranch, color: '#06b6d4', status: 'done' },
  { name: '多 LLM 支持', icon: Zap, color: '#eab308', status: 'done' },
  { name: '内容安全', icon: Shield, color: '#ef4444', status: 'done' },
  { name: '实时 SSE', icon: Clock, color: '#14b8a6', status: 'done' },
  { name: '国际平台', icon: Globe, color: '#6366f1', status: 'wip' },
  { name: '语义检索', icon: Database, color: '#a855f7', status: 'wip' },
  { name: '移动端', icon: Send, color: '#f97316', status: 'wip' }
]

let ctx

onMounted(async () => {
  await nextTick()
  
  ctx = gsap.context(() => {
    // Hero 动画序列
    const heroTl = gsap.timeline()
    heroTl
      .to(badgeRef.value, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' })
      .to(titleRef.value, { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }, '-=0.3')
      .to(subtitleRef.value, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '-=0.4')
      .to(statsRef.value, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '-=0.3')
      .to(scrollHintRef.value, { opacity: 1, duration: 0.6 }, '-=0.2')

    // 数字计数动画
    gsap.utils.toArray('.stat-value[data-value]').forEach(el => {
      const value = parseInt(el.dataset.value)
      gsap.to(el, {
        innerHTML: value,
        duration: 2,
        ease: 'power2.out',
        snap: { innerHTML: 1 },
        delay: 1
      })
    })

    // 价值主张标题动画
    gsap.to([valuesTitleRef.value, valuesSubRef.value], {
      opacity: 1,
      y: 0,
      duration: 0.6,
      stagger: 0.1,
      scrollTrigger: {
        trigger: valuesTitleRef.value,
        start: 'top 80%'
      }
    })

    // 价值卡片动画
    gsap.to([value1Ref.value, value2Ref.value, value3Ref.value], {
      opacity: 1,
      y: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: value1Ref.value,
        start: 'top 85%'
      }
    })

    // 功能矩阵标题动画
    gsap.to([featuresTitleRef.value, featuresSubRef.value], {
      opacity: 1,
      y: 0,
      duration: 0.6,
      stagger: 0.1,
      scrollTrigger: {
        trigger: featuresTitleRef.value,
        start: 'top 80%'
      }
    })

    // 功能瓦片动画
    gsap.to('.feature-item', {
      opacity: 1,
      y: 0,
      duration: 0.5,
      stagger: 0.05,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: featuresGridRef.value,
        start: 'top 85%'
      }
    })

    // 用户画像标题动画
    gsap.to([personasTitleRef.value, personasSubRef.value], {
      opacity: 1,
      y: 0,
      duration: 0.6,
      stagger: 0.1,
      scrollTrigger: {
        trigger: personasTitleRef.value,
        start: 'top 80%'
      }
    })

    // 用户画像卡片动画
    gsap.to('.persona-item', {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.6,
      stagger: 0.1,
      ease: 'back.out(1.2)',
      scrollTrigger: {
        trigger: personasGridRef.value,
        start: 'top 85%'
      }
    })

    // 路线图标题动画
    gsap.to([roadmapTitleRef.value, roadmapSubRef.value], {
      opacity: 1,
      y: 0,
      duration: 0.6,
      stagger: 0.1,
      scrollTrigger: {
        trigger: roadmapTitleRef.value,
        start: 'top 80%'
      }
    })

    // 路线图卡片动画
    gsap.to('.roadmap-item', {
      opacity: 1,
      x: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: roadmapGridRef.value,
        start: 'top 85%'
      }
    })
  })

  // 初始化元素位置
  gsap.set([badgeRef.value, titleRef.value, subtitleRef.value, statsRef.value], { y: 30, opacity: 0 })
  gsap.set([valuesTitleRef.value, valuesSubRef.value], { y: 20, opacity: 0 })
  gsap.set([value1Ref.value, value2Ref.value, value3Ref.value], { y: 40, opacity: 0 })
  gsap.set([featuresTitleRef.value, featuresSubRef.value], { y: 20, opacity: 0 })
  gsap.set('.feature-item', { y: 20, opacity: 0 })
  gsap.set([personasTitleRef.value, personasSubRef.value], { y: 20, opacity: 0 })
  gsap.set('.persona-item', { y: 30, scale: 0.95, opacity: 0 })
  gsap.set([roadmapTitleRef.value, roadmapSubRef.value], { y: 20, opacity: 0 })
  gsap.set('.roadmap-item', { x: -30, opacity: 0 })
})

onUnmounted(() => {
  ctx?.revert()
  ScrollTrigger.getAll().forEach(t => t.kill())
})
</script>


<style scoped>
/* ========== 浅色模式样式 ========== */

/* 统计卡片 - 浅色主题 */
.stat-card-light {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 1.5rem;
  padding: 1.5rem 2.5rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  transition: all 0.4s ease;
}

.stat-card-light:hover {
  transform: translateY(-8px) scale(1.02);
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 16px 48px rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}

/* 价值卡片 - 浅色主题 */
.value-card-light {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  padding: 2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  transition: all 0.4s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.value-card-light::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.value-card-light:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 50px rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(255, 255, 255, 1);
}

.value-card-light:hover::before {
  opacity: 1;
}

.value-card-light .value-title {
  color: #1e293b;
}

.value-card-light .value-desc {
  color: #64748b;
}

.tag-light {
  background: rgba(59, 130, 246, 0.1) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
  color: #3b82f6 !important;
}

/* 功能瓦片 - 浅色主题 */
.feature-tile-light {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 1.25rem;
  text-align: center;
  border: 1px solid rgba(148, 163, 184, 0.2);
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.feature-tile-light:hover {
  transform: scale(1.08) translateY(-4px);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(255, 255, 255, 1);
}

.feature-tile-light .feature-name {
  color: #334155;
}

/* 用户画像卡片 - 浅色主题 */
.persona-card-light {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  border-radius: 1.25rem;
  padding: 2rem;
  text-align: center;
  border: 1px solid rgba(148, 163, 184, 0.2);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.persona-card-light:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 20px 40px rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(255, 255, 255, 1);
}

.persona-card-light .persona-title {
  color: #1e293b;
}

.persona-card-light .persona-desc {
  color: #64748b;
}

/* 路线图容器 - 浅色主题 */
.roadmap-container-light {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
  border: 1px solid rgba(148, 163, 184, 0.3);
}

/* 路线图卡片 - 浅色主题 */
.roadmap-card-light {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 1rem;
  padding: 1.75rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.roadmap-card-light .roadmap-title {
  color: #1e293b;
}

.list-light li {
  color: #64748b !important;
}

/* ========== 深色模式样式 ========== */

/* 统计卡片 - 深色主题 */
.stat-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1.5rem;
  padding: 1.5rem 2.5rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.4s ease;
}

.stat-card:hover {
  transform: translateY(-8px) scale(1.02);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 16px 48px rgba(59, 130, 246, 0.3);
  border-color: rgba(59, 130, 246, 0.4);
}

.stat-value {
  font-size: 3.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
}

.stat-label {
  font-size: 0.9rem;
  color: #94a3b8;
  margin-top: 0.5rem;
  font-weight: 500;
}

/* 价值卡片 - 深色主题 */
.value-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.4s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.value-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.value-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 50px rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(255, 255, 255, 0.08);
}

.value-card:hover::before {
  opacity: 1;
}

.value-icon {
  width: 4rem;
  height: 4rem;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.value-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.75rem;
}

.value-desc {
  font-size: 0.95rem;
  color: #94a3b8;
  line-height: 1.7;
  margin-bottom: 1.25rem;
}

.value-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.value-tags span {
  padding: 0.375rem 0.75rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.5rem;
  font-size: 0.8rem;
  color: #60a5fa;
  font-weight: 500;
  transition: all 0.3s ease;
}

.value-tags span:hover {
  background: rgba(59, 130, 246, 0.3);
  transform: translateY(-2px);
}

/* 功能瓦片 - 深色主题 */
.feature-tile {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 1.25rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.feature-tile:hover {
  transform: scale(1.08) translateY(-4px);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.25);
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(255, 255, 255, 0.08);
}

.feature-icon {
  width: 2rem;
  height: 2rem;
  margin: 0 auto 0.75rem;
  filter: drop-shadow(0 0 8px currentColor);
  transition: filter 0.3s ease;
}

.feature-tile:hover .feature-icon,
.feature-tile-light:hover .feature-icon {
  filter: drop-shadow(0 0 12px currentColor);
}

.feature-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 0.5rem;
}

.feature-status {
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  display: inline-block;
}

.status-done {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-wip {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

/* 用户画像卡片 - 深色主题 */
.persona-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  border-radius: 1.25rem;
  padding: 2rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.persona-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(255, 255, 255, 0.08);
}

.persona-avatar {
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  position: relative;
  z-index: 1;
}

.persona-title {
  font-weight: 700;
  font-size: 1.1rem;
  color: #ffffff;
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
}

.persona-desc {
  font-size: 0.9rem;
  color: #94a3b8;
  position: relative;
  z-index: 1;
}

/* 路线图 */
.roadmap-container {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

.roadmap-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 1.75rem;
  backdrop-filter: blur(10px);
}

.roadmap-phase {
  font-size: 0.8rem;
  font-weight: 600;
  color: #60a5fa;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}

.roadmap-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1rem;
}

.roadmap-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.roadmap-list li {
  font-size: 0.9rem;
  color: #94a3b8;
  padding: 0.5rem 0;
  padding-left: 1.25rem;
  position: relative;
}

.roadmap-list li::before {
  content: '→';
  position: absolute;
  left: 0;
  color: #60a5fa;
}
</style>
