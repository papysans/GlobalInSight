<template>
  <div v-if="showPreview" class="w-full h-full bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
    <div class="text-sm text-slate-500 dark:text-slate-400">洞察卡预览</div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      conclusion: '',
      coverage: {
        platforms: 0,
        debateRounds: 0,
        growth: '',
        controversy: 0
      }
    })
  },
  theme: {
    type: String,
    default: 'blue'
  },
  showPreview: {
    type: Boolean,
    default: false
  }
})

const generateImage = async () => {
  const canvas = document.createElement('canvas')
  const WIDTH = 1080
  const HEIGHT = 1440
  canvas.width = WIDTH
  canvas.height = HEIGHT
  const ctx = canvas.getContext('2d')
  
  // 1. 背景渐变 - 始终使用浅色（输出用）
  const gradient = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT)
  gradient.addColorStop(0, '#ffffff')
  gradient.addColorStop(1, '#eff6ff')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  
  // 2. 顶部标题区域
  const headerY = 80
  const headerHeight = 120
  
  // 绘制灯泡图标背景圆
  ctx.fillStyle = '#dbeafe'
  ctx.beginPath()
  ctx.arc(120, headerY + headerHeight / 2, 50, 0, Math.PI * 2)
  ctx.fill()
  
  // 绘制灯泡 Emoji
  ctx.font = '60px "Apple Color Emoji", "Segoe UI Emoji", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('💡', 120, headerY + headerHeight / 2)
  
  // 标题文字
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 72px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('核心洞察', 200, headerY + headerHeight / 2)
  
  // 3. 结论文本区域
  const conclusionY = headerY + headerHeight + 60
  const conclusionMaxWidth = WIDTH - 160
  const conclusionText = props.data.conclusion || '暂无洞察'
  
  ctx.fillStyle = '#475569'
  ctx.font = '48px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  
  // 文本换行
  const lines = wrapText(ctx, conclusionText, conclusionMaxWidth)
  const lineHeight = 72
  
  lines.forEach((line, index) => {
    ctx.fillText(line, 80, conclusionY + index * lineHeight)
  })
  
  // 4. 数据概览区域
  const dataY = conclusionY + lines.length * lineHeight + 80
  const dataBoxY = dataY
  const dataBoxHeight = 280
  
  // 数据背景框
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(80, dataBoxY, WIDTH - 160, dataBoxHeight)
  
  // 数据标题
  ctx.fillStyle = '#64748b'
  ctx.font = 'bold 40px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillText('数据概览', 120, dataBoxY + 60)
  
  // 2x2 数据网格
  const gridStartY = dataBoxY + 120
  const gridItemWidth = (WIDTH - 160) / 2
  const gridItemHeight = 80
  
  const dataItems = [
    { label: '话题覆盖', value: `${props.data.coverage.platforms}个平台`, color: '#3b82f6' },
    { label: '辩论轮次', value: `${props.data.coverage.debateRounds}轮推演`, color: '#a855f7' },
    { label: '生命周期', value: props.data.coverage.growth || '未知', color: '#10b981' },
    { label: '争议程度', value: formatControversy(props.data.coverage.controversy), color: getControversyColor(props.data.coverage.controversy) }
  ]
  
  dataItems.forEach((item, index) => {
    const col = index % 2
    const row = Math.floor(index / 2)
    const x = 120 + col * gridItemWidth
    const y = gridStartY + row * gridItemHeight
    
    // 标签
    ctx.fillStyle = '#94a3b8'
    ctx.font = '32px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(item.label, x, y)
    
    // 数值
    ctx.fillStyle = item.color
    ctx.font = 'bold 52px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(item.value, x, y + 50)
  })
  
  // 5. 底部水印
  // 数据来源说明
  ctx.fillStyle = '#cbd5e1'
  ctx.font = '22px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('* 核心洞察由 Multi-Agent 协作分析生成', WIDTH / 2, HEIGHT - 95)
  
  // 品牌水印
  ctx.fillStyle = '#cbd5e1'
  ctx.font = '24px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillText('@观潮GlobalInSight · AI舆情洞察', WIDTH / 2, HEIGHT - 60)
  
  return canvas.toDataURL('image/png')
}

// 辅助函数：文本换行
const wrapText = (ctx, text, maxWidth) => {
  const chars = text.split('')
  const lines = []
  let currentLine = ''
  
  for (const char of chars) {
    const testLine = currentLine + char
    const metrics = ctx.measureText(testLine)
    
    if (metrics.width > maxWidth && currentLine.length > 0) {
      lines.push(currentLine)
      currentLine = char
    } else {
      currentLine = testLine
    }
  }
  if (currentLine) lines.push(currentLine)
  return lines
}

// 辅助函数：格式化争议程度
const formatControversy = (c) => {
  if (typeof c === 'number') {
    return `${c.toFixed(1)}/10`
  }
  return c || '未知'
}

// 辅助函数：获取争议程度颜色
const getControversyColor = (c) => {
  if (typeof c === 'number') {
    return c > 7 ? '#ef4444' : c > 4 ? '#f97316' : '#10b981'
  }
  return c === '高' ? '#ef4444' : c === '中' ? '#f97316' : '#10b981'
}

defineExpose({
  generateImage
})
</script>
