<template>
  <div class="bg-white shadow-sm rounded-xl p-4 border border-slate-100">
    <h2 class="text-lg font-semibold mb-3">输入新闻与主题</h2>
    <label class="block text-sm text-slate-600 mb-1">主题</label>
    <input v-model="topic"
      class="w-full rounded-lg border border-slate-200 px-3 py-2 mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
      placeholder="例如：全球 AI 监管格局" />

    <label class="block text-sm text-slate-600 mb-1">新闻链接（可多条）</label>
    <textarea v-model="urlsText" rows="4"
      class="w-full rounded-lg border border-slate-200 px-3 py-2 mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
      placeholder="一行一个链接"></textarea>

    <button @click="onStart" :disabled="isLoading"
      class="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 font-semibold transition disabled:opacity-60">
      {{ isLoading ? '分析中...' : '开始分析' }}
    </button>

    <div v-if="error" class="mt-3 text-sm text-red-600 bg-red-50 p-2 rounded border border-red-100">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useAnalysisStore } from '../stores/analysis';

const store = useAnalysisStore();
const topic = ref('');
const urlsText = ref('');

const isLoading = computed(() => store.isLoading);
const error = computed(() => store.error);

const onStart = async () => {
  const urls = urlsText.value
    .split('\n')
    .map((u) => u.trim())
    .filter(Boolean);
  await store.startAnalysis({ topic: topic.value, urls });
};
</script>
