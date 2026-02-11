<template>
  <div class="glass-card p-6 rounded-xl shadow-lg flex justify-center bg-slate-100/50">
    <div
      class="phone-preview rounded-[3rem] overflow-hidden shadow-2xl bg-white w-full max-w-[320px] h-[680px] flex flex-col transform transition hover:scale-[1.02] duration-300"
      style="border: 8px solid #000000; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);"
    >
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

      <!-- Weibo App Header -->
      <div class="h-11 px-4 bg-white flex items-center justify-between border-b border-slate-100 flex-shrink-0 select-none">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded bg-red-500 flex items-center justify-center">
            <span class="text-white text-[10px] font-black">微</span>
          </div>
          <span class="text-sm font-bold text-slate-900">首页</span>
        </div>
        <Search class="w-4 h-4 text-slate-400" />
      </div>

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar bg-slate-50">
        <div class="bg-white m-2 rounded-xl p-3 shadow-sm">
          <!-- User Info -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <div class="w-9 h-9 rounded-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center flex-shrink-0">
                <Bot class="w-5 h-5 text-white" />
              </div>
              <div>
                <div class="flex items-center gap-1">
                  <span class="text-xs font-bold text-slate-900">财经观察员</span>
                  <span class="w-3.5 h-3.5 rounded-full bg-orange-500 text-white text-[8px] font-bold flex items-center justify-center">V</span>
                </div>
                <span class="text-[10px] text-slate-400">刚刚</span>
              </div>
            </div>
            <button class="px-3 py-1 rounded-full text-[10px] font-bold border border-red-400 text-red-500">
              + 关注
            </button>
          </div>

          <!-- Body Text -->
          <div class="text-xs text-slate-800 leading-relaxed mb-2 whitespace-pre-line">{{ body || '正文生成中...' }}</div>

          <!-- Character count warning -->
          <div v-if="body && body.length > 140" class="text-[10px] text-red-500 font-medium mb-2">
            已超出 140 字限制（当前 {{ body.length }} 字）
          </div>

          <!-- Tags -->
          <div v-if="tags && tags.length" class="flex flex-wrap gap-1 mb-3">
            <span v-for="(tag, i) in tags" :key="i" class="text-[10px] text-blue-500 font-medium">
              #{{ tag }}#
            </span>
          </div>

          <!-- Image Grid -->
          <div v-if="images && images.length" :class="imageGridClass" class="gap-1 mb-3">
            <div
              v-for="(img, i) in images.slice(0, 9)"
              :key="i"
              :class="imageItemClass(i)"
              class="bg-slate-100 rounded overflow-hidden"
            >
              <img :src="img" class="w-full h-full object-cover" :alt="'配图 ' + (i + 1)" loading="lazy" />
            </div>
          </div>

          <!-- Bottom Interaction Bar -->
          <div class="flex items-center justify-around pt-2 border-t border-slate-100 text-slate-400 text-[10px]">
            <span class="flex items-center gap-1"><Repeat2 class="w-3 h-3" /> 转发 12</span>
            <span class="flex items-center gap-1"><MessageCircle class="w-3 h-3" /> 评论 28</span>
            <span class="flex items-center gap-1"><ThumbsUp class="w-3 h-3" /> 点赞 156</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Wifi, Search, Bot, Repeat2, MessageCircle, ThumbsUp } from 'lucide-vue-next'

const props = defineProps({
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  images: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] }
})

const imageCount = computed(() => Math.min((props.images || []).length, 9))

const imageGridClass = computed(() => {
  const n = imageCount.value
  if (n === 0) return 'hidden'
  if (n === 1) return 'grid grid-cols-1'
  if (n <= 3) return 'grid grid-cols-3'
  if (n === 4) return 'grid grid-cols-2'
  return 'grid grid-cols-3'
})

const imageItemClass = (index) => {
  const n = imageCount.value
  if (n === 1) return 'aspect-[4/3]'
  if (n === 4) return 'aspect-square'
  return 'aspect-square'
}
</script>
