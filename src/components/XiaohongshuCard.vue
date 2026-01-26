<template>
  <div 
    class="relative w-full h-full overflow-hidden transition-colors duration-500"
    :class="dynamicStyle.bg"
    style="touch-action: pan-y;"
  >
    <!-- Emoji Layer -->
    <div 
      class="absolute text-[5rem] select-none transition-all duration-500 ease-spring leading-none z-10"
      :style="emojiStyle"
      @click="$emit('emoji-click')"
    >
      {{ emoji || '🤔' }}
    </div>
    
    <!-- Title Layer -->
    <h2 :class="[
      'font-black relative z-10 leading-tight tracking-tight drop-shadow-sm',
      dynamicStyle.textColor
    ]"
    :style="titleTextStyle">
      {{ title || '标题生成中...' }}
    </h2>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  emoji: { type: String, default: '🤔' },
  theme: { type: String, default: 'cool' },
  emojiPos: { type: String, default: 'bottom-right' }
})

defineEmits(['emoji-click'])

// --- Styles & Constants ---

const themeStyles = {
  // 暖色系
  warm: { bg: 'bg-gradient-to-br from-orange-50 to-amber-100', textColor: 'text-amber-900' },
  peach: { bg: 'bg-gradient-to-br from-orange-100 to-pink-100', textColor: 'text-orange-900' },
  sunset: { bg: 'bg-gradient-to-br from-amber-100 to-rose-100', textColor: 'text-amber-900' },
  
  // 冷色系
  cool: { bg: 'bg-gradient-to-br from-indigo-50 to-cyan-100', textColor: 'text-slate-800' },
  ocean: { bg: 'bg-gradient-to-br from-blue-100 to-teal-100', textColor: 'text-blue-900' },
  mint: { bg: 'bg-gradient-to-br from-emerald-50 to-teal-100', textColor: 'text-emerald-900' },
  sky: { bg: 'bg-gradient-to-br from-sky-100 to-blue-100', textColor: 'text-sky-900' },
  
  // 紫色系
  lavender: { bg: 'bg-gradient-to-br from-purple-50 to-violet-100', textColor: 'text-purple-900' },
  grape: { bg: 'bg-gradient-to-br from-violet-100 to-fuchsia-100', textColor: 'text-violet-900' },
  
  // 绿色系
  forest: { bg: 'bg-gradient-to-br from-green-50 to-emerald-100', textColor: 'text-green-900' },
  lime: { bg: 'bg-gradient-to-br from-lime-50 to-green-100', textColor: 'text-lime-900' },
  
  // 特殊色
  alert: { bg: 'bg-gradient-to-br from-red-100 to-rose-200', textColor: 'text-red-900' },
  dark: { bg: 'bg-gradient-to-br from-slate-800 to-slate-900', textColor: 'text-white' },
  cream: { bg: 'bg-gradient-to-br from-stone-50 to-amber-50', textColor: 'text-stone-800' }
}

const themeColorMap = {
  // 暖色系
  warm: { gradientStart: '#fff7ed', gradientEnd: '#fef3c7', textColor: '#78350f' },
  peach: { gradientStart: '#ffedd5', gradientEnd: '#fce7f3', textColor: '#7c2d12' },
  sunset: { gradientStart: '#fef3c7', gradientEnd: '#ffe4e6', textColor: '#78350f' },
  
  // 冷色系
  cool: { gradientStart: '#eef2ff', gradientEnd: '#cffafe', textColor: '#1e293b' },
  ocean: { gradientStart: '#dbeafe', gradientEnd: '#ccfbf1', textColor: '#1e3a8a' },
  mint: { gradientStart: '#ecfdf5', gradientEnd: '#ccfbf1', textColor: '#064e3b' },
  sky: { gradientStart: '#e0f2fe', gradientEnd: '#dbeafe', textColor: '#0c4a6e' },
  
  // 紫色系
  lavender: { gradientStart: '#faf5ff', gradientEnd: '#ede9fe', textColor: '#581c87' },
  grape: { gradientStart: '#ede9fe', gradientEnd: '#fae8ff', textColor: '#5b21b6' },
  
  // 绿色系
  forest: { gradientStart: '#f0fdf4', gradientEnd: '#d1fae5', textColor: '#14532d' },
  lime: { gradientStart: '#f7fee7', gradientEnd: '#dcfce7', textColor: '#365314' },
  
  // 特殊色
  alert: { gradientStart: '#fee2e2', gradientEnd: '#fecdd3', textColor: '#7f1d1d' },
  dark: { gradientStart: '#1e293b', gradientEnd: '#0f172a', textColor: '#ffffff' },
  cream: { gradientStart: '#fafaf9', gradientEnd: '#fffbeb', textColor: '#292524' }
}

const dynamicStyle = computed(() => themeStyles[props.theme] || themeStyles.cool)

// --- CSS Preview Logic ---

const emojiStyle = computed(() => {
    const pos = props.emojiPos
    const margin = '8%' // CSS Preview use 8%
    const style = { transform: 'rotate(-10deg)' } 
    
    switch(pos) {
        case 'top-left':
            return { ...style, top: margin, left: margin }
        case 'top-right':
            return { ...style, top: margin, right: margin, transform: 'rotate(10deg)' }
        case 'bottom-left':
            return { ...style, bottom: margin, left: margin, transform: 'rotate(5deg)' }
        case 'bottom-right':
        default:
            return { ...style, bottom: margin, right: margin }
    }
})

const titleTextStyle = computed(() => {
    const pos = props.emojiPos
    const style = { 
        maxWidth: '65%', // 缩小最大宽度，给 emoji 留出空间
        position: 'absolute',
        wordBreak: 'break-word',
        fontSize: '2.5rem' // Ensure consistent preview size
    }
    
    const verticalMargin = '20%' // 增大垂直边距，避免和 emoji 重叠
    const horizontalMargin = '12%'
    
    switch(pos) {
        case 'top-left': // Text -> Bottom-Right
            style.bottom = verticalMargin
            style.right = horizontalMargin
            style.textAlign = 'right'
            style.alignItems = 'flex-end'
            break
        case 'top-right': // Text -> Bottom-Left
            style.bottom = verticalMargin
            style.left = horizontalMargin
            style.textAlign = 'left'
            style.alignItems = 'flex-start'
            break
        case 'bottom-left': // Text -> Top-Right
            style.top = verticalMargin
            style.right = horizontalMargin
            style.textAlign = 'right'
            style.alignItems = 'flex-end'
            break
        case 'bottom-right': // Text -> Top-Left
        default:
            style.top = verticalMargin
            style.left = horizontalMargin
            style.textAlign = 'left'
            style.alignItems = 'flex-start'
            break
    }
    
    return style
})

// --- Canvas Generation Logic ---

const generateImage = async () => {
    const canvas = document.createElement('canvas')
    const WIDTH = 1080 
    const HEIGHT = 1440
    canvas.width = WIDTH
    canvas.height = HEIGHT
    const ctx = canvas.getContext('2d')
    
    const colors = themeColorMap[props.theme] || themeColorMap.cool
    
    // 1. Background
    const gradient = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT)
    gradient.addColorStop(0, colors.gradientStart)
    gradient.addColorStop(1, colors.gradientEnd)
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, WIDTH, HEIGHT)
    
    // 2. Emoji
    // Preview: 8% margin. 8% of 1080 = 86.4px. Let's use 8%.
    const marginX = WIDTH * 0.08
    const marginY = WIDTH * 0.08 
    const emojiMarginY = HEIGHT * 0.08 
    const emojiMarginX = WIDTH * 0.08
    
    const emojiPos = props.emojiPos
    let emojiX, emojiY
    
    const emojiSize = 250 
    const halfEmojiSize = emojiSize / 2

    switch(emojiPos) {
      case 'top-left':
        emojiX = emojiMarginX + halfEmojiSize
        emojiY = emojiMarginY + halfEmojiSize
        break
      case 'top-right':
        emojiX = WIDTH - emojiMarginX - halfEmojiSize
        emojiY = emojiMarginY + halfEmojiSize
        break
      case 'bottom-left':
        emojiX = emojiMarginX + halfEmojiSize
        emojiY = HEIGHT - emojiMarginY - halfEmojiSize
        break
      case 'bottom-right':
      default:
        emojiX = WIDTH - emojiMarginX - halfEmojiSize
        emojiY = HEIGHT - emojiMarginY - halfEmojiSize
        break
    }
    
    ctx.font = `${emojiSize}px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    
    ctx.save()
    ctx.translate(emojiX, emojiY)
    const rotation = (Math.random() * 20 - 10) * Math.PI / 180
    ctx.rotate(rotation)
    ctx.fillText(props.emoji || '🤔', 0, 0)
    ctx.restore()
    
    // 3. Title Text
    // Margins logic: Vertical 18%, Horizontal 12%
    const textMarginX = WIDTH * 0.12
    const textMarginY = HEIGHT * 0.18
    const maxTitleWidth = WIDTH * 0.72 
    
    const titleText = props.title || '标题生成中...'
    let fontSize = 135 
    
    ctx.fillStyle = colors.textColor
    ctx.shadowColor = 'rgba(0,0,0,0.1)'
    ctx.shadowBlur = 10
    ctx.shadowOffsetX = 4
    ctx.shadowOffsetY = 4
    
    let textX, textY, textAlign
    
    switch(emojiPos) {
        case 'top-left': // Text Bottom-Right
            textX = WIDTH - textMarginX
            textY = HEIGHT - textMarginY
            textAlign = 'right'
            break
        case 'top-right': // Text Bottom-Left
            textX = textMarginX
            textY = HEIGHT - textMarginY
            textAlign = 'left'
            break
        case 'bottom-left': // Text Top-Right
            textX = WIDTH - textMarginX
            textY = textMarginY
            textAlign = 'right'
            break
        case 'bottom-right': // Text Top-Left
        default:
            textX = textMarginX
            textY = textMarginY
            textAlign = 'left'
            break
    }
    
    ctx.textAlign = textAlign
    ctx.textBaseline = 'middle'
    ctx.lineWidth = 3
    ctx.strokeStyle = colors.textColor
    
    // --- Exclusion Zone Algorithm ---
    // 增大 padding 确保 emoji 和文字有足够间距
    const padding = 60
    const emojiBox = {
        left: emojiX - halfEmojiSize - padding,
        right: emojiX + halfEmojiSize + padding,
        top: emojiY - halfEmojiSize - padding,
        bottom: emojiY + halfEmojiSize + padding
    }

    const getLayoutForLine = (lineY, lineHeight) => {
        const lineTop = lineY - lineHeight / 2
        const lineBottom = lineY + lineHeight / 2
        
        // 如果行完全在 emoji 区域外，返回完整宽度
        if (lineBottom < emojiBox.top || lineTop > emojiBox.bottom) {
            return { width: maxTitleWidth }
        }
        
        // 行与 emoji 区域有垂直重叠，需要计算可用宽度
        let availableWidth = maxTitleWidth
        
        if (textAlign === 'left') {
            // 文字左对齐（从 textX 开始向右）
            // 检查 emoji 是否在文字右侧阻挡
            const textRight = textX + maxTitleWidth
            if (emojiBox.left < textRight && emojiBox.right > textX) {
                // emoji 在文字区域内，需要缩短宽度
                availableWidth = Math.max(0, emojiBox.left - textX)
            }
        } else {
            // 文字右对齐（从 textX 向左）
            // 检查 emoji 是否在文字左侧阻挡
            const textLeft = textX - maxTitleWidth
            if (emojiBox.right > textLeft && emojiBox.left < textX) {
                // emoji 在文字区域内，需要缩短宽度
                availableWidth = Math.max(0, textX - emojiBox.right)
            }
        }
        
        // 确保最小宽度，避免文字被完全挤掉
        return { width: Math.max(100, availableWidth) }
    }

    const computeLinesWithExclusion = (ctx, text, startY, lineHeight) => {
        const chars = text.split('')
        const lines = []
        let currentLine = ''
        // We simulate layout line by line.
        // We need to track currentY.
        let currentY = startY
        
        // Since we don't know the exact number of lines yet when Bottom Anchor,
        // startY might be wrong. This function assumes startY is the TOP of the first line.
        
        // Initial layout check for first line
        let layout = getLayoutForLine(currentY, lineHeight)
        let currentMaxWidth = layout.width

        for (const char of chars) {
            const testLine = currentLine + char
            const metrics = ctx.measureText(testLine)
            
            if (metrics.width > currentMaxWidth && currentLine.length > 0) {
                lines.push(currentLine)
                currentLine = char
                // Move to next line
                currentY += lineHeight
                // Re-calculate layout for new line
                layout = getLayoutForLine(currentY, lineHeight)
                currentMaxWidth = layout.width
            } else {
                currentLine = testLine
            }
        }
        if (currentLine) lines.push(currentLine)
        return lines
    }
    // Iterative Solver
    let finalLines = []
    let finalStartY = 0
    const isBottomAnchored = emojiPos.includes('top')
    
    // Fallback font shrink loop
    for (let f = 0; f < 3; f++) {
        ctx.font = `900 ${fontSize}px "SF Pro SC", "PingFang SC", sans-serif`
        const lineHeight = fontSize * 1.25
        
        // Stable layout pass
        for (let pass = 0; pass < 3; pass++) {
            let candidateStartY
            if (isBottomAnchored) {
                 // Text is at bottom. Canvas `textY` is the baseline/center of the LAST line.
                 // Deduce Top from it.
                 const numLines = (finalLines && finalLines.length) ? finalLines.length : 3 
                 candidateStartY = textY - ((numLines - 1) * lineHeight)
            } else {
                 // Text is at Top. `textY` is the center/baseline of FIRST line.
                 candidateStartY = textY + (lineHeight * 0.5)
            }
            
            const lines = computeLinesWithExclusion(ctx, titleText, candidateStartY, lineHeight)
            
            finalLines = lines
            finalStartY = candidateStartY
            
            // If stable, break inner pass
            if (pass > 0 && lines.length === finalLines.length) break
        }
        
        if (finalLines.length <= 4) break
        fontSize -= 15
    }

    // Final Draw
    const finalLineHeight = fontSize * 1.25
    finalLines.forEach((line, i) => {
        const y = finalStartY + (i * finalLineHeight)
        ctx.strokeText(line, textX, y)
        ctx.fillText(line, textX, y)
    })
    
    return canvas.toDataURL('image/png')
}

// Expose generation function
defineExpose({
    generateImage
})
</script>
