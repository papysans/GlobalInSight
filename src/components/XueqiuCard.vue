<template>
  <div class="w-full max-w-[680px] bg-white rounded-xl shadow-lg border border-slate-100 overflow-hidden">
    <!-- Xueqiu Header -->
    <div class="h-10 px-4 bg-gradient-to-r from-blue-600 to-blue-700 flex items-center justify-between select-none">
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 rounded bg-white flex items-center justify-center">
          <span class="text-blue-600 text-[8px] font-black">雪</span>
        </div>
        <span class="text-xs font-bold text-white">长文</span>
      </div>
      <div class="flex items-center gap-2 text-white/70 text-[10px]">
        <Search class="w-3 h-3" />
      </div>
    </div>

    <!-- User Info -->
    <div class="px-4 py-3 flex items-center justify-between border-b border-slate-100">
      <div class="flex items-center gap-2">
        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
          <Bot class="w-5 h-5 text-white" />
        </div>
        <div>
          <div class="flex items-center gap-1">
            <span class="text-xs font-bold text-slate-900">雪球财经观察</span>
            <span class="w-3.5 h-3.5 rounded-full bg-blue-500 text-white text-[8px] font-bold flex items-center justify-center">V</span>
          </div>
          <span class="text-[10px] text-slate-400">刚刚发布</span>
        </div>
      </div>
      <button class="px-3 py-1 rounded-full text-[10px] font-bold border border-blue-400 text-blue-500">
        + 关注
      </button>
    </div>

    <!-- Article Title -->
    <div class="px-4 pt-4 pb-2">
      <h2 class="text-base font-extrabold text-slate-900 leading-snug">{{ title || '标题生成中...' }}</h2>
    </div>

    <!-- Article Body (Markdown) -->
    <div class="px-4 pb-3">
      <div v-if="!body" class="space-y-2 py-4">
        <div class="h-2 bg-slate-100 rounded w-full animate-pulse"></div>
        <div class="h-2 bg-slate-100 rounded w-5/6 animate-pulse"></div>
        <div class="h-2 bg-slate-100 rounded w-4/6 animate-pulse"></div>
      </div>
      <div
        v-else
        class="prose prose-sm max-w-none text-slate-700 leading-relaxed xueqiu-body"
        v-html="renderedBody"
      ></div>
    </div>

    <!-- Inline Images -->
    <div v-if="images && images.length" class="px-4 pb-3 space-y-3">
      <div v-for="(img, i) in images" :key="i" class="flex justify-center">
        <img :src="img" class="max-w-full rounded-lg shadow-sm" :alt="'配图 ' + (i + 1)" loading="lazy" />
      </div>
    </div>

    <!-- Tags -->
    <div v-if="tags && tags.length" class="px-4 pb-3 flex flex-wrap gap-1">
      <span v-for="(tag, i) in tags" :key="i" class="text-[10px] text-blue-500 font-medium bg-blue-50 px-2 py-0.5 rounded-full">
        ${{ tag }}
      </span>
    </div>

    <!-- Disclaimer -->
    <div class="mx-4 mb-3 p-2 bg-slate-50 rounded-lg border border-slate-100">
      <p class="text-[10px] text-slate-400 leading-relaxed">
        ⚠️ 以上内容仅为市场观点讨论，不构成任何投资建议。投资有风险，入市需谨慎。
      </p>
    </div>

    <!-- Bottom Interaction Bar -->
    <div class="px-4 py-3 border-t border-slate-100 flex items-center justify-around text-slate-400 text-[10px]">
      <span class="flex items-center gap-1"><ThumbsUp class="w-3 h-3" /> 赞同 89</span>
      <span class="flex items-center gap-1"><MessageCircle class="w-3 h-3" /> 评论 34</span>
      <span class="flex items-center gap-1"><Repeat2 class="w-3 h-3" /> 转发 21</span>
      <span class="flex items-center gap-1"><Bookmark class="w-3 h-3" /> 收藏 56</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Search, Bot, ThumbsUp, MessageCircle, Repeat2, Bookmark } from 'lucide-vue-next'
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
.xueqiu-body :deep(h2) {
  font-size: 0.875rem;
  font-weight: 700;
  color: #1e293b;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
.xueqiu-body :deep(h3) {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #334155;
  margin-top: 0.75rem;
  margin-bottom: 0.375rem;
}
.xueqiu-body :deep(blockquote) {
  border-left: 3px solid #3b82f6;
  padding-left: 0.75rem;
  color: #64748b;
  font-style: italic;
  margin: 0.5rem 0;
}
.xueqiu-body :deep(ul),
.xueqiu-body :deep(ol) {
  padding-left: 1.25rem;
  margin: 0.5rem 0;
}
.xueqiu-body :deep(li) {
  margin-bottom: 0.25rem;
}
.xueqiu-body :deep(strong) {
  color: #0f172a;
}
</style>
