<template>
  <transition name="edit-panel">
    <div v-if="isEditing" class="mt-4 glass-card rounded-xl p-6 border-2 border-blue-200">
      <!-- 标题编辑 -->
      <div class="mb-6">
        <label class="flex items-center gap-2 text-sm font-bold text-slate-700 mb-2">
          <PenTool class="w-4 h-4 text-blue-600" />
          编辑标题 (最多20字)
        </label>
        <input
          v-model="localTitle"
          type="text"
          maxlength="20"
          :class="[
            'w-full px-4 py-3 rounded-lg text-sm transition-colors',
            'border-2 focus:outline-none',
            titleError ? 'border-red-500 bg-red-50' : 'border-blue-300 bg-white focus:border-blue-500'
          ]"
          placeholder="输入标题..."
          @input="onTitleInput"
        />
        <div class="mt-1 flex items-center justify-between text-xs">
          <span v-if="titleError" class="text-red-600 flex items-center gap-1">
            <AlertTriangle class="w-3 h-3" /> {{ titleError }}
          </span>
          <span v-else class="text-slate-500">小红书标题建议简短有力</span>
          <span :class="titleCharsLeft >= 0 ? 'text-green-600' : 'text-red-600'" class="font-mono">
            {{ titleCharsLeft >= 0 ? `剩余: ${titleCharsLeft}字 ✓` : `超出: ${Math.abs(titleCharsLeft)}字 ⚠️` }}
          </span>
        </div>
      </div>

      <!-- 正文编辑 -->
      <div class="mb-6">
        <label class="flex items-center gap-2 text-sm font-bold text-slate-700 mb-2">
          <FileText class="w-4 h-4 text-blue-600" />
          编辑正文 (最多1000字)
        </label>
        <textarea
          v-model="localBody"
          rows="8"
          maxlength="1000"
          :class="[
            'w-full px-4 py-3 rounded-lg text-sm transition-colors resize-none',
            'border-2 focus:outline-none',
            bodyError ? 'border-red-500 bg-red-50' : 'border-blue-300 bg-white focus:border-blue-500'
          ]"
          placeholder="输入正文内容...&#10;&#10;提示：话题格式为 #话题名称（无空格）"
          @input="onBodyInput"
        ></textarea>
        <div class="mt-1 flex items-center justify-between text-xs">
          <div class="flex items-center gap-3">
            <span :class="bodyCharsLeft >= 0 ? 'text-green-600' : 'text-red-600'" class="font-mono">
              {{ bodyCharsLeft >= 0 ? `剩余: ${bodyCharsLeft}字 ✓` : `超出: ${Math.abs(bodyCharsLeft)}字 ⚠️` }}
            </span>
            <span :class="topicCount <= 10 ? 'text-green-600' : 'text-orange-600'" class="font-mono">
              话题: {{ topicCount }}/10 {{ topicCount <= 10 ? '✓' : '⚠️' }}
            </span>
          </div>
          <span v-if="topicFormatError" class="text-orange-600 flex items-center gap-1">
            <AlertTriangle class="w-3 h-3" /> {{ topicFormatError }}
          </span>
        </div>
      </div>

      <!-- 图片选择和排序 -->
      <div class="mb-6">
        <label class="flex items-center gap-2 text-sm font-bold text-slate-700 mb-2">
          <Image class="w-4 h-4 text-blue-600" />
          选择和排序图片 (1-9张)
        </label>
        
        <!-- 使用 VueDraggable 实现拖拽排序 - 只显示已选中的图片 -->
        <VueDraggable
          v-model="sortedImages"
          :animation="200"
          class="grid grid-cols-4 gap-3 mb-3"
          @end="onDragEnd"
        >
          <div
            v-for="img in sortedImages"
            :key="img.originalIndex"
            class="relative aspect-square rounded-lg overflow-hidden cursor-move border-2 border-blue-500 shadow-md group"
          >
            <!-- 拖拽手柄（hover显示） -->
            <div class="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/20 transition-colors flex items-center justify-center z-10">
              <div class="w-10 h-10 bg-blue-500/80 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
                </svg>
              </div>
            </div>
            
            <!-- 图片内容 -->
            <img
              v-if="img.type === 'ai' || img.type === 'title-image' || img.type === 'dataview'"
              :src="img.url"
              :alt="img.label"
              class="w-full h-full object-cover"
            />
            <div
              v-else-if="img.type === 'title'"
              class="w-full h-full"
            >
              <XiaohongshuCard
                :title="localTitle || '标题'"
                :emoji="titleEmoji"
                :theme="titleTheme"
                :mini="true"
              />
            </div>
            
            <!-- 删除按钮 -->
            <button
              v-if="selectedCount > 1"
              @click.stop="toggleImageSelection(img.originalIndex)"
              class="absolute top-1 left-1 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600 z-20"
              title="取消选择"
            >
              <X class="w-4 h-4" />
            </button>
            
            <!-- 序号 -->
            <div class="absolute top-1 right-1 w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
              {{ sortedImages.indexOf(img) + 1 }}
            </div>
            
            <!-- 标签 -->
            <div class="absolute bottom-1 left-1 right-1 text-center">
              <span class="text-[10px] bg-black/60 text-white px-2 py-0.5 rounded-full">
                {{ img.label }}
              </span>
            </div>
          </div>
        </VueDraggable>
        
        <!-- 未选中的图片（可点击添加） -->
        <div v-if="unselectedImages.length > 0" class="mt-3 p-3 bg-slate-50 rounded-lg">
          <div class="text-xs text-slate-600 mb-2 flex items-center gap-1">
            <Info class="w-3 h-3" />
            点击添加更多图片
          </div>
          <div class="grid grid-cols-4 gap-3">
            <div
              v-for="img in unselectedImages"
              :key="img.originalIndex"
              class="relative aspect-square rounded-lg overflow-hidden cursor-pointer border-2 border-dashed border-slate-300 hover:border-blue-400 transition-all opacity-60 hover:opacity-100"
              @click="toggleImageSelection(img.originalIndex)"
            >
              <!-- 图片内容 -->
              <img
                v-if="img.type === 'ai' || img.type === 'title-image' || img.type === 'dataview'"
                :src="img.url"
                :alt="img.label"
                class="w-full h-full object-cover"
              />
              <div
                v-else-if="img.type === 'title'"
                class="w-full h-full"
              >
                <XiaohongshuCard
                  :title="localTitle || '标题'"
                  :emoji="titleEmoji"
                  :theme="titleTheme"
                  :mini="true"
                />
              </div>
              
              <!-- 添加图标 -->
              <div class="absolute inset-0 bg-slate-900/30 flex items-center justify-center">
                <div class="w-8 h-8 rounded-full bg-white/90 flex items-center justify-center">
                  <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                </div>
              </div>
              
              <!-- 标签 -->
              <div class="absolute bottom-1 left-1 right-1 text-center">
                <span class="text-[10px] bg-black/60 text-white px-2 py-0.5 rounded-full">
                  {{ img.label }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="mt-2 flex items-center justify-between text-xs">
          <span class="text-slate-500 flex items-center gap-1">
            <Info class="w-3 h-3" />
            拖拽调整顺序，第一张为封面
          </span>
          <span :class="selectedCount >= 1 && selectedCount <= 9 ? 'text-green-600' : 'text-red-600'" class="font-mono">
            已选择: {{ selectedCount }}/9 {{ selectedCount >= 1 && selectedCount <= 9 ? '✓' : '⚠️' }}
          </span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center gap-3">
        <button
          @click="handleSave"
          :disabled="!canSave"
          class="flex-1 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-bold shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Check class="w-4 h-4" />
          完成编辑
        </button>
        <button
          @click="handleCancel"
          class="px-4 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-sm font-bold shadow-sm transition-colors flex items-center justify-center gap-2"
        >
          <X class="w-4 h-4" />
          取消
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAnalysisStore } from '../stores/analysis'
import { storeToRefs } from 'pinia'
import { PenTool, FileText, Image, Check, X, AlertTriangle, Info } from 'lucide-vue-next'
import { useDebounceFn } from '@vueuse/core'
import { VueDraggable } from 'vue-draggable-plus'
import XiaohongshuCard from './XiaohongshuCard.vue'

const analysisStore = useAnalysisStore()
const { isEditing, editableContent, imageUrls, titleEmoji, titleTheme } = storeToRefs(analysisStore)

// 本地编辑状态
const localTitle = ref('')
const localBody = ref('')
const localSelectedIndices = ref([])
const localImageOrder = ref([])

// 初始化本地状态
watch(isEditing, (newVal) => {
  if (newVal) {
    localTitle.value = editableContent.value.title
    localBody.value = editableContent.value.body
    
    // 计算当前实际的图片总数
    const dataViewCount = analysisStore.dataViewImages?.length || 0
    const aiImageCount = imageUrls.value?.length || 0
    const totalImages = 1 + dataViewCount + aiImageCount // Title Card + DataView + AI
    
    // 验证并过滤 selectedImageIndices，确保索引在有效范围内
    const rawSelectedIndices = editableContent.value.selectedImageIndices || []
    const validSelectedIndices = rawSelectedIndices.filter(idx => idx >= 0 && idx < totalImages)
    
    // 验证并过滤 imageOrder，确保索引在有效范围内
    const rawImageOrder = editableContent.value.imageOrder || []
    const validImageOrder = rawImageOrder.filter(idx => idx >= 0 && idx < totalImages)
    
    // 如果过滤后为空，使用默认值（全选所有图片）
    if (validSelectedIndices.length === 0) {
      localSelectedIndices.value = Array.from({ length: totalImages }, (_, i) => i)
    } else {
      localSelectedIndices.value = validSelectedIndices
    }
    
    if (validImageOrder.length === 0) {
      localImageOrder.value = Array.from({ length: totalImages }, (_, i) => i)
    } else {
      localImageOrder.value = validImageOrder
    }
    
    console.log('[CopywritingEditor] 编辑模式已启动:', {
      title: localTitle.value,
      bodyLength: localBody.value?.length,
      totalImages,
      dataViewCount,
      aiImageCount,
      rawSelectedIndices,
      validSelectedIndices: localSelectedIndices.value,
      rawImageOrder,
      validImageOrder: localImageOrder.value
    })
  }
}, { immediate: true })

// 所有图片（可能包含Title Card图片 + AI图片，或者只有AI图片）
const allImages = computed(() => {
  const images = []
  
  // 1. Title Card（始终在第一位）
  images.push({ type: 'title', label: '标题卡', url: null, originalIndex: 0 })
  
  // 2. DataView 卡片（如果有）
  const dataViewImages = analysisStore.dataViewImages || []
  dataViewImages.forEach((url, i) => {
    const labels = ['平台覆盖', '辩论演化', '热度趋势']
    images.push({ 
      type: 'dataview', 
      label: labels[i] || `数据卡片 ${i + 1}`, 
      url, 
      originalIndex: i + 1 
    })
  })
  
  // 3. AI 生图
  imageUrls.value.forEach((url, i) => {
    images.push({ 
      type: 'ai', 
      label: `AI配图 ${i + 1}`, 
      url, 
      originalIndex: dataViewImages.length + i + 1 
    })
  })
  
  console.log('[CopywritingEditor] allImages computed:', {
    totalCount: images.length,
    dataViewCount: dataViewImages.length,
    aiImageCount: imageUrls.value.length,
    firstImage: images[0],
    restImages: images.slice(1).map(img => ({ label: img.label, type: img.type }))
  })
  return images
})

// 排序后的图片（用于拖拽）
const sortedImages = computed({
  get() {
    // 过滤掉无效索引（超出 allImages 范围的索引）
    const validOrder = localImageOrder.value.filter(idx => idx >= 0 && idx < allImages.value.length)
    const result = validOrder.map(idx => allImages.value[idx]).filter(img => img !== undefined)
    console.log('[CopywritingEditor] sortedImages get:', {
      localImageOrder: localImageOrder.value,
      validOrder,
      allImagesCount: allImages.value.length,
      resultCount: result.length,
      result: result.map(img => ({ type: img?.type, label: img?.label, index: img?.originalIndex }))
    })
    return result
  },
  set(newOrder) {
    localImageOrder.value = newOrder.map(img => img.originalIndex)
    console.log('[CopywritingEditor] sortedImages set:', {
      newOrder: newOrder.map(img => ({ type: img.type, index: img.originalIndex })),
      localImageOrder: localImageOrder.value
    })
    // 直接更新 store
    analysisStore.updateEditableContent('imageOrder', localImageOrder.value)
  }
})

// 未选中的图片
const unselectedImages = computed(() => {
  const result = allImages.value.filter(img => !isImageSelected(img.originalIndex))
  console.log('[CopywritingEditor] 📋 未选中图片:', {
    allImagesCount: allImages.value.length,
    selectedCount: localSelectedIndices.value.length,
    unselectedCount: result.length,
    unselected: result.map(img => ({ type: img.type, label: img.label, index: img.originalIndex }))
  })
  return result
})

// 字符计数
const titleCharsLeft = computed(() => 20 - (localTitle.value?.length || 0))
const bodyCharsLeft = computed(() => 1000 - (localBody.value?.length || 0))

// 话题计数和验证
const topicCount = computed(() => {
  const matches = (localBody.value || '').match(/#[^\s#]+/g)
  return matches ? matches.length : 0
})

const topicFormatError = computed(() => {
  const text = localBody.value || ''
  // 检查是否有 "# " 格式（井号后有空格）
  if (text.includes('# ')) {
    return '话题格式错误：#话题名称（无空格）'
  }
  return null
})

// 错误状态
const titleError = computed(() => {
  if (titleCharsLeft.value < 0) return '标题超出限制'
  if (!localTitle.value?.trim()) return '标题不能为空'
  return null
})

const bodyError = computed(() => {
  if (bodyCharsLeft.value < 0) return '正文超出限制'
  return null
})

// 选中图片数量
const selectedCount = computed(() => localSelectedIndices.value.length)

// 是否可以保存
const canSave = computed(() => {
  return !titleError.value &&
    !bodyError.value &&
    !topicFormatError.value &&
    topicCount.value <= 10 &&
    selectedCount.value >= 1 &&
    selectedCount.value <= 9
})

// 输入处理（带防抖）
const updateStore = useDebounceFn(() => {
  analysisStore.updateEditableContent('title', localTitle.value)
  analysisStore.updateEditableContent('body', localBody.value)
}, 300)

const onTitleInput = () => {
  updateStore()
}

const onBodyInput = () => {
  updateStore()
}

// 图片选择
const isImageSelected = (index) => {
  return localSelectedIndices.value.includes(index)
}

const toggleImageSelection = (index) => {
  console.log('[CopywritingEditor] 🖱️ 点击图片:', { index, currentSelected: localSelectedIndices.value })
  
  const idx = localSelectedIndices.value.indexOf(index)
  if (idx > -1) {
    // 取消选择
    if (localSelectedIndices.value.length > 1) { // 至少保留1张
      localSelectedIndices.value.splice(idx, 1)
      // 同时从排序中移除
      const orderIdx = localImageOrder.value.indexOf(index)
      if (orderIdx > -1) {
        localImageOrder.value.splice(orderIdx, 1)
      }
      console.log('[CopywritingEditor] ❌ 取消选择图片:', { index, remainingSelected: localSelectedIndices.value, remainingOrder: localImageOrder.value })
    } else {
      console.log('[CopywritingEditor] ⚠️ 至少保留1张图片，无法取消')
    }
  } else {
    // 选择
    if (localSelectedIndices.value.length < 9) { // 最多9张
      localSelectedIndices.value.push(index)
      localImageOrder.value.push(index)
      console.log('[CopywritingEditor] ✅ 添加图片:', { index, newSelected: localSelectedIndices.value, newOrder: localImageOrder.value })
    } else {
      console.log('[CopywritingEditor] ⚠️ 最多选择9张图片')
    }
  }
  analysisStore.updateEditableContent('selectedImageIndices', localSelectedIndices.value)
  analysisStore.updateEditableContent('imageOrder', localImageOrder.value)
  console.log('[CopywritingEditor] 📤 已同步到 store')
}

const getImageOrder = (index) => {
  return localImageOrder.value.indexOf(index)
}

// 拖拽结束处理（VueDraggable）
const onDragEnd = () => {
  // sortedImages 的 setter 已经更新了 localImageOrder
  // 这里只需要同步到 store
  console.log('[CopywritingEditor] 🔄 拖拽结束:', {
    newOrder: localImageOrder.value,
    sortedImages: sortedImages.value.map(img => ({ type: img.type, label: img.label, index: img.originalIndex }))
  })
  analysisStore.updateEditableContent('imageOrder', localImageOrder.value)
  console.log('[CopywritingEditor] ✅ 已同步到 store')
}

// 保存和取消
const handleSave = () => {
  if (!canSave.value) return
  analysisStore.saveEditing()
}

const handleCancel = () => {
  if (confirm('确定要取消编辑吗？未保存的更改将丢失。')) {
    analysisStore.cancelEditing()
  }
}
</script>

<style scoped>
.edit-panel-enter-active,
.edit-panel-leave-active {
  transition: all 0.3s ease-out;
}

.edit-panel-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.edit-panel-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* === 深色模式样式 === */

/* 编辑面板容器 */
:global(html.dark) .glass-card.border-blue-200 {
  background: #1e293b;
  border-color: rgba(59, 130, 246, 0.4);
}

/* 标签文字 */
:global(html.dark) .text-slate-700 {
  color: #cbd5e1;
}

/* 输入框 */
:global(html.dark) input.border-blue-300,
:global(html.dark) textarea.border-blue-300 {
  background: #0f172a;
  border-color: rgba(59, 130, 246, 0.4);
  color: #e2e8f0;
}

:global(html.dark) input.border-blue-300:focus,
:global(html.dark) textarea.border-blue-300:focus {
  border-color: #3b82f6;
}

:global(html.dark) input::placeholder,
:global(html.dark) textarea::placeholder {
  color: #64748b;
}

/* 错误状态输入框 */
:global(html.dark) input.border-red-500.bg-red-50,
:global(html.dark) textarea.border-red-500.bg-red-50 {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
}

/* 提示文字 */
:global(html.dark) .text-slate-500 {
  color: #64748b;
}

/* 未选中图片区域 */
:global(html.dark) .bg-slate-50 {
  background: rgba(51, 65, 85, 0.3);
}

/* 取消按钮 */
:global(html.dark) .bg-slate-200 {
  background: #334155;
}

:global(html.dark) .bg-slate-200:hover {
  background: #475569;
}

:global(html.dark) .bg-slate-200.text-slate-700 {
  color: #e2e8f0;
}
</style>
