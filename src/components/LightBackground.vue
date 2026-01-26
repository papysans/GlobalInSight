<template>
  <div ref="containerRef" class="light-background"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const containerRef = ref(null)
let scene, camera, renderer, animationId
let particles, waves, floatingOrbs

// 初始化场景
function initScene() {
  scene = new THREE.Scene()
  
  // 相机
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
  camera.position.z = 50
  
  // 渲染器
  renderer = new THREE.WebGLRenderer({ 
    antialias: true, 
    alpha: true,
    powerPreference: 'high-performance'
  })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x000000, 0)
  containerRef.value.appendChild(renderer.domElement)
}

// 创建柔和粒子
function createParticles() {
  const geometry = new THREE.BufferGeometry()
  const count = 800
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)
  const sizes = new Float32Array(count)
  
  // 柔和的蓝紫色调
  const colorPalette = [
    new THREE.Color('#93c5fd'), // blue-300
    new THREE.Color('#c4b5fd'), // violet-300
    new THREE.Color('#a5b4fc'), // indigo-300
    new THREE.Color('#99f6e4'), // teal-200
    new THREE.Color('#fda4af'), // rose-300
  ]
  
  for (let i = 0; i < count; i++) {
    const i3 = i * 3
    positions[i3] = (Math.random() - 0.5) * 150
    positions[i3 + 1] = (Math.random() - 0.5) * 100
    positions[i3 + 2] = (Math.random() - 0.5) * 80
    
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
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true
  })
  
  particles = new THREE.Points(geometry, material)
  scene.add(particles)
}

// 创建波浪网格
function createWaves() {
  const geometry = new THREE.PlaneGeometry(200, 200, 50, 50)
  const material = new THREE.MeshBasicMaterial({
    color: 0x3b82f6,
    wireframe: true,
    transparent: true,
    opacity: 0.08
  })
  
  waves = new THREE.Mesh(geometry, material)
  waves.rotation.x = -Math.PI / 2.5
  waves.position.y = -30
  waves.position.z = -20
  scene.add(waves)
}

// 创建漂浮光球
function createFloatingOrbs() {
  floatingOrbs = []
  const orbColors = [0x60a5fa, 0xa78bfa, 0x34d399, 0xf472b6, 0xfbbf24]
  
  for (let i = 0; i < 8; i++) {
    const geometry = new THREE.SphereGeometry(Math.random() * 2 + 1, 32, 32)
    const material = new THREE.MeshBasicMaterial({
      color: orbColors[i % orbColors.length],
      transparent: true,
      opacity: 0.15
    })
    
    const orb = new THREE.Mesh(geometry, material)
    orb.position.set(
      (Math.random() - 0.5) * 100,
      (Math.random() - 0.5) * 60,
      (Math.random() - 0.5) * 40
    )
    orb.userData = {
      speed: Math.random() * 0.5 + 0.2,
      amplitude: Math.random() * 10 + 5,
      phase: Math.random() * Math.PI * 2
    }
    
    floatingOrbs.push(orb)
    scene.add(orb)
  }
}

// 动画循环
function animate() {
  animationId = requestAnimationFrame(animate)
  const time = Date.now() * 0.001
  
  // 粒子缓慢旋转和漂浮
  if (particles) {
    particles.rotation.y = time * 0.02
    particles.rotation.x = Math.sin(time * 0.1) * 0.05
    
    const positions = particles.geometry.attributes.position.array
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] += Math.sin(time + positions[i] * 0.01) * 0.01
    }
    particles.geometry.attributes.position.needsUpdate = true
  }
  
  // 波浪动画
  if (waves) {
    const positions = waves.geometry.attributes.position.array
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i]
      const y = positions[i + 1]
      positions[i + 2] = Math.sin(x * 0.05 + time) * 2 + Math.cos(y * 0.05 + time) * 2
    }
    waves.geometry.attributes.position.needsUpdate = true
  }
  
  // 光球漂浮
  floatingOrbs?.forEach((orb, i) => {
    const { speed, amplitude, phase } = orb.userData
    orb.position.y += Math.sin(time * speed + phase) * 0.02
    orb.position.x += Math.cos(time * speed * 0.5 + phase) * 0.01
    orb.scale.setScalar(1 + Math.sin(time * speed + phase) * 0.1)
  })
  
  renderer.render(scene, camera)
}

// 窗口大小调整
function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
}

onMounted(() => {
  initScene()
  createParticles()
  createWaves()
  createFloatingOrbs()
  animate()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  cancelAnimationFrame(animationId)
  
  // 清理资源
  scene?.traverse((object) => {
    if (object.geometry) object.geometry.dispose()
    if (object.material) {
      if (Array.isArray(object.material)) {
        object.material.forEach(m => m.dispose())
      } else {
        object.material.dispose()
      }
    }
  })
  
  renderer?.dispose()
  if (containerRef.value && renderer?.domElement) {
    containerRef.value.removeChild(renderer.domElement)
  }
})
</script>

<style scoped>
.light-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 30%, #ede9fe 70%, #fce7f3 100%);
}
</style>
