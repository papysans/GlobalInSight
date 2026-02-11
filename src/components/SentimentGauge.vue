<template>
  <div class="sentiment-gauge" :class="[`sentiment-gauge--${size}`]">
    <v-chart :option="chartOption" :autoresize="true" :style="chartStyle" />
    <div v-if="size === 'full'" class="sentiment-gauge__details">
      <span class="sentiment-gauge__label" :style="{ color: labelColor }">{{ displayLabel }}</span>
    </div>
    <div v-if="size === 'mini'" class="sentiment-gauge__mini-label">
      <span class="text-xs font-semibold" :style="{ color: labelColor }">{{ displayLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { GaugeChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { TooltipComponent } from 'echarts/components';

use([CanvasRenderer, GaugeChart, TooltipComponent]);

const props = defineProps({
  indexValue: {
    type: Number,
    default: 50,
    validator: (v) => v >= 0 && v <= 100,
  },
  label: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'full',
    validator: (v) => ['mini', 'full'].includes(v),
  },
});

const displayLabel = computed(() => {
  if (props.label) return props.label;
  const v = props.indexValue;
  if (v <= 20) return '极度恐慌';
  if (v <= 40) return '恐慌';
  if (v <= 60) return '中性';
  if (v <= 80) return '贪婪';
  return '极度贪婪';
});

const labelColor = computed(() => {
  const v = props.indexValue;
  if (v <= 20) return '#dc2626';
  if (v <= 40) return '#ea580c';
  if (v <= 60) return '#ca8a04';
  if (v <= 80) return '#65a30d';
  return '#16a34a';
});

const chartStyle = computed(() => {
  if (props.size === 'mini') return { width: '90px', height: '70px' };
  return { width: '220px', height: '180px' };
});

const chartOption = computed(() => {
  const isMini = props.size === 'mini';

  return {
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 10,
        radius: isMini ? '90%' : '85%',
        center: ['50%', '60%'],
        axisLine: {
          lineStyle: {
            width: isMini ? 8 : 18,
            color: [
              [0.2, '#dc2626'],
              [0.4, '#ea580c'],
              [0.6, '#ca8a04'],
              [0.8, '#65a30d'],
              [1, '#16a34a'],
            ],
          },
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: isMini ? '50%' : '60%',
          width: isMini ? 4 : 8,
          offsetCenter: [0, '-10%'],
          itemStyle: {
            color: 'auto',
          },
        },
        axisTick: {
          show: !isMini,
          length: 6,
          lineStyle: { color: 'auto', width: 1 },
        },
        splitLine: {
          show: !isMini,
          length: 12,
          lineStyle: { color: 'auto', width: 2 },
        },
        axisLabel: {
          show: !isMini,
          distance: isMini ? 8 : 16,
          color: '#64748b',
          fontSize: 10,
          formatter: (value) => {
            if (value === 0 || value === 50 || value === 100) return value;
            return '';
          },
        },
        title: {
          show: false,
        },
        detail: {
          valueAnimation: true,
          fontSize: isMini ? 14 : 28,
          fontWeight: 'bold',
          offsetCenter: [0, isMini ? '20%' : '30%'],
          formatter: '{value}',
          color: 'auto',
        },
        data: [{ value: Math.round(props.indexValue) }],
      },
    ],
  };
});
</script>

<style scoped>
.sentiment-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sentiment-gauge--full {
  min-width: 220px;
}
.sentiment-gauge--mini {
  min-width: 90px;
}
.sentiment-gauge__details {
  margin-top: -8px;
  text-align: center;
}
.sentiment-gauge__label {
  font-size: 14px;
  font-weight: 700;
}
.sentiment-gauge__mini-label {
  margin-top: -6px;
  text-align: center;
}
</style>
