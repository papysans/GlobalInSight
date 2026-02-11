<template>
  <div class="platform-preview">
    <!-- Platform Tab Bar -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">平台预览</span>
      <button
        v-for="p in platforms"
        :key="p.id"
        @click="$emit('update:selectedPlatform', p.id)"
        :class="[
          'px-3 py-1 rounded-full border text-xs font-semibold transition',
          selectedPlatform === p.id
            ? 'bg-blue-50 border-blue-300 text-blue-600'
            : 'border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600'
        ]"
      >
        {{ p.name }}
      </button>
    </div>

    <!-- Preview Area -->
    <div class="flex justify-center">
      <XiaohongshuPreview
        v-if="selectedPlatform === 'xhs'"
        :title="currentContent.title"
        :body="currentContent.body"
        :images="currentContent.images"
        :tags="currentContent.tags"
        :title-emoji="currentContent.titleEmoji || '🤔'"
        :title-theme="currentContent.titleTheme || 'cool'"
      />
      <WeiboCard
        v-else-if="selectedPlatform === 'weibo'"
        :title="currentContent.title"
        :body="currentContent.body"
        :images="currentContent.images"
        :tags="currentContent.tags"
      />
      <XueqiuCard
        v-else-if="selectedPlatform === 'xueqiu'"
        :title="currentContent.title"
        :body="currentContent.body"
        :images="currentContent.images"
        :tags="currentContent.tags"
      />
      <ZhihuCard
        v-else-if="selectedPlatform === 'zhihu'"
        :title="currentContent.title"
        :body="currentContent.body"
        :images="currentContent.images"
        :tags="currentContent.tags"
      />
    </div>

    <!-- Action Bar -->
    <div class="mt-4 flex items-center justify-between px-1">
      <button
        @click="$emit('startEditing')"
        :disabled="!currentContent.body"
        class="px-3 py-1.5 bg-blue-600 border border-blue-600 hover:bg-blue-700 text-white rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Edit class="w-3 h-3" />
        编辑
      </button>
      <button
        @click="copyFullText"
        :disabled="!currentContent.body"
        class="px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded text-xs font-bold shadow-sm transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Copy class="w-3 h-3" />
        {{ copySuccess ? '已复制' : '复制全文' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Edit, Copy } from 'lucide-vue-next'
import XiaohongshuPreview from './XiaohongshuPreview.vue'
import WeiboCard from './WeiboCard.vue'
import XueqiuCard from './XueqiuCard.vue'
import ZhihuCard from './ZhihuCard.vue'

const props = defineProps({
  platformContents: {
    type: Object,
    default: () => ({})
  },
  selectedPlatform: {
    type: String,
    default: 'xhs'
  },
  isEditing: {
    type: Boolean,
    default: false
  },
  editableContent: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['update:selectedPlatform', 'startEditing', 'updateContent'])

const platforms = [
  { id: 'xhs', name: '小红书' },
  { id: 'weibo', name: '微博' },
  { id: 'xueqiu', name: '雪球' },
  { id: 'zhihu', name: '知乎' }
]

const copySuccess = ref(false)

const currentContent = computed(() => {
  return props.platformContents[props.selectedPlatform] || { title: '', body: '', images: [], tags: [] }
})

const copyFullText = async () => {
  const content = currentContent.value
  const text = [content.title, content.body].filter(Boolean).join('\n\n')
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch (e) {
    console.warn('Copy failed', e)
  }
}
</script>
