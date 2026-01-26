<template>
  <div v-if="showPreview" class="w-full h-full bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
    <div class="text-sm text-slate-500 dark:text-slate-400">趋势图预览</div>
  </div>
</template>

<script setup>
import { Chart } from 'chart.js/auto'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({
      stage: '扩散期',
      growth: 50,
      curve: [40, 55, 70, 80, 90, 95, 92]
    })
  },
  theme: {
    type: String,
    default: 'white'
  },
  showPreview: {
    type: Boolean,
    default: false
  }
})

const generateImage = async () => {
  console.log('[TrendChartCanvas] 🎨 开始生成趋势图')
  console.log('[TrendChartCanvas] 📊 输入数据:', {
    stage: props.data.stage,
    growth: props.data.growth,
    curve: props.data.curve,
    theme: props.theme
  })
  
  const canvas = document.createElement('canvas')
  const WIDTH = 1080
  const HEIGHT = 1440
  canvas.width = WIDTH
  canvas.height = HEIGHT
  const ctx = canvas.getContext('2d')
  
  // 1. 背景
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  
  // 2. 顶部标题区域
  const headerY = 80
  const headerHeight = 120
  
  // 绘制趋势图标背景圆
  ctx.fillStyle = '#dcfce7'
  ctx.beginPath()
  ctx.arc(120, headerY + headerHeight / 2, 50, 0, Math.PI * 2)
  ctx.fill()
  
  // 绘制趋势 Emoji
  ctx.font = '60px "Apple Color Emoji", "Segoe UI Emoji", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('📈', 120, headerY + headerHeight / 2)
  
  // 标题文字
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 72px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('热度趋势分析', 200, headerY + headerHeight / 2)
  
  // 3. 创建临时 canvas 绘制折线图
  const chartCanvas = document.createElement('canvas')
  const chartWidth = 900
  const chartHeight = 600
  chartCanvas.width = chartWidth
  chartCanvas.height = chartHeight
  
  const chartInstance = new Chart(chartCanvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'],
      datasets: [{
        label: '热度指数',
        data: props.data.curve,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 8,
        pointHoverRadius: 10,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 4,
        borderWidth: 4
      }]
    },
    options: {
      responsive: false,
      animation: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (value) => value + '%',
            font: {
              size: 24
            },
            color: '#64748b'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)',
            lineWidth: 2
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: {
              size: 24,
              weight: 'bold'
            },
            color: '#1e293b'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  })
  
  // 等待图表渲染
  await new Promise(resolve => setTimeout(resolve, 100))
  
  // 4. 将折线图绘制到主 canvas
  const chartY = headerY + headerHeight + 80
  const chartX = (WIDTH - chartWidth) / 2
  ctx.drawImage(chartCanvas, chartX, chartY, chartWidth, chartHeight)
  
  // 销毁临时图表
  chartInstance.destroy()
  
  // 5. 阶段标签
  const stageY = chartY + chartHeight + 80
  const stageWidth = WIDTH / 3
  
  const stages = [
    { label: '爆发期', desc: '快速上升', color: '#10b981' },
    { label: '扩散期', desc: '持续增长', color: '#3b82f6' },
    { label: '回落期', desc: '逐渐降温', color: '#f97316' }
  ]
  
  stages.forEach((stage, index) => {
    const x = 80 + index * stageWidth
    
    // 标签
    ctx.fillStyle = stage.color
    ctx.font = 'bold 40px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(stage.label, x, stageY)
    
    // 描述
    ctx.fillStyle = '#64748b'
    ctx.font = '32px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(stage.desc, x, stageY + 50)
  })
  
  // 6. 当前状态卡片
  const statusY = stageY + 140
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(80, statusY, WIDTH - 160, 140)
  
  // 状态指示点
  const stageColor = props.data.stage === '爆发期' ? '#10b981' : 
                     props.data.stage === '扩散期' ? '#3b82f6' : '#f97316'
  ctx.fillStyle = stageColor
  ctx.beginPath()
  ctx.arc(140, statusY + 70, 15, 0, Math.PI * 2)
  ctx.fill()
  
  // 当前阶段文字
  ctx.fillStyle = '#475569'
  ctx.font = '36px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('当前阶段：', 180, statusY + 50)
  
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 40px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillText(props.data.stage, 180, statusY + 100)
  
  // 增速
  const growthColor = props.data.growth > 100 ? '#10b981' : 
                      props.data.growth > 0 ? '#3b82f6' : '#ef4444'
  ctx.fillStyle = '#475569'
  ctx.font = '36px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText('增速：', WIDTH - 280, statusY + 75)
  
  ctx.fillStyle = growthColor
  ctx.font = 'bold 44px "PingFang SC", "Microsoft YaHei", sans-serif'
  const growthText = props.data.growth > 0 ? `+${props.data.growth}%` : `${props.data.growth}%`
  ctx.fillText(growthText, WIDTH - 100, statusY + 75)
  
  // 7. 底部水印
  // 数据来源说明
  ctx.fillStyle = '#cbd5e1'
  ctx.font = '22px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('* 基于语义分析的热度推演模型', WIDTH / 2, HEIGHT - 95)
  
  // 品牌水印
  ctx.fillStyle = '#cbd5e1'
  ctx.font = '24px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillText('@观潮GlobalInSight · AI舆情洞察', WIDTH / 2, HEIGHT - 60)
  
  const dataUrl = canvas.toDataURL('image/png')
  console.log('[TrendChartCanvas] ✅ 趋势图生成完成，大小:', dataUrl.length, 'bytes')
  return dataUrl
}

defineExpose({
  generateImage
})
</script>
