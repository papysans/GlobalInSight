<template>
  <div ref="containerRef" class="w-full h-[500px] rounded-2xl overflow-hidden relative cursor-grab active:cursor-grabbing">
    <canvas ref="canvasRef" class="w-full h-full"></canvas>
    
    <!-- 悬浮信息卡 -->
    <transition name="card-pop">
      <div 
        v-if="hoveredNode" 
        class="absolute pointer-events-none z-50"
        :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
      >
        <div class="bg-slate-900/95 backdrop-blur-md text-white px-5 py-4 rounded-xl shadow-2xl border border-white/20 min-w-[200px]">
          <!-- 顶部彩色条 -->
          <div class="absolute top-0 left-0 right-0 h-1 rounded-t-xl" :style="{ background: hoveredNode.color }"></div>
          
          <!-- 图标和名称 -->
          <div class="flex items-center gap-3 mb-3">
            <div 
              class="w-10 h-10 rounded-full flex items-center justify-center text-lg"
              :style="{ background: hoveredNode.color + '30', color: hoveredNode.color }"
            >
              {{ hoveredNode.icon }}
            </div>
            <div>
              <div class="font-bold text-lg">{{ hoveredNode.name }}</div>
              <div class="text-xs text-slate-400">{{ hoveredNode.role }}</div>
            </div>
          </div>
          
          <!-- 描述 -->
          <div class="text-sm text-slate-300 mb-3">{{ hoveredNode.desc }}</div>
          
          <!-- 能力标签 -->
          <div class="flex flex-wrap gap-1.5">
            <span 
              v-for="tag in hoveredNode.tags" 
              :key="tag"
              class="px-2 py-0.5 text-xs rounded-full"
              :style="{ background: hoveredNode.color + '20', color: hoveredNode.color }"
            >
              {{ tag }}
            </span>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 操作提示 -->
    <div class="absolute bottom-4 left-4 text-xs text-slate-500 flex items-center gap-2">
      <span class="px-2 py-1 bg-slate-800/50 rounded">🖱️ 拖拽旋转</span>
      <span class="px-2 py-1 bg-slate-800/50 rounded">悬停查看详情</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const containerRef = ref(null)
const canvasRef = ref(null)
const hoveredNode = ref(null)
const tooltipPos = ref({ x: 0, y: 0 })

// Agent 节点数据 - 增强版
const agents = [
  { 
    id: 'crawler', 
    name: 'Crawler', 
    role: '数据采集引擎',
    desc: '多平台并行爬取，支持小红书、微博、抖音等主流平台的实时数据采集', 
    color: '#3b82f6', 
    icon: '🕷️',
    tags: ['多平台', '实时采集', '反爬绕过'],
    position: [-3.5, 1.5, 0] 
  },
  { 
    id: 'reporter', 
    name: 'Reporter', 
    role: '事实提取专家',
    desc: '从海量数据中提取关键事实，进行多源信息聚合与去重', 
    color: '#8b5cf6', 
    icon: '📰',
    tags: ['事实核查', '信息聚合', 'NLP'],
    position: [-1.5, 3, 1] 
  },
  { 
    id: 'analyst', 
    name: 'Analyst', 
    role: '深度分析师',
    desc: '运用 LLM 进行深度语义分析，生成多维度洞察报告', 
    color: '#10b981', 
    icon: '🔬',
    tags: ['语义分析', '趋势预测', '情感分析'],
    position: [1.5, 2.5, -1] 
  },
  { 
    id: 'debater', 
    name: 'Debater', 
    role: '观点辩论者',
    desc: '模拟多方观点进行辩论，通过对抗性思考发现盲点', 
    color: '#f59e0b', 
    icon: '⚔️',
    tags: ['多角度', '批判思维', '共识达成'],
    position: [3, 0.5, 0.5] 
  },
  { 
    id: 'writer', 
    name: 'Writer', 
    role: '爆款文案师',
    desc: '根据平台特性生成适配的爆款文案，支持多种风格', 
    color: '#ec4899', 
    icon: '✍️',
    tags: ['风格适配', '标题党', '情感共鸣'],
    position: [1, -2, 1] 
  },
  { 
    id: 'publisher', 
    name: 'Publisher', 
    role: '自动发布器',
    desc: '通过 MCP 协议自动发布到小红书，支持图文和视频', 
    color: '#ef4444', 
    icon: '🚀',
    tags: ['小红书MCP', '定时发布', '数据回流'],
    position: [-1.5, -2.5, -0.5] 
  }
]

// 连接关系
const connections = [
  ['crawler', 'reporter'],
  ['reporter', 'analyst'],
  ['analyst', 'debater'],
  ['debater', 'analyst'],
  ['analyst', 'writer'],
  ['writer', 'publisher']
]

let scene, camera, renderer, animationId
let nodeMeshes = []
let glowMeshes = []
let pulseRings = []
let particles = []
let raycaster, mouse
let isDragging = false
let previousMousePosition = { x: 0, y: 0 }
let targetRotation = { x: 0, y: 0 }
let currentRotation = { x: 0, y: 0 }
let autoRotate = true

onMounted(() => {
  initScene()
  animate()
  window.addEventListener('resize', onResize)
  canvasRef.value.addEventListener('mousemove', onMouseMove)
  canvasRef.value.addEventListener('mousedown', onMouseDown)
  canvasRef.value.addEventListener('mouseup', onMouseUp)
  canvasRef.value.addEventListener('mouseleave', onMouseUp)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', onResize)
  if (canvasRef.value) {
    canvasRef.value.removeEventListener('mousemove', onMouseMove)
    canvasRef.value.removeEventListener('mousedown', onMouseDown)
    canvasRef.value.removeEventListener('mouseup', onMouseUp)
    canvasRef.value.removeEventListener('mouseleave', onMouseUp)
  }
  renderer?.dispose()
})

function initScene() {
  const container = containerRef.value
  const canvas = canvasRef.value
  
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0f172a)
  
  camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000)
  camera.position.set(0, 0, 10)
  
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  
  // 光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4)
  scene.add(ambientLight)
  
  const pointLight1 = new THREE.PointLight(0x3b82f6, 0.8)
  pointLight1.position.set(5, 5, 5)
  scene.add(pointLight1)
  
  const pointLight2 = new THREE.PointLight(0xec4899, 0.5)
  pointLight2.position.set(-5, -5, 5)
  scene.add(pointLight2)
  
  // 创建节点组
  const nodeGroup = new THREE.Group()
  scene.add(nodeGroup)
  
  // 创建节点
  agents.forEach((agent, index) => {
    // 主球体
    const geometry = new THREE.SphereGeometry(0.5, 64, 64)
    const material = new THREE.MeshPhongMaterial({
      color: agent.color,
      emissive: agent.color,
      emissiveIntensity: 0.4,
      shininess: 100,
      transparent: true,
      opacity: 0.95
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(...agent.position)
    mesh.userData = agent
    nodeGroup.add(mesh)
    nodeMeshes.push(mesh)
    
    // 外发光球体
    const glowGeometry = new THREE.SphereGeometry(0.65, 32, 32)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: agent.color,
      transparent: true,
      opacity: 0.15,
      side: THREE.BackSide
    })
    const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial)
    glowMesh.position.copy(mesh.position)
    nodeGroup.add(glowMesh)
    glowMeshes.push(glowMesh)
    
    // 脉冲环
    for (let i = 0; i < 2; i++) {
      const ringGeometry = new THREE.RingGeometry(0.6, 0.65, 64)
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: agent.color,
        transparent: true,
        opacity: 0,
        side: THREE.DoubleSide
      })
      const ring = new THREE.Mesh(ringGeometry, ringMaterial)
      ring.position.copy(mesh.position)
      ring.userData = { 
        baseScale: 1, 
        phase: i * Math.PI
      }
      nodeGroup.add(ring)
      pulseRings.push(ring)
    }
    
    // 文字标签 Sprite（球体下方）
    const labelCanvas = document.createElement('canvas')
    labelCanvas.width = 512
    labelCanvas.height = 128
    const labelCtx = labelCanvas.getContext('2d')
    
    // 绘制圆角矩形背景（兼容方式）
    const drawRoundRect = (ctx, x, y, width, height, radius) => {
      ctx.beginPath()
      ctx.moveTo(x + radius, y)
      ctx.lineTo(x + width - radius, y)
      ctx.quadraticCurveTo(x + width, y, x + width, y + radius)
      ctx.lineTo(x + width, y + height - radius)
      ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height)
      ctx.lineTo(x + radius, y + height)
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius)
      ctx.lineTo(x, y + radius)
      ctx.quadraticCurveTo(x, y, x + radius, y)
      ctx.closePath()
    }
    
    // 绘制背景
    labelCtx.fillStyle = 'rgba(15, 23, 42, 0.85)'
    drawRoundRect(labelCtx, 10, 20, 492, 88, 20)
    labelCtx.fill()
    
    // 绘制边框
    labelCtx.strokeStyle = agent.color
    labelCtx.lineWidth = 3
    drawRoundRect(labelCtx, 10, 20, 492, 88, 20)
    labelCtx.stroke()
    
    // 绘制文字
    labelCtx.fillStyle = '#ffffff'
    labelCtx.font = 'bold 48px Arial'
    labelCtx.textAlign = 'center'
    labelCtx.textBaseline = 'middle'
    labelCtx.fillText(agent.name, 256, 64)
    
    const labelTexture = new THREE.CanvasTexture(labelCanvas)
    const labelMaterial = new THREE.SpriteMaterial({ 
      map: labelTexture, 
      transparent: true,
      opacity: 0.9
    })
    const labelSprite = new THREE.Sprite(labelMaterial)
    labelSprite.scale.set(2, 0.5, 1)
    labelSprite.position.set(agent.position[0], agent.position[1] - 1.1, agent.position[2])
    // 复制完整的 agent 数据到 userData，确保悬停检测正常工作
    labelSprite.userData = { ...agent, type: 'label' }
    nodeGroup.add(labelSprite)
  })
  
  // 创建连接线（曲线）
  connections.forEach(([fromId, toId]) => {
    const fromAgent = agents.find(a => a.id === fromId)
    const toAgent = agents.find(a => a.id === toId)
    if (!fromAgent || !toAgent) return
    
    const start = new THREE.Vector3(...fromAgent.position)
    const end = new THREE.Vector3(...toAgent.position)
    const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5)
    mid.z += 0.5 // 曲线弧度
    
    const curve = new THREE.QuadraticBezierCurve3(start, mid, end)
    const points = curve.getPoints(50)
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({
      color: 0x475569,
      transparent: true,
      opacity: 0.5
    })
    const line = new THREE.Line(geometry, material)
    nodeGroup.add(line)
    
    // 流动粒子
    for (let i = 0; i < 5; i++) {
      const particleGeometry = new THREE.SphereGeometry(0.06, 16, 16)
      const particleMaterial = new THREE.MeshBasicMaterial({
        color: fromAgent.color,
        transparent: true,
        opacity: 0.9
      })
      const particle = new THREE.Mesh(particleGeometry, particleMaterial)
      particle.userData = {
        curve,
        progress: i / 5,
        speed: 0.003 + Math.random() * 0.002,
        color: fromAgent.color
      }
      nodeGroup.add(particle)
      particles.push(particle)
    }
  })
  
  // 背景粒子
  const bgParticlesGeometry = new THREE.BufferGeometry()
  const bgPositions = []
  const bgColors = []
  for (let i = 0; i < 500; i++) {
    bgPositions.push(
      (Math.random() - 0.5) * 40,
      (Math.random() - 0.5) * 40,
      (Math.random() - 0.5) * 40
    )
    const color = new THREE.Color().setHSL(Math.random() * 0.2 + 0.55, 0.5, 0.5)
    bgColors.push(color.r, color.g, color.b)
  }
  bgParticlesGeometry.setAttribute('position', new THREE.Float32BufferAttribute(bgPositions, 3))
  bgParticlesGeometry.setAttribute('color', new THREE.Float32BufferAttribute(bgColors, 3))
  const bgParticlesMaterial = new THREE.PointsMaterial({ 
    size: 0.03, 
    vertexColors: true,
    transparent: true,
    opacity: 0.6
  })
  const bgParticles = new THREE.Points(bgParticlesGeometry, bgParticlesMaterial)
  scene.add(bgParticles)
  
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()
}

function animate() {
  animationId = requestAnimationFrame(animate)
  
  const time = Date.now() * 0.001
  
  // 自动旋转
  if (autoRotate && !isDragging) {
    targetRotation.y += 0.002
  }
  
  // 平滑旋转
  currentRotation.x += (targetRotation.x - currentRotation.x) * 0.05
  currentRotation.y += (targetRotation.y - currentRotation.y) * 0.05
  
  // 应用旋转到场景中的节点组
  if (scene.children[3]) { // nodeGroup
    scene.children[3].rotation.x = currentRotation.x
    scene.children[3].rotation.y = currentRotation.y
  }
  
  // 节点呼吸动画
  nodeMeshes.forEach((mesh, i) => {
    const scale = 1 + Math.sin(time * 2 + i * 0.5) * 0.08
    mesh.scale.set(scale, scale, scale)
    
    // 发光强度变化
    mesh.material.emissiveIntensity = 0.3 + Math.sin(time * 3 + i) * 0.15
  })
  
  // 外发光动画
  glowMeshes.forEach((mesh, i) => {
    const scale = 1.3 + Math.sin(time * 1.5 + i * 0.7) * 0.1
    mesh.scale.set(scale, scale, scale)
    mesh.material.opacity = 0.1 + Math.sin(time * 2 + i) * 0.05
  })
  
  // 脉冲环动画
  pulseRings.forEach((ring) => {
    const { phase } = ring.userData
    const pulseTime = (time * 1.5 + phase) % (Math.PI * 2)
    const scale = 1 + pulseTime * 0.3
    const opacity = Math.max(0, 0.4 - pulseTime * 0.15)
    
    ring.scale.set(scale, scale, scale)
    ring.material.opacity = opacity
    ring.lookAt(camera.position)
  })
  
  // 粒子流动
  particles.forEach(particle => {
    const { curve, speed } = particle.userData
    particle.userData.progress += speed
    if (particle.userData.progress > 1) {
      particle.userData.progress = 0
    }
    const point = curve.getPoint(particle.userData.progress)
    particle.position.copy(point)
    
    // 粒子大小变化
    const size = 0.06 + Math.sin(particle.userData.progress * Math.PI) * 0.04
    particle.scale.set(size / 0.06, size / 0.06, size / 0.06)
  })
  
  renderer.render(scene, camera)
}

function onResize() {
  const container = containerRef.value
  if (!container) return
  camera.aspect = container.clientWidth / container.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(container.clientWidth, container.clientHeight)
}

function onMouseDown(event) {
  isDragging = true
  autoRotate = false
  previousMousePosition = { x: event.clientX, y: event.clientY }
}

function onMouseUp() {
  isDragging = false
  // 3秒后恢复自动旋转
  setTimeout(() => {
    if (!isDragging) autoRotate = true
  }, 3000)
}

function onMouseMove(event) {
  const rect = canvasRef.value.getBoundingClientRect()
  
  // 拖拽旋转
  if (isDragging) {
    const deltaX = event.clientX - previousMousePosition.x
    const deltaY = event.clientY - previousMousePosition.y
    
    targetRotation.y += deltaX * 0.005
    targetRotation.x += deltaY * 0.005
    targetRotation.x = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, targetRotation.x))
    
    previousMousePosition = { x: event.clientX, y: event.clientY }
  }
  
  // 射线检测悬停
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  
  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObjects(nodeMeshes)
  
  if (intersects.length > 0) {
    const node = intersects[0].object.userData
    hoveredNode.value = node
    tooltipPos.value = {
      x: Math.min(event.clientX - rect.left + 20, rect.width - 250),
      y: Math.max(event.clientY - rect.top - 100, 10)
    }
  } else {
    hoveredNode.value = null
  }
}
</script>

<style scoped>
.card-pop-enter-active {
  animation: cardPopIn 0.25s ease-out;
}
.card-pop-leave-active {
  animation: cardPopOut 0.15s ease-in;
}

@keyframes cardPopIn {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(10px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes cardPopOut {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0.9);
  }
}
</style>
