<template>
  <div class="absolute inset-0 -z-10">
    <vue-particles
      id="tsparticles"
      :options="particlesOptions"
      @particles-loaded="onParticlesLoaded"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const particlesOptions = ref({
  background: {
    color: {
      value: 'transparent'
    }
  },
  fpsLimit: 60,
  interactivity: {
    events: {
      onHover: {
        enable: true,
        mode: 'grab'
      },
      onClick: {
        enable: true,
        mode: 'push'
      },
      resize: true
    },
    modes: {
      grab: {
        distance: 140,
        links: {
          opacity: 0.5
        }
      },
      push: {
        quantity: 4
      }
    }
  },
  particles: {
    color: {
      value: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899']
    },
    links: {
      color: '#64748b',
      distance: 150,
      enable: true,
      opacity: 0.2,
      width: 1
    },
    move: {
      direction: 'none',
      enable: true,
      outModes: {
        default: 'bounce'
      },
      random: false,
      speed: 1,
      straight: false
    },
    number: {
      density: {
        enable: true,
        area: 800
      },
      value: 60
    },
    opacity: {
      value: 0.5
    },
    shape: {
      type: 'circle'
    },
    size: {
      value: { min: 1, max: 3 }
    }
  },
  detectRetina: true
})

const onParticlesLoaded = (container) => {
  console.log('Particles loaded', container)
}
</script>
