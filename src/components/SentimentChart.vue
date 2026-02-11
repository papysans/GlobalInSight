<template>
  <div class="sentiment-chart">
    <!-- Time range selector -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex gap-1">
        <button
          v-for="range in timeRanges"
          :key="range.days"
          class="px-3 py-1 rounded-full border text-xs font-semibold transition-colors"
          :class="selectedDays === range.days
            ? 'bg-blue-50 border-blue-300 text-blue-600'
            : 'border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600'"
          @click="selectedDays = range.days"
        >
          {{ range.label }}
        </button>
      </div>
      <div v-if="showSubScores" class="flex gap-1 flex-wrap">
        <button
          v-for="series in subScoreSeries"
          :key="series.key"
          class="px-2 py-0.5 rounded-full border text-xs transition-colors"
          :class="visibleSeries.has(series.key)
            ? 'border-current font-semibold'
            : 'border-slate-200 text-slate-400'"
          :style="visibleSeries.has(series.key) ? { color: series.color, borderColor: series.color } : {}"
          @click="toggleSeries(series.key)"
        >
          {{ series.label }}
        </button>
      </div>
    </div>
    <!-- Chart -->
    <v-chart :option="chartOption" :autoresize="true" style="width: 100%; height: 320px;" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import {
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkPointComponent,
  VisualMapComponent,
  LegendComponent,
} from 'echarts/components';

use([
  CanvasRenderer,
  LineChart,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  MarkPointComponent,
  VisualMapComponent,
  LegendComponent,
]);

const props = defineProps({
  historyData: {
    type: Array,
    default: () => [],
  },
  stockCode: {
    type: String,
    default: null,
  },
  showSubScores: {
    type: Boolean,
    default: false,
  },
});

const timeRanges = [
  { days: 7, label: '7天' },
  { days: 14, label: '14天' },
  { days: 30, label: '30天' },
];

const selectedDays = ref(30);

const subScoreSeries = [
  { key: 'comment_sentiment_score', label: '评论情绪', color: '#3b82f6' },
  { key: 'baidu_vote_score', label: '百度投票', color: '#f59e0b' },
  { key: 'akshare_aggregate_score', label: 'AKShare', color: '#8b5cf6' },
  { key: 'news_sentiment_score', label: '新闻情绪', color: '#06b6d4' },
  { key: 'margin_trading_score', label: '融资融券', color: '#ec4899' },
];

const visibleSeries = ref(new Set(['comment_sentiment_score']));

function toggleSeries(key) {
  const s = new Set(visibleSeries.value);
  if (s.has(key)) {
    s.delete(key);
  } else {
    s.add(key);
  }
  visibleSeries.value = s;
}

const filteredData = computed(() => {
  if (!props.historyData || props.historyData.length === 0) return [];
  const cutoff = Date.now() - selectedDays.value * 24 * 60 * 60 * 1000;
  return props.historyData.filter((item) => {
    const t = new Date(item.snapshot_time || item.time).getTime();
    return t >= cutoff;
  });
});

const chartOption = computed(() => {
  const data = filteredData.value;
  const times = data.map((d) => d.snapshot_time || d.time);
  const indexValues = data.map((d) => d.index_value ?? d.value ?? 0);

  // Find key event points (index > 80 or < 20)
  const markPoints = [];
  data.forEach((d, i) => {
    const v = d.index_value ?? d.value ?? 0;
    if (v > 80 || v < 20) {
      markPoints.push({
        coord: [times[i], v],
        value: Math.round(v),
        itemStyle: { color: v > 80 ? '#16a34a' : '#dc2626' },
        symbol: 'pin',
        symbolSize: 36,
      });
    }
  });

  // Build series array
  const series = [
    {
      name: '综合指数',
      type: 'line',
      data: indexValues,
      smooth: true,
      lineStyle: { width: 2.5, color: '#3b82f6' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59,130,246,0.15)' },
            { offset: 1, color: 'rgba(59,130,246,0.01)' },
          ],
        },
      },
      itemStyle: { color: '#3b82f6' },
      markPoint: markPoints.length > 0 ? { data: markPoints, label: { fontSize: 10, color: '#fff' } } : undefined,
    },
  ];

  // Add sub-score series if enabled
  if (props.showSubScores) {
    subScoreSeries.forEach((ss) => {
      if (!visibleSeries.value.has(ss.key)) return;
      series.push({
        name: ss.label,
        type: 'line',
        data: data.map((d) => d[ss.key] ?? null),
        smooth: true,
        lineStyle: { width: 1.5, color: ss.color, type: 'dashed' },
        itemStyle: { color: ss.color },
        symbol: 'none',
      });
    });
  }

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155', fontSize: 12 },
      formatter: (params) => {
        if (!params || params.length === 0) return '';
        const idx = params[0].dataIndex;
        const item = data[idx];
        if (!item) return '';
        const time = times[idx];
        let html = `<div style="font-weight:600;margin-bottom:4px">${time}</div>`;
        params.forEach((p) => {
          if (p.value != null) {
            html += `<div style="display:flex;align-items:center;gap:4px">`;
            html += `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>`;
            html += `<span>${p.seriesName}: <b>${Math.round(p.value)}</b></span></div>`;
          }
        });
        if (item.sample_count != null) {
          html += `<div style="color:#94a3b8;font-size:11px;margin-top:4px">样本量: ${item.sample_count}</div>`;
        }
        if (item.representative_comment) {
          const comment = item.representative_comment.length > 40
            ? item.representative_comment.slice(0, 40) + '...'
            : item.representative_comment;
          html += `<div style="color:#94a3b8;font-size:11px;margin-top:2px">"${comment}"</div>`;
        }
        return html;
      },
    },
    grid: {
      left: 45,
      right: 20,
      top: 20,
      bottom: 60,
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: {
        fontSize: 10,
        color: '#94a3b8',
        formatter: (val) => {
          if (!val) return '';
          const d = new Date(val);
          return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')}`;
        },
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitNumber: 5,
      axisLabel: { fontSize: 10, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 20,
        bottom: 8,
        borderColor: '#e2e8f0',
        fillerColor: 'rgba(59,130,246,0.1)',
        handleStyle: { color: '#3b82f6' },
      },
    ],
    visualMap: {
      show: false,
      pieces: [
        { gte: 0, lt: 20, color: '#dc2626' },
        { gte: 20, lt: 40, color: '#ea580c' },
        { gte: 40, lt: 60, color: '#ca8a04' },
        { gte: 60, lt: 80, color: '#65a30d' },
        { gte: 80, lte: 100, color: '#16a34a' },
      ],
      seriesIndex: 0,
      dimension: 1,
    },
    series,
  };
});
</script>

<style scoped>
.sentiment-chart {
  width: 100%;
}
</style>
