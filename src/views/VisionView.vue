<template>
  <div class="view-section animate-fade-in py-12 px-4 overflow-hidden">
    <div class="max-w-7xl mx-auto">
      <!-- Hero 区域 -->
      <div class="relative mb-16 bg-gradient-to-br from-blue-50/50 via-white to-purple-50/50 rounded-5xl p-8 md:p-12 border border-slate-100">
        <!-- 背景装饰 -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none rounded-3xl">
          <div class="absolute -top-20 -right-20 w-96 h-96 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-[100px]"></div>
          <div class="absolute -bottom-20 -left-20 w-96 h-96 bg-gradient-to-br from-emerald-400/20 to-cyan-400/20 rounded-full blur-[100px]"></div>
        </div>

        <div class="text-center relative">
          <div class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full border border-blue-200 mb-6">
            <Sparkles class="w-4 h-4 text-blue-600" />
            <span class="text-sm font-medium text-blue-700">AI 舆情洞察 · 智能内容生成</span>
          </div>
          <h1 class="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            观潮 <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">GlobalInSight</span>
          </h1>
          <p class="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
            基于 Multi-Agent Debate 框架的新一代舆情分析系统<br/>
            让 AI 像专业分析师一样思考、辩论、创作
          </p>
          
          <!-- 核心数据展示 -->
          <div class="flex flex-wrap justify-center gap-4 md:gap-6">
            <div class="stat-card">
              <div class="stat-value">6</div>
              <div class="stat-label">专用 Agent</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">7</div>
              <div class="stat-label">LLM 厂商</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">9+</div>
              <div class="stat-label">数据平台</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">∞</div>
              <div class="stat-label">洞察可能</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 核心价值主张 -->
      <div class="mb-16">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-slate-900 mb-2">为什么选择 GlobalInSight？</h2>
          <p class="text-slate-500">三大核心差异化能力</p>
        </div>

        <div class="grid md:grid-cols-3 gap-6">
          <!-- Multi-Agent Debate -->
          <div class="value-card group">
            <div class="value-icon bg-gradient-to-br from-blue-500 to-indigo-600">
              <MessageSquare class="w-6 h-6 text-white" />
            </div>
            <h3 class="value-title">Multi-Agent Debate</h3>
            <p class="value-desc">
              不是简单的 Prompt 调用，而是多个 AI Agent 之间的真实辩论。
              Reporter 提取事实，Analyst 深度分析，Debater 观点碰撞，Writer 文案输出。
            </p>
            <div class="value-highlight">
              <span class="highlight-tag">LangGraph 编排</span>
              <span class="highlight-tag">状态图驱动</span>
            </div>
          </div>

          <!-- 全链路自动化 -->
          <div class="value-card group">
            <div class="value-icon bg-gradient-to-br from-emerald-500 to-teal-600">
              <Workflow class="w-6 h-6 text-white" />
            </div>
            <h3 class="value-title">全链路自动化</h3>
            <p class="value-desc">
              从热点发现到内容发布的完整闭环。
              热榜采集 → 智能对齐 → 深度分析 → 文案生成 → 图片渲染 → 一键发布小红书。
            </p>
            <div class="value-highlight">
              <span class="highlight-tag">端到端</span>
              <span class="highlight-tag">零人工干预</span>
            </div>
          </div>

          <!-- 可解释 AI -->
          <div class="value-card group">
            <div class="value-icon bg-gradient-to-br from-purple-500 to-pink-600">
              <Eye class="w-6 h-6 text-white" />
            </div>
            <h3 class="value-title">可解释 AI</h3>
            <p class="value-desc">
              每一步推理过程透明可见。
              实时展示 Agent 思考链路、辩论演化时间线、数据来源追溯，让 AI 决策不再是黑箱。
            </p>
            <div class="value-highlight">
              <span class="highlight-tag">思维链可视化</span>
              <span class="highlight-tag">SSE 实时流</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 功能矩阵 -->
      <div class="mb-16">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-slate-900 mb-2">功能全景</h2>
          <p class="text-slate-500">已实现的核心能力</p>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div class="feature-tile" v-for="feature in features" :key="feature.name">
            <component :is="feature.icon" class="feature-icon" :style="{ color: feature.color }" />
            <div class="feature-name">{{ feature.name }}</div>
            <div class="feature-status" :class="feature.status === 'done' ? 'status-done' : 'status-wip'">
              {{ feature.status === 'done' ? '✓ 已上线' : '🚧 开发中' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 技术亮点 Timeline -->
      <div class="mb-16">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-slate-900 mb-2">技术亮点</h2>
          <p class="text-slate-500">让这个项目与众不同的细节</p>
        </div>

        <div class="tech-timeline">
          <div class="timeline-item" v-for="(item, index) in techHighlights" :key="index">
            <div class="timeline-dot" :style="{ background: item.color }"></div>
            <div class="timeline-content">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="timeline-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 应用场景 -->
      <div class="mb-16">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-slate-900 mb-2">谁在使用？</h2>
          <p class="text-slate-500">多元化的应用场景</p>
        </div>

        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="persona-card">
            <div class="persona-avatar bg-gradient-to-br from-pink-400 to-rose-500">
              <PenTool class="w-6 h-6 text-white" />
            </div>
            <div class="persona-title">内容创作者</div>
            <div class="persona-desc">追热点、写爆款、一键发布</div>
          </div>

          <div class="persona-card">
            <div class="persona-avatar bg-gradient-to-br from-blue-400 to-indigo-500">
              <BarChart3 class="w-6 h-6 text-white" />
            </div>
            <div class="persona-title">舆情分析师</div>
            <div class="persona-desc">跨平台监控、趋势预警</div>
          </div>

          <div class="persona-card">
            <div class="persona-avatar bg-gradient-to-br from-emerald-400 to-teal-500">
              <GraduationCap class="w-6 h-6 text-white" />
            </div>
            <div class="persona-title">研究人员</div>
            <div class="persona-desc">数据采集、传播分析</div>
          </div>

          <div class="persona-card">
            <div class="persona-avatar bg-gradient-to-br from-amber-400 to-orange-500">
              <Building2 class="w-6 h-6 text-white" />
            </div>
            <div class="persona-title">企业决策者</div>
            <div class="persona-desc">市场洞察、风险预警</div>
          </div>
        </div>
      </div>

      <!-- 未来路线图 -->
      <div class="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-8 relative overflow-hidden">
        <!-- 背景装饰 -->
        <div class="absolute inset-0 opacity-10">
          <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.3),transparent_50%)]"></div>
          <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.3),transparent_50%)]"></div>
        </div>

        <div class="relative z-10">
          <div class="text-center mb-8">
            <h2 class="text-2xl font-bold text-white mb-2">未来路线图</h2>
            <p class="text-slate-400">持续进化的 AI 舆情系统</p>
          </div>

          <div class="grid md:grid-cols-3 gap-6">
            <div class="roadmap-card">
              <div class="roadmap-phase">Phase 1</div>
              <div class="roadmap-title">能力增强</div>
              <ul class="roadmap-list">
                <li>Twitter/Reddit 国际平台接入</li>
                <li>向量数据库语义检索</li>
                <li>多模态内容理解</li>
              </ul>
            </div>

            <div class="roadmap-card">
              <div class="roadmap-phase">Phase 2</div>
              <div class="roadmap-title">生态扩展</div>
              <ul class="roadmap-list">
                <li>开放 API 接口</li>
                <li>插件化 Agent 市场</li>
                <li>移动端 App</li>
              </ul>
            </div>

            <div class="roadmap-card">
              <div class="roadmap-phase">Phase 3</div>
              <div class="roadmap-title">商业化</div>
              <ul class="roadmap-list">
                <li>SaaS 平台上线</li>
                <li>企业定制服务</li>
                <li>社区生态建设</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Sparkles, MessageSquare, Workflow, Eye, PenTool, BarChart3,
  GraduationCap, Building2, Database, BrainCircuit, Image, Send,
  TrendingUp, GitBranch, Zap, Shield, Clock, Globe
} from 'lucide-vue-next'

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

// 技术亮点数据
const techHighlights = [
  {
    title: 'LangGraph 状态图编排',
    desc: '基于有向图的工作流管理，支持条件分支、循环、并行执行，比传统 Chain 更灵活',
    color: '#3b82f6'
  },
  {
    title: '按需 LLM 调用 + 智能缓存',
    desc: '热点解读仅在用户点击时触发，结合内存+文件双重缓存，大幅降低 Token 成本',
    color: '#10b981'
  },
  {
    title: '跨平台热点对齐算法',
    desc: '基于标题相似度的智能聚类，自动识别同一事件在不同平台的表达',
    color: '#8b5cf6'
  },
  {
    title: 'Canvas API 图片渲染',
    desc: '纯前端生成小红书风格配图，支持雷达图、时间线、趋势图等多种可视化',
    color: '#f59e0b'
  },
  {
    title: '多厂商 LLM Fallback',
    desc: '支持 7 家 LLM 厂商，按 Agent 独立配置，Key 轮换与自动降级',
    color: '#ec4899'
  },
  {
    title: 'SSE 实时流式传输',
    desc: 'Server-Sent Events 推送 Agent 思考过程，前端实时渲染思维链',
    color: '#06b6d4'
  }
]
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 统计卡片 - Vue 官网风格 */
.stat-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 1rem;
  padding: 1.25rem 2rem;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  margin-top: 0.25rem;
  font-weight: 500;
}

/* 价值卡片 */
.value-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.value-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
  border-color: transparent;
}

.value-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.value-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.value-desc {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.value-highlight {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.highlight-tag {
  padding: 0.25rem 0.5rem;
  background: #f1f5f9;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #475569;
}

/* 功能瓦片 */
.feature-tile {
  background: white;
  border-radius: 0.75rem;
  padding: 1rem;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.feature-tile:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.feature-icon {
  width: 1.5rem;
  height: 1.5rem;
  margin: 0 auto 0.5rem;
}

.feature-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.feature-status {
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  display: inline-block;
}

.status-done {
  background: #dcfce7;
  color: #166534;
}

.status-wip {
  background: #fef3c7;
  color: #92400e;
}

/* 技术时间线 */
.tech-timeline {
  display: grid;
  gap: 1rem;
}

.timeline-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.timeline-dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.timeline-content {
  flex: 1;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.timeline-item:last-child .timeline-content {
  border-bottom: none;
}

.timeline-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.timeline-desc {
  font-size: 0.875rem;
  color: #64748b;
}

/* 用户画像卡片 */
.persona-card {
  background: white;
  border-radius: 1rem;
  padding: 1.25rem;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.persona-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.persona-avatar {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 0.75rem;
}

.persona-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.persona-desc {
  font-size: 0.8rem;
  color: #64748b;
}

/* 路线图卡片 */
.roadmap-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 1.5rem;
}

.roadmap-phase {
  font-size: 0.75rem;
  font-weight: 600;
  color: #60a5fa;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.roadmap-title {
  font-size: 1.125rem;
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
  font-size: 0.875rem;
  color: #94a3b8;
  padding: 0.375rem 0;
  padding-left: 1rem;
  position: relative;
}

.roadmap-list li::before {
  content: '→';
  position: absolute;
  left: 0;
  color: #60a5fa;
}
</style>
