<template>
  <div v-if="showPreview" class="w-full h-full bg-gradient-to-br from-orange-50 to-amber-50 dark:from-slate-800 dark:to-slate-900 rounded-xl shadow-lg p-6">
    <div class="text-sm text-slate-500 dark:text-slate-400">关键发现预览</div>
  </div>
</template>

<script setup>
const props = defineProps({
  findings: {
    type: Array,
    default: () => []
  },
  theme: {
    type: String,
    default: 'warm'
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
  
  // 1. 背景渐变
  const gradient = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT)
  gradient.addColorStop(0, '#fff7ed')
  gradient.addColorStop(1, '#fef3c7')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  
  // 2. 顶部标题区域
  const headerY = 80
  const headerHeight = 120
  
  // 绘制星星图标背景圆
  ctx.fillStyle = '#fed7aa'
  ctx.beginPath()
  ctx.arc(120, headerY + headerHeight / 2, 50, 0, Math.PI * 2)
  ctx.fill()
  
  // 绘制星星 Emoji
  ctx.font = '60px "Apple Color Emoji", "Segoe UI Emoji", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('✨', 120, headerY + headerHeight / 2)
  
  // 标题文字
  ctx.fillStyle = '#78350f'
  ctx.font = 'bold 72px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('关键发现', 200, headerY + headerHeight / 2)
  
  // 3. 发现列表
  const listStartY = headerY + headerHeight + 80
  const findings = props.findings.slice(0, 3) // 最多3条
  const itemSpacing = 180
  const maxTextWidth = WIDTH - 280
  
  findings.forEach((finding, index) => {
    const itemY = listStartY + index * itemSpacing
    
    // 序号圆圈
    const circleX = 120
    const circleY = itemY
    const circleRadius = 35
    
    ctx.fillStyle = '#f97316'
    ctx.beginPath()
    ctx.arc(circleX, circleY, circleRadius, 0, Math.PI * 2)
    ctx.fill()
    
    // 序号文字
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 48px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(String(index + 1), circleX, circleY)
    
    // 发现文本
    ctx.fillStyle = '#78350f'
    ctx.font = '42px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    
    const lines = wrapText(ctx, finding, maxTextWidth)
    const lineHeight = 60
    
    lines.forEach((line, lineIndex) => {
      ctx.fillText(line, 200, itemY - 20 + lineIndex * lineHeight)
    })
  })
  
  // 4. 装饰元素 - 底部波浪
  ctx.fillStyle = 'rgba(251, 146, 60, 0.1)'
  ctx.beginPath()
  ctx.moveTo(0, HEIGHT - 200)
  for (let x = 0; x <= WIDTH; x += 50) {
    const y = HEIGHT - 200 + Math.sin(x / 100) * 30
    ctx.lineTo(x, y)
  }
  ctx.lineTo(WIDTH, HEIGHT)
  ctx.lineTo(0, HEIGHT)
  ctx.closePath()
  ctx.fill()
  
  // 5. 底部水印
  // 数据来源说明
  ctx.fillStyle = '#d97706'
  ctx.font = '22px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('* 关键发现由 LLM 多维度分析自动提取', WIDTH / 2, HEIGHT - 95)
  
  // 品牌水印
  ctx.fillStyle = '#d97706'
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

defineExpose({
  generateImage
})
</script>
