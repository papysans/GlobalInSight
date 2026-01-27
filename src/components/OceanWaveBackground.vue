<template>
  <div ref="containerRef" class="ocean-wave-background"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const containerRef = ref(null)
let scene, camera, renderer, animationId
let particles = []
let count = 0

// 配置参数
const SEPARATION = 50  // 粒子间距
const AMOUNTX = 60     // X 轴粒子数量
const AMOUNTY = 30     // Y 轴粒子数量

// 初始化场景
function initScene() {
  scene = new THREE.Scene()
  
  // 相机设置 - 俯视角度看海浪
  camera = new THREE.PerspectiveCamera(120, window.innerWidth / window.innerHeight, 1, 10000)
  camera.position.y = 180  // 高度
  camera.position.z = 20   // 距离
  camera.rotation.x = 0.35 // 俯视角度
  
  // 渲染器
  renderer = new THREE.WebGLRenderer({ 
    antialias: true, 
    alpha: true 
  })
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x000000, 0)
  containerRef.value.appendChild(renderer.domElement)
}

// 创建粒子波浪
function createParticles() {
  // 粒子材质 - 蓝色系
  const geometry = new THREE.SphereGeometry(1, 8, 8)
  const material = new THREE.MeshBasicMaterial({ 
    color: 0x60a5fa,  // 蓝色
    transparent: true,
    opacity: 0.8
  })
  
  let i = 0
  for (let ix = 0; ix < AMOUNTX; ix++) {
    for (let iy = 0; iy < AMOUNTY; iy++) {
      const particle = new THREE.Mesh(geometry, material.clone())
      
      // 设置粒子位置
      particle.position.x = ix * SEPARATION - ((AMOUNTX * SEPARATION) / 2)
      particle.position.z = iy * SEPARATION - ((AMOUNTY * SEPARATION) - 10)
      
      // 根据位置设置不同的蓝色调
      const colorVariation = (ix / AMOUNTX) * 0.3
      particle.material.color.setHSL(0.55 + colorVariation * 0.1, 0.8, 0.5 + colorVariation)
      
      particles.push(particle)
      scene.add(particle)
      i++
    }
  }
}

// 动画循环
function animate() {
  animationId = requestAnimationFrame(animate)
  render()
}

// 渲染函数 - 波浪动画
function render() {
  let i = 0
  
  for (let ix = 0; ix < AMOUNTX; ix++) {
    for (let iy = 0; iy < AMOUNTY; iy++) {
      const particle = particles[i++]
      
      // 正弦波计算高度 - 创造波浪效果
      particle.position.y = 
        (Math.sin((ix + count) * 0.5) * 15) + 
        (Math.sin((iy + count) * 0.5) * 15)
      
      // 粒子大小随波浪变化
      const scale = 
        (Math.sin((ix + count) * 0.5) + 2) * 4 + 
        (Math.sin((iy + count) * 0.5) + 1) * 4
      particle.scale.set(scale, scale, scale)
    }
  }
  
  renderer.render(scene, camera)
  
  // 控制波浪速度
  count += 0.05
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
  animate()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  cancelAnimationFrame(animationId)
  
  // 清理资源
  particles.forEach(particle => {
    if (particle.geometry) particle.geometry.dispose()
    if (particle.material) particle.material.dispose()
    scene.remove(particle)
  })
  particles = []
  
  renderer?.dispose()
  if (containerRef.value && renderer?.domElement) {
    containerRef.value.removeChild(renderer.domElement)
  }
})
</script>

<style scoped>
.ocean-wave-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 50%, #ffffff 100%);
}
</style>
