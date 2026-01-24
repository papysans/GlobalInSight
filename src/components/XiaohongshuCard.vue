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
  warm: { bg: 'bg-gradient-to-br from-orange-50 to-amber-100', textColor: 'text-amber-900' },
  cool: { bg: 'bg-gradient-to-br from-indigo-50 to-cyan-100', textColor: 'text-slate-800' },
  alert: { bg: 'bg-gradient-to-br from-red-100 to-rose-200', textColor: 'text-red-900' },
  dark: { bg: 'bg-gradient-to-br from-slate-800 to-slate-900', textColor: 'text-white' }
}

const themeColorMap = {
  warm: { gradientStart: '#fff7ed', gradientEnd: '#fef3c7', textColor: '#78350f' },
  cool: { gradientStart: '#eef2ff', gradientEnd: '#cffafe', textColor: '#1e293b' },
  alert: { gradientStart: '#fee2e2', gradientEnd: '#fecdd3', textColor: '#7f1d1d' },
  dark: { gradientStart: '#1e293b', gradientEnd: '#0f172a', textColor: '#ffffff' }
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
        maxWidth: '75%',
        position: 'absolute',
        wordBreak: 'break-word',
        fontSize: '2.5rem' // Ensure consistent preview size
    }
    
    const verticalMargin = '18%'
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
    const marginY = WIDTH * 0.08 // Usually margins are visually consistent, so relative to width is common or height?
    // In CSS "top: 8%", it's percentage of container height usually.
    // 8% of 1440 = 115.2px.
    const emojiMarginY = HEIGHT * 0.08 
    const emojiMarginX = WIDTH * 0.08
    
    const emojiPos = props.emojiPos
    let emojiX, emojiY
    
    switch(emojiPos) {
      case 'top-left':
        emojiX = emojiMarginX
        emojiY = emojiMarginY
        break
      case 'top-right':
        emojiX = WIDTH - emojiMarginX
        emojiY = emojiMarginY
        break
      case 'bottom-left':
        emojiX = emojiMarginX
        emojiY = HEIGHT - emojiMarginY
        break
      case 'bottom-right':
      default:
        emojiX = WIDTH - emojiMarginX
        emojiY = HEIGHT - emojiMarginY
        break
    }
    
    // Emoji size: 5rem in preview. 5 * 16 = 80px (on typical root). 
    // Phone view is ~320px wide. 80/320 = 1/4.
    // On 1080px canvas, 1/4 * 1080 = 270px.
    // Let's settle on 220px to 250px.
    const emojiSize = 250 
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
    // Margins logic:
    // Vertical: 18% of Height
    // Horizontal: 12% of Width
    const textMarginX = WIDTH * 0.12
    const textMarginY = HEIGHT * 0.18
    const maxTitleWidth = WIDTH * 0.75 // 75% width
    
    const titleText = props.title || '标题生成中...'
    
    // Font Sizing matches 2.5rem ~ 1/8 to 1/7 of container width
    let fontSize = 135 
    
    // Wrapping helper
    const getLines = (ctx, text, maxWidth) => {
        const chars = text.split('')
        const lines = []
        let line = ''
        for (const char of chars) {
            const testLine = line + char
            const metrics = ctx.measureText(testLine)
            if (metrics.width > maxWidth && line.length > 0) {
                lines.push(line)
                line = char
            } else {
                line = testLine
            }
        }
        if (line) lines.push(line)
        return lines
    }
    
    let lines = []
    // Fallback shrink loop (only if crazy long)
    for (let i = 0; i < 5; i++) {
        ctx.font = `900 ${fontSize}px "SF Pro SC", "PingFang SC", "Microsoft YaHei", sans-serif`
        lines = getLines(ctx, titleText, maxTitleWidth)
        if (lines.length <= 4) break
        fontSize -= 10
        if (fontSize < 80) break
    }
    
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
    const lineHeight = fontSize * 1.25
    
    // Positioning logic (calculating start Y based on block height)
    let startY = textY
    const totalBlockHeight = lines.length * lineHeight
    
    if (emojiPos.includes('top')) {
        // Text is at Bottom. anchor textY is the "Bottom" line (from CSS: bottom: 18%)
        // So we draw UPWARDS from textY? or we shift startY up.
        // Let's say textY is the visual center of the last line? Or bottom of the block?
        // To be safe: let's assume textY is the bottom edge of the text block area.
        // Let's shift up by total block height.
        startY = textY - totalBlockHeight + (lineHeight * 0.5) // basic adjustment
        // Actually, canvas textBaseline middle means Y is center of char.
        // If textY is "bottom margin", it's the baseline of the last line roughly.
        startY = textY - ((lines.length - 1) * lineHeight)
    } else {
        // Text is at Top. textY is "Top" margin (top: 18%).
        // This is the top of the block.
        // We draw downwards.
        startY = textY + (lineHeight * 0.5) // Push down half-line for middle baseline
    }
    
    lines.forEach((line, i) => {
        ctx.fillText(line, textX, startY + (i * lineHeight))
    })
    
    return canvas.toDataURL('image/png')
}

// Expose generation function
defineExpose({
    generateImage
})
</script>
