<template>
  <div class="w-full max-w-[680px] bg-white rounded-xl shadow-lg border border-slate-100 overflow-hidden">
    <!-- Zhihu Header -->
    <div class="h-10 px-4 bg-white flex items-center justify-between border-b border-slate-100 select-none">
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 rounded bg-blue-600 flex items-center justify-center">
          <span class="text-white text-[8px] font-black">知</span>
        </div>
        <span class="text-xs font-bold text-slate-700">回答</span>
      </div>
      <div class="flex items-center gap-2 text-slate-400 text-[10px]">
        <Search class="w-3 h-3" />
      </div>
    </div>

    <!-- Question Title -->
    <div class="px-4 pt-4 pb-3 border-b border-slate-100">
      <h2 class="text-base font-extrabold text-blue-700 leading-snug">{{ title || '问题标题生成中...' }}</h2>
      <div class="mt-1 flex items-center gap-2 text-[10px] text-slate-400">
        <span>1,234 关注</span>
        <span>·</span>
        <span>567 回答</span>
      </div>
    </div>

    <!-- Answerer Info -->
    <div class="px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
          <Bot class="w-5 h-5 text-white" />
        </div>
        <div>
          <div class="flex items-center gap-1">
            <span class="text-xs font-bold text-slate-900">知乎财经分析师</span>
            <span class="text-[10px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded font-medium">优秀回答者</span>
          </div>
          <span class="text-[10px] text-slate-400">金融领域答主 · 2.3万 赞同</span>
        </div>
      </div>
      <button class="px-3 py-1 rounded-full text-[10px] font-bold bg-blue-50 border border-blue-200 text-blue-600">
        + 关注
      </button>
    </div>

    <!-- Answer Body (Markdown) -->
    <div class="px-4 pb-3">
      <div v-if="!body" class="space-y-2 py-4">
        <div class="h-2 bg-slate-100 rounded w-full animate-pulse"></div>
        <div class="h-2 bg-slate-100 rounded w-5/6 animate-pulse"></div>
        <div class="h-2 bg-slate-100 rounded w-4/6 animate-pulse"></div>
      </div>
      <div
        v-else
        class="prose prose-sm max-w-none text-slate-700 leading-relaxed zhihu-body"
        v-html="renderedBody"
      ></div>
    </div>

    <!-- Inline Images with Captions -->
    <div v-if="images && images.length" class="px-4 pb-3 space-y-3">
      <div v-for="(img, i) in images" :key="i" class="flex flex-col items-center gap-1">
        <img :src="img" class="max-w-full rounded-lg shadow-sm" :alt="'配图 ' + (i + 1)" loading="lazy" />
        <span class="text-[10px] text-slate-400">图 {{ i + 1 }}</span>
      </div>
    </div>

    <!-- Tags -->
    <div v-if="tags && tags.length" class="px-4 pb-3 flex flex-wrap gap-1">
      <span v-for="(tag, i) in tags" :key="i" class="text-[10px] text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded">
        {{ tag }}
      </span>
    </div>

    <!-- Disclaimer -->
    <div class="mx-4 mb-3 border-t border-slate-100 pt-2">
      <p class="text-[10px] text-slate-400 leading-relaxed">
        ⚠️ 以上内容仅为市场观点讨论，不构成任何投资建议。投资有风险，入市需谨慎。
      </p>
    </div>

    <!-- Bottom Interaction Bar -->
    <div class="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button class="flex items-center gap-1 px-3 py-1.5 bg-blue-500 text-white rounded-full text-[10px] font-bold">
          <ThumbsUp class="w-3 h-3" /> 赞同 328
        </button>
        <button class="flex items-center gap-1 px-2 py-1.5 bg-slate-100 text-slate-500 rounded-full text-[10px]">
          <ThumbsDown class="w-3 h-3" />
        </button>
      </div>
      <div class="flex items-center gap-3 text-slate-400 text-[10px]">
        <span class="flex items-center gap-1"><MessageCircle class="w-3 h-3" /> 评论 45</span>
        <span class="flex items-center gap-1"><Bookmark class="w-3 h-3" /> 收藏</span>
        <span class="flex items-center gap-1"><Share2 class="w-3 h-3" /> 分享</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Search, Bot, ThumbsUp, ThumbsDown, MessageCircle, Bookmark, Share2 } from 'lucide-vue-next'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

const props = defineProps({
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  images: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] }
})

const renderedBody = computed(() => {
  if (!props.body) return ''
  let html = md.render(props.body)
  // Highlight paragraphs containing numbers/percentages with light blue background
  html = html.replace(
    /<p>((?:(?!<\/p>).)*\d+(?:\.\d+)?%(?:(?!<\/p>).)*)<\/p>/g,
    '<p class="bg-blue-50 rounded px-2 py-1 border-l-2 border-blue-300">$1</p>'
  )
  return html
})
</script>

<style scoped>
.zhihu-body :deep(h2) {
  font-size: 0.875rem;
  font-weight: 700;
  color: #1e293b;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
.zhihu-body :deep(h3) {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #334155;
  margin-top: 0.75rem;
  margin-bottom: 0.375rem;
}
.zhihu-body :deep(blockquote) {
  border-left: 3px solid #3b82f6;
  padding-left: 0.75rem;
  color: #64748b;
  font-style: italic;
  margin: 0.5rem 0;
}
.zhihu-body :deep(ul),
.zhihu-body :deep(ol) {
  padding-left: 1.25rem;
  margin: 0.5rem 0;
}
.zhihu-body :deep(li) {
  margin-bottom: 0.25rem;
}
.zhihu-body :deep(strong) {
  color: #0f172a;
}
.zhihu-body :deep(code) {
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #475569;
}
.zhihu-body :deep(pre) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.75rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}
</style>
