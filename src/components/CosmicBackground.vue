<template>
  <div ref="containerRef" class="cosmic-background">
    <canvas ref="canvasRef" class="w-full h-full"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const containerRef = ref(null)
const canvasRef = ref(null)

let scene, camera, renderer, animationId
let stars, nebula, connections
let mouseX = 0, mouseY = 0

onMounted(() => {
  initScene()
  animate()
  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', onMouseMove)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('mousemove', onMouseMove)
  renderer?.dispose()
})

function initScene() {
  const container = containerRef.value
  const canvas = canvasRef.value
  
  // 场景
  scene = new THREE.Scene()
  
  // 相机
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000)
  camera.position.z = 500
  
  // 渲染器
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x0a0a1a, 1)
  
  // 创建星空
  createStars()
  
  // 创建星云
  createNebula()
  
  // 创建神经网络连接
  createNeuralNetwork()
  
  // 创建流动光线
  createFlowingLines()
}

function createStars() {
  const geometry = new THREE.BufferGeometry()
  const count = 3000
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)
  const sizes = new Float32Array(count)
  
  const colorPalette = [
    new THREE.Color(0x3b82f6), // blue
    new THREE.Color(0x8b5cf6), // purple
    new THREE.Color(0x10b981), // green
    new THREE.Color(0xf59e0b), // amber
    new THREE.Color(0xec4899), // pink
    new THREE.Color(0xffffff), // white
  ]
  
  for (let i = 0; i < count; i++) {
    const i3 = i * 3
    
    // 球形分布
    const radius = 300 + Math.random() * 700
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    
    positions[i3] = radius * Math.sin(phi) * Math.cos(theta)
    positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
    positions[i3 + 2] = radius * Math.cos(phi)
    
    // 随机颜色
    const color = colorPalette[Math.floor(Math.random() * colorPalette.length)]
    colors[i3] = color.r
    colors[i3 + 1] = color.g
    colors[i3 + 2] = color.b
    
    sizes[i] = Math.random() * 3 + 1
  }
  
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
  
  const material = new THREE.PointsMaterial({
    size: 2,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true
  })
  
  stars = new THREE.Points(geometry, material)
  scene.add(stars)
}

function createNebula() {
  // 多层星云效果
  const nebulaGroup = new THREE.Group()
  
  const nebulaColors = [
    { color: 0x3b82f6, opacity: 0.03 },
    { color: 0x8b5cf6, opacity: 0.025 },
    { color: 0xec4899, opacity: 0.02 },
  ]
  
  nebulaColors.forEach((config, index) => {
    const geometry = new THREE.SphereGeometry(200 + index * 100, 32, 32)
    const material = new THREE.MeshBasicMaterial({
      color: config.color,
      transparent: true,
      opacity: config.opacity,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.userData = { rotationSpeed: 0.0001 * (index + 1) }
    nebulaGroup.add(mesh)
  })
  
  nebula = nebulaGroup
  scene.add(nebula)
}

function createNeuralNetwork() {
  // 创建神经网络节点
  const nodeCount = 50
  const nodes = []
  const nodeGeometry = new THREE.SphereGeometry(3, 16, 16)
  
  const nodeColors = [0x3b82f6, 0x8b5cf6, 0x10b981, 0xf59e0b, 0xec4899]
  
  for (let i = 0; i < nodeCount; i++) {
    const material = new THREE.MeshBasicMaterial({
      color: nodeColors[i % nodeColors.length],
      transparent: true,
      opacity: 0.6
    })
    const node = new THREE.Mesh(nodeGeometry, material)
    
    // 随机位置
    node.position.set(
      (Math.random() - 0.5) * 600,
      (Math.random() - 0.5) * 400,
      (Math.random() - 0.5) * 300
    )
    
    node.userData = {
      originalPos: node.position.clone(),
      phase: Math.random() * Math.PI * 2,
      amplitude: 10 + Math.random() * 20
    }
    
    nodes.push(node)
    scene.add(node)
  }
  
  // 创建连接线
  const lineMaterial = new THREE.LineBasicMaterial({
    color: 0x3b82f6,
    transparent: true,
    opacity: 0.15,
    blending: THREE.AdditiveBlending
  })
  
  connections = []
  
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const distance = nodes[i].position.distanceTo(nodes[j].position)
      if (distance < 150) {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          nodes[i].position,
          nodes[j].position
        ])
        const line = new THREE.Line(geometry, lineMaterial.clone())
        line.userData = { nodeA: nodes[i], nodeB: nodes[j] }
        connections.push(line)
        scene.add(line)
      }
    }
  }
  
  // 保存节点引用
  scene.userData.nodes = nodes
}

function createFlowingLines() {
  // 创建流动的光线
  const lineCount = 12
  
  for (let i = 0; i < lineCount; i++) {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-400 + Math.random() * 100, (Math.random() - 0.5) * 300, -200),
      new THREE.Vector3(-100 + Math.random() * 100, (Math.random() - 0.5) * 300, 0),
      new THREE.Vector3(100 + Math.random() * 100, (Math.random() - 0.5) * 300, 100),
      new THREE.Vector3(400 + Math.random() * 100, (Math.random() - 0.5) * 300, -100),
    ])
    
    const points = curve.getPoints(100)
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    
    // 渐变透明度
    const alphas = new Float32Array(points.length)
    for (let j = 0; j < points.length; j++) {
      alphas[j] = Math.sin((j / points.length) * Math.PI) * 0.3
    }
    geometry.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1))
    
    const material = new THREE.LineBasicMaterial({
      color: [0x3b82f6, 0x8b5cf6, 0x10b981, 0xec4899, 0xf59e0b, 0x06b6d4][i % 6],
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending
    })
    
    const line = new THREE.Line(geometry, material)
    line.userData = {
      curve,
      phase: Math.random() * Math.PI * 2,
      speed: 0.001 + Math.random() * 0.002
    }
    scene.add(line)
  }
  
  // 创建光晕环
  createGlowRings()
  
  // 创建流星
  createShootingStars()
}

function createGlowRings() {
  const ringCount = 5
  const ringColors = [0x3b82f6, 0x8b5cf6, 0x10b981, 0xec4899, 0xf59e0b]
  
  for (let i = 0; i < ringCount; i++) {
    const geometry = new THREE.TorusGeometry(150 + i * 80, 1, 16, 100)
    const material = new THREE.MeshBasicMaterial({
      color: ringColors[i],
      transparent: true,
      opacity: 0.08,
      blending: THREE.AdditiveBlending
    })
    const ring = new THREE.Mesh(geometry, material)
    ring.rotation.x = Math.PI / 2 + (Math.random() - 0.5) * 0.5
    ring.rotation.y = Math.random() * Math.PI
    ring.userData = {
      rotationSpeed: 0.0003 * (i + 1) * (Math.random() > 0.5 ? 1 : -1),
      pulsePhase: Math.random() * Math.PI * 2
    }
    scene.add(ring)
    scene.userData.rings = scene.userData.rings || []
    scene.userData.rings.push(ring)
  }
}

function createShootingStars() {
  scene.userData.shootingStars = []
  
  for (let i = 0; i < 5; i++) {
    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(30 * 3) // 10 points trail
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    
    const material = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending
    })
    
    const shootingStar = new THREE.Line(geometry, material)
    shootingStar.userData = {
      active: false,
      progress: 0,
      startPos: new THREE.Vector3(),
      endPos: new THREE.Vector3(),
      delay: Math.random() * 10000
    }
    scene.add(shootingStar)
    scene.userData.shootingStars.push(shootingStar)
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)
  
  const time = Date.now() * 0.001
  
  // 星空旋转
  if (stars) {
    stars.rotation.y += 0.0002
    stars.rotation.x = Math.sin(time * 0.1) * 0.05
  }
  
  // 星云旋转
  if (nebula) {
    nebula.children.forEach(mesh => {
      mesh.rotation.y += mesh.userData.rotationSpeed
      mesh.rotation.x += mesh.userData.rotationSpeed * 0.5
    })
  }
  
  // 神经网络节点浮动
  if (scene.userData.nodes) {
    scene.userData.nodes.forEach(node => {
      const { originalPos, phase, amplitude } = node.userData
      node.position.y = originalPos.y + Math.sin(time + phase) * amplitude * 0.3
      node.position.x = originalPos.x + Math.cos(time * 0.5 + phase) * amplitude * 0.2
    })
  }
  
  // 更新连接线
  connections?.forEach(line => {
    const { nodeA, nodeB } = line.userData
    const positions = line.geometry.attributes.position.array
    positions[0] = nodeA.position.x
    positions[1] = nodeA.position.y
    positions[2] = nodeA.position.z
    positions[3] = nodeB.position.x
    positions[4] = nodeB.position.y
    positions[5] = nodeB.position.z
    line.geometry.attributes.position.needsUpdate = true
  })
  
  // 光晕环动画
  if (scene.userData.rings) {
    scene.userData.rings.forEach(ring => {
      ring.rotation.z += ring.userData.rotationSpeed
      ring.material.opacity = 0.05 + Math.sin(time + ring.userData.pulsePhase) * 0.03
    })
  }
  
  // 流星动画
  if (scene.userData.shootingStars) {
    scene.userData.shootingStars.forEach(star => {
      if (!star.userData.active) {
        star.userData.delay -= 16
        if (star.userData.delay <= 0) {
          // 激活流星
          star.userData.active = true
          star.userData.progress = 0
          star.userData.startPos.set(
            (Math.random() - 0.5) * 800,
            200 + Math.random() * 200,
            (Math.random() - 0.5) * 400
          )
          star.userData.endPos.set(
            star.userData.startPos.x + (Math.random() - 0.5) * 400,
            -200 - Math.random() * 100,
            star.userData.startPos.z + (Math.random() - 0.5) * 200
          )
          star.material.opacity = 0.8
        }
      } else {
        star.userData.progress += 0.015
        if (star.userData.progress >= 1) {
          star.userData.active = false
          star.userData.delay = 3000 + Math.random() * 8000
          star.material.opacity = 0
        } else {
          // 更新流星轨迹
          const positions = star.geometry.attributes.position.array
          for (let i = 0; i < 10; i++) {
            const t = Math.max(0, star.userData.progress - i * 0.02)
            const pos = new THREE.Vector3().lerpVectors(
              star.userData.startPos,
              star.userData.endPos,
              t
            )
            positions[i * 3] = pos.x
            positions[i * 3 + 1] = pos.y
            positions[i * 3 + 2] = pos.z
          }
          star.geometry.attributes.position.needsUpdate = true
          star.material.opacity = 0.8 * (1 - star.userData.progress * 0.5)
        }
      }
    })
  }
  
  // 相机跟随鼠标
  camera.position.x += (mouseX * 50 - camera.position.x) * 0.02
  camera.position.y += (-mouseY * 30 - camera.position.y) * 0.02
  camera.lookAt(scene.position)
  
  renderer.render(scene, camera)
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
}

function onMouseMove(event) {
  mouseX = (event.clientX / window.innerWidth) * 2 - 1
  mouseY = (event.clientY / window.innerHeight) * 2 - 1
}
</script>


<style scoped>
.cosmic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}
</style>
