<template>
  <div v-if="showPreview" class="w-full h-full bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl shadow-lg p-6">
    <div class="text-sm text-slate-500">辩论时间线预览</div>
  </div>
</template>

<script setup>
const props = defineProps({
  timeline: {
    type: Array,
    default: () => []
  },
  theme: {
    type: String,
    default: 'default'
  },
  showPreview: {
    type: Boolean,
    default: false
  }
})

// 智能提取核心观点（使用 summary 字段，完整显示）
const extractKeyPoint = (item) => {
  if (item.summary) {
    return item.summary
  }
  const text = item.insight || ''
  const firstSentence = text.match(/^[^。！？.!?]+[。！？.!?]/)
  if (firstSentence) {
    return firstSentence[0]
  }
  return text.substring(0, 30)
}

// 动态计算布局参数
const calculateLayout = (roundCount) => {
  if (roundCount <= 3) {
    return { 
      itemSpacing: 280,      // 🔧 调整这里：每个卡片之间的垂直间距
      cardHeight: 240,       // 🔧 调整这里：卡片高度
      contentFont: 26,
      titleFont: 32
    }
  } else if (roundCount <= 5) {
    return { 
      itemSpacing: 240,      // 🔧 调整这里：4-5轮时的间距
      cardHeight: 200,       // 🔧 调整这里：卡片高度
      contentFont: 24,
      titleFont: 30
    }
  } else if (roundCount <= 7) {
    return { 
      itemSpacing: 200,      // 🔧 调整这里：6-7轮时的间距
      cardHeight: 180,       // 🔧 调整这里：卡片高度
      contentFont: 22,
      titleFont: 28
    }
  } else {
    return { 
      itemSpacing: 170,      // 🔧 调整这里：8轮时的间距
      cardHeight: 160,       // 🔧 调整这里：卡片高度
      contentFont: 20,
      titleFont: 26
    }
  }
}

const generateImage = async () => {
  const canvas = document.createElement('canvas')
  const WIDTH = 1080
  const HEIGHT = 1440
  canvas.width = WIDTH
  canvas.height = HEIGHT
  const ctx = canvas.getContext('2d')
  
  // 动态计算显示的轮数（最多8轮）
  const maxRounds = Math.min(props.timeline.length, 8)
  const timeline = props.timeline.slice(0, maxRounds)
  const layout = calculateLayout(timeline.length)
  
  // 1. 背景 - 浅灰色
  ctx.fillStyle = '#f5f5f5'
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  
  // 2. 顶部标题
  // 标题图标背景圆
  ctx.fillStyle = '#8b5cf6'
  ctx.beginPath()
  ctx.arc(100, 80, 40, 0, Math.PI * 2)
  ctx.fill()
  
  // 标题图标
  ctx.font = '48px "Apple Color Emoji", "Segoe UI Emoji", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('🔀', 100, 80)
  
  // 标题文字
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 56px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('辩论演化过程', 180, 90)
  
  // 3. 时间线内容 - 计算总高度并垂直居中
  const headerY = 100
  const headerHeight = 120
  const summaryHeight = 120
  const summaryMargin = 20
  
  // 🔧 计算时间线内容的总高度
  // 时间线高度 = (轮数-1) * 间距 + 第一个卡片的上半部分 + 最后一个卡片的下半部分
  const timelineContentHeight = (timeline.length - 1) * layout.itemSpacing + layout.cardHeight
  const totalContentHeight = timelineContentHeight + summaryMargin + summaryHeight
  
  // 计算可用空间（画布高度 - 顶部标题 - 底部水印）
  const availableHeight = HEIGHT - (headerY + headerHeight) - 80
  
  // 计算起始Y坐标，使内容垂直居中
  const startY = headerY + headerHeight + (availableHeight - totalContentHeight) / 2
  
  const circleX = 125          // 🔧 调整这里：左侧圆圈的X坐标（增大向右移动）
  const cardX = 200            // 🔧 调整这里：右侧卡片的X坐标
  const cardWidth = WIDTH - cardX - 80
  
  // 绘制每个时间点
  timeline.forEach((item, index) => {
    const itemY = startY + index * layout.itemSpacing
    
    // 虚线连接（在圆圈之间）
    if (index < timeline.length - 1) {
      ctx.strokeStyle = '#60a5fa'
      ctx.lineWidth = 3
      ctx.setLineDash([8, 8])
      ctx.beginPath()
      ctx.moveTo(circleX, itemY + 45)
      ctx.lineTo(circleX, itemY + layout.itemSpacing - 45)
      ctx.stroke()
      ctx.setLineDash([])
    }
    
    // 圆圈
    ctx.fillStyle = '#3b82f6'
    ctx.beginPath()
    ctx.arc(circleX, itemY, 45, 0, Math.PI * 2)
    ctx.fill()
    
    // 轮次文字
    ctx.fillStyle = '#ffffff'
    ctx.font = `bold 40px "PingFang SC", "Microsoft YaHei", sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(`R${item.round}`, circleX, itemY)
    
    // 卡片
    const cardY = itemY - (layout.cardHeight / 2)  // 🔧 使用动态高度，卡片垂直居中对齐圆圈
    const cardHeight = layout.cardHeight           // 🔧 从 layout 获取动态高度
    const cardRadius = 12  // 🔧 调整这里：卡片整体圆角大小
    
    // 卡片背景
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.roundRect(cardX, cardY, cardWidth, cardHeight, cardRadius)
    ctx.fill()
    
    // 左侧蓝色装饰条（只有左侧圆角）
    const barWidth = 8       // 🔧 调整这里：蓝色条的宽度
    const barRadius = 12     // 🔧 调整这里：蓝色条的圆角（应该和 cardRadius 一致）
    ctx.fillStyle = '#3b82f6'
    ctx.beginPath()
    // 使用 roundRect 的四角圆角参数：[左上, 右上, 右下, 左下]
    ctx.roundRect(cardX, cardY, barWidth, cardHeight, [barRadius, 0, 0, barRadius])
    ctx.fill()
    
    // 标题
    ctx.fillStyle = '#1e293b'
    ctx.font = `bold ${layout.titleFont}px "PingFang SC", "Microsoft YaHei", sans-serif`
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    const titleText = item.title.length > 18 ? item.title.substring(0, 18) + '...' : item.title
    ctx.fillText(titleText, cardX + 24, cardY + 20)
    
    // 内容
    ctx.fillStyle = '#64748b'
    ctx.font = `${layout.contentFont}px "PingFang SC", "Microsoft YaHei", sans-serif`
    const keyPoint = extractKeyPoint(item)
    const lines = wrapText(ctx, keyPoint, cardWidth - 48)
    
    lines.slice(0, 3).forEach((line, lineIndex) => {
      ctx.fillText(line, cardX + 24, cardY + 20 + layout.titleFont + 12 + lineIndex * (layout.contentFont + 8))
    })
  })
  
  // 4. 底部总结卡片
  const summaryY = startY + timeline.length * layout.itemSpacing + summaryMargin
  
  // 总结卡片背景
  ctx.fillStyle = '#d1fae5'
  ctx.beginPath()
  ctx.roundRect(80, summaryY, WIDTH - 160, 100, 16)
  ctx.fill()
  
  // 勾选图标
  ctx.fillStyle = '#059669'
  ctx.font = '48px "Apple Color Emoji", "Segoe UI Emoji", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('✓', 120, summaryY + 50)
  
  // 总结文字
  ctx.fillStyle = '#065f46'
  ctx.font = 'bold 32px "PingFang SC", "Microsoft YaHei", sans-serif'
  const summaryText = props.timeline.length > maxRounds 
    ? `展示前 ${maxRounds} 轮，共 ${props.timeline.length} 轮辩论收敛`
    : `经过 ${timeline.length} 轮辩论，AI推理最终收敛`
  ctx.fillText(summaryText, 190, summaryY + 50)
  
  // 5. 底部水印
  ctx.fillStyle = '#94a3b8'
  ctx.font = '24px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('@观潮GlobalInSight · AI舆情洞察', WIDTH / 2, HEIGHT - 40)
  
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

defineExpose({
  generateImage
})
</script>
