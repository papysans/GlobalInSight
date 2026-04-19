<template>
  <!--
    系统架构页
    - 展示 Multi-Agent 系统的数据流与组件关系
    - 主要为静态展示：3D 网络可视化 + 数据处理流水线 + 能力矩阵
  -->
  <div class="view-section animate-fade-in py-12 px-4 overflow-hidden">
    <div class="max-w-7xl mx-auto">
      <!-- 标题区域 -->
      <div class="text-center mb-12 relative">
        <div class="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
          <Network class="w-96 h-96 text-blue-600 animate-pulse-slow" />
        </div>
        <h2 class="text-3xl md:text-4xl font-bold text-slate-900 mb-4 relative">系统技术架构</h2>
        <p class="text-slate-500 text-lg relative">Multi-Agent Debate Framework · LangGraph Orchestration</p>
      </div>

      <!-- 3D Agent 网络可视化 -->
      <div class="mb-12">
        <h3 class="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
          <BrainCircuit class="w-6 h-6 text-emerald-600" />
          Multi-Agent 协作网络
          <span class="text-sm font-normal text-slate-400 ml-2">（鼠标悬停查看详情）</span>
        </h3>
        <AgentNetwork3D />
      </div>

      <!-- 数据流架构图 -->
      <div class="arch-pipeline-section rounded-2xl shadow-2xl p-8 md:p-12 mb-8 relative overflow-hidden">
        <!-- 背景动画网格 -->
        <div class="absolute inset-0 opacity-10">
          <div class="grid-bg"></div>
        </div>
        
        <!-- 流动粒子效果 -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none">
          <div class="particle particle-1"></div>
          <div class="particle particle-2"></div>
          <div class="particle particle-3"></div>
        </div>

        <h3 class="text-xl font-bold arch-pipeline-title mb-8 flex items-center gap-2 relative z-10">
          <Workflow class="w-6 h-6 text-blue-500" />
          数据处理流水线
        </h3>

        <!-- 横向流程图 -->
        <div class="relative z-10">
          <div class="flex flex-col lg:flex-row items-center justify-between gap-4 lg:gap-2">
            <!-- 数据源 -->
            <div class="arch-node bg-gradient-to-br from-blue-600 to-blue-700 w-full lg:w-44">
              <Database class="w-6 h-6 text-blue-200 mb-2" />
              <div class="text-sm font-bold text-white">数据采集层</div>
              <div class="text-xs text-blue-200 mt-1">TopHub · HN · MediaCrawler</div>
            </div>

            <ArrowRight class="hidden lg:block w-8 h-8 text-blue-400 animate-pulse flex-shrink-0" />
            <ArrowDown class="lg:hidden w-8 h-8 text-blue-400 animate-pulse flex-shrink-0" />

            <!-- 处理层 -->
            <div class="arch-node bg-gradient-to-br from-purple-600 to-purple-700 w-full lg:w-44">
              <Cpu class="w-6 h-6 text-purple-200 mb-2" />
              <div class="text-sm font-bold text-white">智能处理层</div>
              <div class="text-xs text-purple-200 mt-1">对齐聚类 · 信号分析</div>
            </div>

            <ArrowRight class="hidden lg:block w-8 h-8 text-purple-400 animate-pulse flex-shrink-0" />
            <ArrowDown class="lg:hidden w-8 h-8 text-purple-400 animate-pulse flex-shrink-0" />

            <!-- Agent层 - 核心 -->
            <div class="arch-node-core bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 w-full lg:w-56 ring-2 ring-emerald-400/50 ring-offset-2 ring-offset-slate-900">
              <BrainCircuit class="w-8 h-8 text-white mb-2 animate-pulse" />
              <div class="text-base font-bold text-white">Multi-Agent Core</div>
              <div class="text-xs text-emerald-100 mt-1">Reporter → Analyst → Debater → Writer</div>
              <div class="mt-2 flex gap-1 justify-center">
                <span class="px-1.5 py-0.5 bg-white/20 rounded text-[10px] text-white">LangGraph</span>
                <span class="px-1.5 py-0.5 bg-white/20 rounded text-[10px] text-white">SSE</span>
              </div>
            </div>

            <ArrowRight class="hidden lg:block w-8 h-8 text-emerald-400 animate-pulse flex-shrink-0" />
            <ArrowDown class="lg:hidden w-8 h-8 text-emerald-400 animate-pulse flex-shrink-0" />

            <!-- 生成层 -->
            <div class="arch-node bg-gradient-to-br from-orange-600 to-orange-700 w-full lg:w-44">
              <Sparkles class="w-6 h-6 text-orange-200 mb-2" />
              <div class="text-sm font-bold text-white">内容生成层</div>
              <div class="text-xs text-orange-200 mt-1">文案 · 图片 · Canvas</div>
            </div>

            <ArrowRight class="hidden lg:block w-8 h-8 text-orange-400 animate-pulse flex-shrink-0" />
            <ArrowDown class="lg:hidden w-8 h-8 text-orange-400 animate-pulse flex-shrink-0" />

            <!-- 发布层 -->
            <div class="arch-node bg-gradient-to-br from-pink-600 to-rose-600 w-full lg:w-44">
              <Send class="w-6 h-6 text-pink-200 mb-2" />
              <div class="text-sm font-bold text-white">自动发布层</div>
              <div class="text-xs text-pink-200 mt-1">小红书 MCP</div>
            </div>
          </div>
        </div>

        <!-- 底部技术标签 -->
        <div class="mt-8 flex flex-wrap justify-center gap-2 relative z-10">
          <span class="tech-tag-adaptive">FastAPI</span>
          <span class="tech-tag-adaptive">LangChain</span>
          <span class="tech-tag-adaptive">LangGraph</span>
          <span class="tech-tag-adaptive">Vue 3</span>
          <span class="tech-tag-adaptive">Pinia</span>
          <span class="tech-tag-adaptive">Canvas API</span>
          <span class="tech-tag-adaptive">SSE</span>
          <span class="tech-tag-adaptive">火山引擎</span>
        </div>
      </div>

      <!-- LLM 支持矩阵 -->
      <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 mb-8">
        <h3 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Zap class="w-5 h-5 text-amber-500" />
          多厂商 LLM 支持 · 智能 Fallback
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <div class="llm-badge llm-deepseek">
            <span class="llm-name">DeepSeek</span>
            <span class="llm-model">Chat / Reasoner</span>
          </div>
          <div class="llm-badge llm-gemini">
            <span class="llm-name">Gemini</span>
            <span class="llm-model">3 Pro / Flash</span>
          </div>
          <div class="llm-badge llm-kimi">
            <span class="llm-name">Kimi</span>
            <span class="llm-model">K2 Turbo</span>
          </div>
          <div class="llm-badge llm-doubao">
            <span class="llm-name">豆包</span>
            <span class="llm-model">Seed 1.6</span>
          </div>
          <div class="llm-badge llm-zhipu">
            <span class="llm-name">智谱</span>
            <span class="llm-model">GLM-4.7</span>
          </div>
          <div class="llm-badge llm-minimax">
            <span class="llm-name">MiniMax</span>
            <span class="llm-model">M2.1</span>
          </div>
          <div class="llm-badge llm-openai">
            <span class="llm-name">OpenAI</span>
            <span class="llm-model">GPT-4o</span>
          </div>
        </div>
        <p class="text-xs text-slate-500 mt-3 text-center">* 支持按 Agent 独立配置 Provider/Model，Key 轮换与自动 Fallback</p>
      </div>

      <!-- 技术栈详情 -->
      <div class="grid md:grid-cols-3 gap-6">
        <div class="tech-stack-card">
          <div class="tech-stack-header bg-gradient-to-r from-blue-500 to-blue-600">
            <Server class="w-5 h-5" />
            <span>后端架构</span>
          </div>
          <ul class="tech-stack-list">
            <li><strong>FastAPI</strong> - 高性能异步 API</li>
            <li><strong>LangGraph</strong> - 状态图工作流编排</li>
            <li><strong>LangChain</strong> - LLM 抽象层</li>
            <li><strong>httpx</strong> - 异步 HTTP 客户端</li>
            <li><strong>Pydantic</strong> - 数据验证</li>
            <li><strong>APScheduler</strong> - 定时任务</li>
          </ul>
        </div>

        <div class="tech-stack-card">
          <div class="tech-stack-header bg-gradient-to-r from-emerald-500 to-emerald-600">
            <Monitor class="w-5 h-5" />
            <span>前端架构</span>
          </div>
          <ul class="tech-stack-list">
            <li><strong>Vue 3</strong> - Composition API</li>
            <li><strong>Pinia</strong> - 响应式状态管理</li>
            <li><strong>Three.js</strong> - 3D 可视化</li>
            <li><strong>GSAP</strong> - 高级动画</li>
            <li><strong>Canvas API</strong> - 图片生成</li>
            <li><strong>Tailwind CSS</strong> - 原子化样式</li>
          </ul>
        </div>

        <div class="tech-stack-card">
          <div class="tech-stack-header bg-gradient-to-r from-purple-500 to-purple-600">
            <Cloud class="w-5 h-5" />
            <span>外部服务</span>
          </div>
          <ul class="tech-stack-list">
            <li><strong>火山引擎</strong> - AI 图片生成</li>
            <li><strong>小红书 MCP</strong> - 自动发布</li>
            <li><strong>TopHub</strong> - 国内热榜聚合</li>
            <li><strong>Hacker News</strong> - 海外科技热点</li>
            <li><strong>MediaCrawler</strong> - 深度爬虫</li>
            <li><strong>SSE</strong> - 实时流式传输</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 该页面为展示型页面，仅引入图标与可视化组件，不包含业务状态
import {
  Network, Database, Cpu, BrainCircuit, Sparkles, Send, ArrowRight, ArrowDown,
  Workflow, Zap, Server, Monitor, Cloud
} from 'lucide-vue-next'
import AgentNetwork3D from '@/components/AgentNetwork3D.vue'
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-pulse-slow {
  animation: pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 网格背景 */
.grid-bg {
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(40px, 40px); }
}

/* 流动粒子 */
.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  border-radius: 50%;
  filter: blur(1px);
}

.particle-1 {
  top: 20%;
  animation: particleFlow 8s linear infinite;
}

.particle-2 {
  top: 50%;
  animation: particleFlow 6s linear infinite 2s;
}

.particle-3 {
  top: 80%;
  animation: particleFlow 10s linear infinite 4s;
}

@keyframes particleFlow {
  0% { left: -10px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: calc(100% + 10px); opacity: 0; }
}

/* 架构节点 */
.arch-node {
  padding: 1rem;
  border-radius: 0.75rem;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.arch-node:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.arch-node-core {
  padding: 1.25rem;
  border-radius: 1rem;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}

.arch-node-core:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 30px rgba(16, 185, 129, 0.4);
}

/* 技术标签 */
.tech-tag {
  padding: 0.25rem 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 9999px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.2s ease;
}

.tech-tag:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* 自适应技术标签 - Light/Dark 模式 */
.tech-tag-adaptive {
  padding: 0.25rem 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 9999px;
  font-size: 0.75rem;
  color: #3b82f6;
  transition: all 0.2s ease;
}

.tech-tag-adaptive:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #2563eb;
}

/* 数据流水线区域 - 自适应主题 (Light Mode) */
.arch-pipeline-section {
  background: linear-gradient(to bottom right, #f8fafc, #f1f5f9, #e2e8f0);
  border: 1px solid #e2e8f0;
}

.arch-pipeline-title {
  color: #1e293b;
}

/* Dark mode styles are in src/style.css for proper global scoping */

/* LLM 徽章 */
.llm-badge {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  text-align: center;
  transition: all 0.2s ease;
}

.llm-badge:hover {
  transform: scale(1.05);
}

.llm-name {
  display: block;
  font-weight: 600;
  font-size: 0.75rem;
}

.llm-model {
  display: block;
  font-size: 0.625rem;
  opacity: 0.8;
  margin-top: 0.125rem;
}

.llm-deepseek { background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; }
.llm-gemini { background: linear-gradient(135deg, #4285f4, #34a853); color: white; }
.llm-kimi { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; }
.llm-doubao { background: linear-gradient(135deg, #f97316, #fb923c); color: white; }
.llm-zhipu { background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; }
.llm-minimax { background: linear-gradient(135deg, #ec4899, #f472b6); color: white; }
.llm-openai { background: linear-gradient(135deg, #10b981, #34d399); color: white; }

/* 技术栈卡片 */
.tech-stack-card {
  background: white;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.tech-stack-header {
  padding: 0.75rem 1rem;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tech-stack-list {
  padding: 1rem;
  list-style: none;
  margin: 0;
}

.tech-stack-list li {
  padding: 0.375rem 0;
  font-size: 0.8rem;
  color: #475569;
  border-bottom: 1px solid #f1f5f9;
}

.tech-stack-list li:last-child {
  border-bottom: none;
}

.tech-stack-list li strong {
  color: #1e293b;
}
</style>
