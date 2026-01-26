<template>
  <div v-if="showPreview" class="w-full h-full bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
    <div class="text-sm text-slate-500 dark:text-slate-400">雷达图预览</div>
  </div>
</template>

<script setup>
import { Chart } from 'chart.js/auto'

const props = defineProps({
  data: {
    type: Object,
    required: true
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
  console.log('[RadarChartCanvas] 🎨 开始生成雷达图')
  console.log('[RadarChartCanvas] 📊 输入数据:', {
    labels: props.data.labels,
    dataPoints: props.data.datasets[0].data,
    theme: props.theme
  })
  
  const canvas = document.createElement('canvas')
  const WIDTH = 1080
  const HEIGHT = 1440
  canvas.width = WIDTH
  canvas.height = HEIGHT
  const ctx = canvas.getContext('2d')
  
  // 1. 背景渐变
  const gradient = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT)
  gradient.addColorStop(0, '#ffffff')
  gradient.addColorStop(1, '#eff6ff')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  
  // 2. 顶部标题区域
  const headerY = 80
  const headerHeight = 120
  
  // 绘制雷达图标背景圆
  ctx.fillStyle = '#dbeafe'
  ctx.beginPath()
  ctx.arc(120, headerY + headerHeight / 2, 50, 0, Math.PI * 2)
  ctx.fill()
  
  // 绘制雷达 Emoji
  ctx.font = '60px "Apple Color Emoji", "Segoe UI Emoji", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('📡', 120, headerY + headerHeight / 2)
  
  // 标题文字
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 72px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('平台覆盖分布', 200, headerY + headerHeight / 2)
  
  // 3. 创建临时 canvas 绘制雷达图
  const chartCanvas = document.createElement('canvas')
  const chartSize = 800
  chartCanvas.width = chartSize
  chartCanvas.height = chartSize
  
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  
  console.log('[RadarChartCanvas] 📈 创建 Chart.js 雷达图')
  const chartInstance = new Chart(chartCanvas.getContext('2d'), {
    type: 'radar',
    data: {
      labels: props.data.labels,
      datasets: [{
        data: props.data.datasets[0].data,
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        borderWidth: 3,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 3,
        pointRadius: 6,
        pointHoverRadius: 8
      }]
    },
    options: {
      responsive: false,
      animation: false,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            font: {
              size: 20
            },
            color: '#64748b'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)',
            lineWidth: 2
          },
          pointLabels: {
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
  
  // 4. 将雷达图绘制到主 canvas
  const chartY = headerY + headerHeight + 60
  const chartX = (WIDTH - chartSize) / 2
  ctx.drawImage(chartCanvas, chartX, chartY, chartSize, chartSize)
  
  // 销毁临时图表
  chartInstance.destroy()
  
  // 5. 绘制图例
  const legendY = chartY + chartSize + 60
  const legendItemWidth = WIDTH / 3
  const legendItemHeight = 80
  
  props.data.labels.forEach((label, index) => {
    const col = index % 3
    const row = Math.floor(index / 3)
    const x = 80 + col * legendItemWidth
    const y = legendY + row * legendItemHeight
    
    // 颜色圆点
    ctx.fillStyle = colors[index % colors.length]
    ctx.beginPath()
    ctx.arc(x, y, 12, 0, Math.PI * 2)
    ctx.fill()
    
    // 平台名称
    ctx.fillStyle = '#475569'
    ctx.font = '32px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.fillText(label, x + 25, y)
    
    // 数值
    ctx.fillStyle = '#1e293b'
    ctx.font = 'bold 36px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(props.data.datasets[0].data[index].toString(), x + 25 + ctx.measureText(label).width + 20, y)
  })
  
  // 6. 底部水印
  // 数据来源说明
  ctx.fillStyle = '#cbd5e1'
  ctx.font = '22px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('* 数值基于各平台实际爬取内容数量归一化', WIDTH / 2, HEIGHT - 95)
  
  // 品牌水印
  ctx.fillStyle = '#cbd5e1'
  ctx.font = '24px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillText('@观潮GlobalInSight · AI舆情洞察', WIDTH / 2, HEIGHT - 60)
  
  const dataUrl = canvas.toDataURL('image/png')
  console.log('[RadarChartCanvas] ✅ 雷达图生成完成，大小:', dataUrl.length, 'bytes')
  return dataUrl
}

defineExpose({
  generateImage
})
</script>
