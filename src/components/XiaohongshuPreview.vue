<template>
  <div class="glass-card p-6 rounded-xl shadow-lg flex justify-center bg-slate-100/50">
    <div
      class="phone-preview rounded-[3rem] overflow-hidden shadow-2xl bg-white w-full max-w-[320px] h-[680px] flex flex-col transform transition hover:scale-[1.02] duration-300"
      style="border: 8px solid #000000; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);"
    >
      <!-- Status Bar -->
      <div class="relative bg-white px-5 h-10 flex items-center justify-between z-10 flex-shrink-0 select-none">
        <span class="text-[10px] font-bold text-slate-900 w-8">09:41</span>
        <div
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-6 bg-black rounded-full flex justify-center items-center"
        >
          <div class="w-1.5 h-1.5 bg-gray-800 rounded-full absolute right-4"></div>
        </div>
        <div class="w-8 flex justify-end">
          <Wifi class="w-3 h-3 text-slate-900" />
        </div>
      </div>

      <!-- App Header (XHS-like) -->
      <div
        class="h-12 px-4 bg-white flex items-center justify-between border-b border-slate-100 flex-shrink-0 select-none"
      >
        <div class="flex items-center gap-2 min-w-0">
          <ChevronLeft class="w-5 h-5 text-slate-900" />
          <div
            class="w-7 h-7 rounded-full bg-slate-200 overflow-hidden flex items-center justify-center flex-shrink-0"
          >
            <Bot class="w-4 h-4 text-slate-500" />
          </div>
          <div class="min-w-0">
            <div class="text-xs font-bold text-slate-900 truncate">{{ title ? 'Napstablook' : '预览' }}</div>
            <div class="text-[10px] text-slate-400 truncate">已关注</div>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button class="px-3 py-1 rounded-full text-[10px] font-bold border border-slate-200 text-slate-700 bg-white">
            已关注
          </button>
          <Share2 class="w-4 h-4 text-slate-700" />
        </div>
      </div>

      <!-- Screen Content -->
      <div class="relative cursor-pointer group flex-1 flex flex-col overflow-hidden bg-white" @click="switchImage">
        <!-- Scrollable content -->
        <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
          <!-- Image area: 3:4 aspect ratio -->
          <div class="relative overflow-hidden flex-shrink-0 transition-colors duration-500 aspect-[3/4] bg-slate-100">
            <div
              class="relative w-full h-full"
              style="touch-action: pan-y;"
              @pointerdown="onPointerDown"
              @pointermove="onPointerMove"
              @pointerup="onPointerUp"
              @pointercancel="onPointerUp"
            >
              <transition name="image-fade" mode="out-in">
                <!-- Title Card (index 0) -->
                <XiaohongshuCard
                  v-if="displayImages[currentIndex] === null"
                  key="title-card"
                  :title="title"
                  :emoji="titleEmoji"
                  :theme="titleTheme"
                  emoji-pos="bottom-right"
                  class="absolute inset-0"
                />
                <!-- AI Images -->
                <img
                  v-else
                  :key="'img-' + currentIndex"
                  :src="displayImages[currentIndex]"
                  class="absolute inset-0 w-full h-full object-cover block"
                  alt="AI Generated"
                  draggable="false"
                  loading="lazy"
                  decoding="async"
                />
              </transition>

              <!-- AI badge -->
              <div
                v-if="displayImages[currentIndex] !== null"
                class="absolute top-2 left-2 flex items-center gap-1 bg-white/80 text-slate-700 text-[10px] px-2 py-1 rounded-full backdrop-blur-sm border border-slate-100"
              >
                <AlertTriangle class="w-3 h-3 text-slate-700" />
                <span>内容可能使用AI技术生成</span>
              </div>

              <!-- Dot indicators -->
              <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5 z-20">
                <div
                  v-for="(_, i) in displayImages"
                  :key="i"
                  :class="[
                    'w-1.5 h-1.5 rounded-full transition-all duration-300',
                    currentIndex === i ? 'bg-white scale-125' : 'bg-white/50'
                  ]"
                ></div>
              </div>

              <div
                class="absolute bottom-2 right-2 bg-black/50 text-white text-[10px] px-2 py-1 rounded-full backdrop-blur-sm"
              >
                {{ currentIndex + 1 }} / {{ displayImages.length }}
              </div>
            </div>
          </div>

          <!-- Text area -->
          <div class="p-4 flex-1 flex flex-col">
            <h4 class="font-bold text-sm text-slate-900 mb-2">
              {{ title || '标题生成中...' }}
            </h4>
            <div class="text-xs text-slate-600 space-y-2 flex-1">
              <div v-if="!body" class="space-y-2">
                <div class="h-2 bg-slate-100 rounded w-full animate-pulse"></div>
                <div class="h-2 bg-slate-100 rounded w-5/6 animate-pulse"></div>
                <div class="h-2 bg-slate-100 rounded w-4/6 animate-pulse"></div>
              </div>
              <div v-else class="prose prose-xs max-w-none" v-html="renderedBody"></div>
            </div>
            <!-- Tags -->
            <div v-if="tags && tags.length" class="mt-3 flex flex-wrap gap-1">
              <span
                v-for="(tag, i) in tags"
                :key="i"
                class="text-[10px] text-blue-500 font-medium"
              >
                #{{ tag }}
              </span>
            </div>
          </div>
        </div>

        <!-- Bottom interaction bar (fixed) -->
        <div
          class="px-4 py-3 border-t border-slate-100 flex items-center justify-between text-slate-500 text-[10px] bg-white z-10 flex-shrink-0"
        >
          <div class="flex-1 mr-3">
            <div class="w-full rounded-full bg-slate-100 text-slate-400 px-3 py-2 text-[10px] border border-slate-100">
              说点什么...
            </div>
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
</template>

<script setup>
import { ref, computed } from 'vue'
import { Wifi, ChevronLeft, Bot, Share2, AlertTriangle, Heart, Star, MessageCircle } from 'lucide-vue-next'
import XiaohongshuCard from './XiaohongshuCard.vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

const props = defineProps({
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  images: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] },
  titleEmoji: { type: String, default: '🤔' },
  titleTheme: { type: String, default: 'cool' }
})

const currentIndex = ref(0)

// Title card (null) + AI images
const displayImages = computed(() => {
  return [null, ...(props.images || [])]
})

const renderedBody = computed(() => {
  return props.body ? md.render(props.body) : ''
})

// Swipe support
let pointerStartX = 0
let pointerStartY = 0

const onPointerDown = (e) => {
  pointerStartX = e.clientX
  pointerStartY = e.clientY
}

const onPointerMove = () => {}

const onPointerUp = (e) => {
  const dx = e.clientX - pointerStartX
  const dy = e.clientY - pointerStartY
  if (Math.abs(dx) > 30 && Math.abs(dx) > Math.abs(dy)) {
    if (dx < 0 && currentIndex.value < displayImages.value.length - 1) {
      currentIndex.value++
    } else if (dx > 0 && currentIndex.value > 0) {
      currentIndex.value--
    }
  }
}

const switchImage = () => {
  if (displayImages.value.length > 1) {
    currentIndex.value = (currentIndex.value + 1) % displayImages.value.length
  }
}
</script>

<style scoped>
.image-fade-enter-active,
.image-fade-leave-active {
  transition: opacity 0.3s ease;
}
.image-fade-enter-from,
.image-fade-leave-to {
  opacity: 0;
}
</style>
