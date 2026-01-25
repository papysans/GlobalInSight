<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="max-w-7xl mx-auto">
      <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 class="text-3xl font-bold text-gray-900 mb-4">📝 文案编辑功能测试</h1>
        <p class="text-gray-600 mb-4">
          这是一个独立的测试页面，用于测试文案编辑功能。点击下方按钮加载测试数据。
        </p>
        
        <div class="flex gap-4 mb-6">
          <button
            @click="loadTestData"
            class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
          >
            🚀 加载测试数据
          </button>
          
          <button
            @click="clearData"
            class="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
          >
            🗑️ 清空数据
          </button>
        </div>

        <div v-if="dataLoaded" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <p class="text-green-800 font-medium">✅ 测试数据已加载！现在可以测试编辑功能了。</p>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 左侧：文案编辑区 -->
        <div class="bg-white rounded-lg shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">📝 文案生成 (Copywriting)</h2>
          
          <!-- 只读文本框 -->
          <div class="mb-4">
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 min-h-[200px] whitespace-pre-wrap">
              {{ displayText }}
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-2 mb-4">
            <button
              @click="toggleEditing"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                isEditing 
                  ? 'bg-green-500 hover:bg-green-600 text-white' 
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              ]"
            >
              <Edit v-if="!isEditing" :size="18" />
              <Check v-else :size="18" />
              {{ isEditing ? '完成' : '编辑' }}
            </button>

            <button
              v-if="isEditing"
              @click="cancelEditing"
              class="flex items-center gap-2 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
            >
              <X :size="18" />
              取消
            </button>

            <button
              class="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors"
            >
              <Download :size="18" />
              导出全部图片
            </button>

            <button
              class="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors"
            >
              <Copy :size="18" />
              复制全文
            </button>
          </div>

          <!-- 编辑面板 -->
          <CopywritingEditor v-if="isEditing" />
        </div>

        <!-- 右侧：手机预览区 -->
        <div class="bg-white rounded-lg shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">📱 手机预览 (实时同步)</h2>
          
          <div class="mx-auto max-w-sm">
            <!-- 手机框架 -->
            <div class="bg-gray-900 rounded-[2.5rem] p-4 shadow-2xl">
              <div class="bg-white rounded-[2rem] overflow-hidden">
                <!-- 状态栏 -->
                <div class="bg-gray-100 px-6 py-2 flex justify-between items-center text-xs">
                  <span>9:41</span>
                  <span>📶 📡 🔋</span>
                </div>

                <!-- 内容区 -->
                <div class="p-4 h-[600px] overflow-y-auto">
                  <!-- 标题 -->
                  <h3 class="text-lg font-bold text-gray-900 mb-3">
                    {{ previewTitle }}
                  </h3>

                  <!-- 图片轮播 -->
                  <div class="mb-4">
                    <div class="relative bg-gray-200 rounded-lg overflow-hidden aspect-square">
                      <img
                        v-if="previewImages.length > 0"
                        :src="previewImages[currentImageIndex]"
                        :alt="`预览图 ${currentImageIndex + 1}`"
                        class="w-full h-full object-cover"
                      />
                      <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                        暂无图片
                      </div>

                      <!-- 图片指示器 -->
                      <div v-if="previewImages.length > 1" class="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
                        <div
                          v-for="(_, idx) in previewImages"
                          :key="idx"
                          :class="[
                            'w-2 h-2 rounded-full transition-colors',
                            idx === currentImageIndex ? 'bg-white' : 'bg-white/50'
                          ]"
                        />
                      </div>

                      <!-- 切换按钮 -->
                      <button
                        v-if="previewImages.length > 1"
                        @click="prevImage"
                        class="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white rounded-full p-2 hover:bg-black/70"
                      >
                        ‹
                      </button>
                      <button
                        v-if="previewImages.length > 1"
                        @click="nextImage"
                        class="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white rounded-full p-2 hover:bg-black/70"
                      >
                        ›
                      </button>
                    </div>
                  </div>

                  <!-- 正文 -->
                  <div class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {{ previewContent }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAnalysisStore } from '../stores/analysis'
import { storeToRefs } from 'pinia'
import { Edit, Check, X, Download, Copy } from 'lucide-vue-next'
import CopywritingEditor from '../components/CopywritingEditor.vue'

const analysisStore = useAnalysisStore()
const { isEditing, editableContent } = storeToRefs(analysisStore)

const dataLoaded = ref(false)
const currentImageIndex = ref(0)

// 测试数据
const testData = {
  title: '不舒服的关系，不断开留着过年吗？🤷‍♀️',
  body: `最近刷到好多姐妹在聊"断关系"！不是闹分手，是集体觉醒：任何让你持续内耗、不舒服的关系，都该立刻喊停。

👉 微博和小红书加起来快30条热门讨论，核心就一句：及时止损。

💡 恋爱也好友情也罢，一旦沟通变无效争吵，付出变单向消耗，你的感受就是唯一警报。

🔥 大家不是不爱了，是更爱自己了。高赞评论都在说：断开后不是结束，是自我成长的开始。

说白了，成年人的顶级自律，不是坚持，而是懂得放弃。

你为哪段关系拧巴过？评论区聊聊。

#情感断舍离 #成年人的清醒 #关系边界感 #自我成长 #情感内耗`,
  images: [
    '/src/test/xhs_title_card (8).png',  // 已生成的Title Card
    '/src/test/xhs_ai_image_1.jpg',      // AI配图1
    '/src/test/xhs_ai_image_2.jpg'       // AI配图2
  ]
}

// 加载测试数据
const loadTestData = () => {
  console.log('[EditorTestView] 🚀 开始加载测试数据:', {
    imagesCount: testData.images.length,
    images: testData.images
  })
  
  // 清空 sessionStorage 避免旧数据干扰
  sessionStorage.removeItem('grandchart_analysis_results')
  console.log('[EditorTestView] 🗑️ 已清空 sessionStorage')
  
  // 设置图片数据（包含Title Card图片 + AI配图）
  analysisStore.imageUrls = [...testData.images] // 使用展开运算符确保响应式

  // 初始化可编辑内容
  // 索引0=Title Card图片, 索引1-2=AI配图（共3张）
  analysisStore.editableContent = {
    title: testData.title,
    body: testData.body,
    selectedImageIndices: [0, 1, 2], // 默认全选：Title Card + 2张AI配图
    imageOrder: [0, 1, 2]
  }

  dataLoaded.value = true
  
  console.log('✅ 测试数据已加载:', {
    title: testData.title,
    bodyLength: testData.body.length,
    totalImages: testData.images.length,
    imageUrls: analysisStore.imageUrls,
    imageUrlsLength: analysisStore.imageUrls.length,
    selectedIndices: [0, 1, 2],
    imageOrder: [0, 1, 2]
  })
}

// 清空数据
const clearData = () => {
  analysisStore.editableContent = {
    title: '',
    body: '',
    selectedImageIndices: [],
    imageOrder: []
  }
  analysisStore.imageUrls = []
  dataLoaded.value = false
  console.log('🗑️ 数据已清空')
}

// 切换编辑模式
const toggleEditing = () => {
  if (isEditing.value) {
    analysisStore.saveEditing()
  } else {
    analysisStore.startEditing()
  }
}

// 取消编辑
const cancelEditing = () => {
  if (confirm('确定要取消编辑吗？所有未保存的更改将丢失。')) {
    analysisStore.cancelEditing()
  }
}

// 显示文本（只读区域）
const displayText = computed(() => {
  if (!editableContent.value.title && !editableContent.value.body) {
    return '点击上方"加载测试数据"按钮开始测试...'
  }
  return `${editableContent.value.title}\n\n${editableContent.value.body}`
})

// 预览标题
const previewTitle = computed(() => {
  return editableContent.value.title || '标题'
})

// 预览正文
const previewContent = computed(() => {
  return editableContent.value.body || '正文内容'
})

// 预览图片（根据选中和排序）
const previewImages = computed(() => {
  console.log('[EditorTestView] 📱 计算预览图片:', {
    imageUrlsCount: analysisStore.imageUrls?.length || 0,
    selectedIndices: editableContent.value.selectedImageIndices,
    imageOrder: editableContent.value.imageOrder
  })
  
  if (!analysisStore.imageUrls || analysisStore.imageUrls.length === 0) {
    console.log('[EditorTestView] ⚠️ 没有图片数据')
    return []
  }

  const { selectedImageIndices, imageOrder } = editableContent.value
  
  if (!selectedImageIndices || selectedImageIndices.length === 0) {
    console.log('[EditorTestView] ⚠️ 没有选中的图片')
    return []
  }

  // imageUrls 包含所有图片（Title Card图片 + AI配图）
  // selectedImageIndices 和 imageOrder 的索引对应 imageUrls 的索引
  const result = imageOrder
    .filter(idx => selectedImageIndices.includes(idx))
    .map(idx => analysisStore.imageUrls[idx])
    .filter(Boolean)
  
  console.log('[EditorTestView] ✅ 预览图片结果:', {
    count: result.length,
    urls: result.map(url => url.substring(url.lastIndexOf('/') + 1))
  })
  
  return result
})

// 图片切换
const prevImage = () => {
  const oldIndex = currentImageIndex.value
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  } else {
    currentImageIndex.value = previewImages.value.length - 1
  }
  console.log('[EditorTestView] ⬅️ 切换到上一张:', { from: oldIndex, to: currentImageIndex.value })
}

const nextImage = () => {
  const oldIndex = currentImageIndex.value
  if (currentImageIndex.value < previewImages.value.length - 1) {
    currentImageIndex.value++
  } else {
    currentImageIndex.value = 0
  }
  console.log('[EditorTestView] ➡️ 切换到下一张:', { from: oldIndex, to: currentImageIndex.value })
}

// 监听编辑内容变化，实时同步预览
watch(() => editableContent.value, (newContent) => {
  console.log('[EditorTestView] 📝 编辑内容已更新:', {
    title: newContent.title?.substring(0, 20) + '...',
    bodyLength: newContent.body?.length,
    selectedImages: newContent.selectedImageIndices?.length,
    imageOrder: newContent.imageOrder,
    previewImagesCount: previewImages.value.length
  })
}, { deep: true })
</script>
