<template>
    <div class="bg-white shadow-lg rounded-3xl border border-slate-100 p-4 max-w-md mx-auto">
        <div class="bg-slate-50 rounded-2xl p-4 min-h-[300px]">
            <div class="text-xs text-slate-400 mb-2">小红书预览</div>
            <h3 class="text-lg font-bold mb-3" v-if="finalCopy.title">{{ finalCopy.title }}</h3>
            <p class="text-sm text-slate-700 whitespace-pre-line leading-relaxed">{{ finalCopy.body || '等待生成...' }}</p>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAnalysisStore } from '../stores/analysis';

const store = useAnalysisStore();
const finalCopy = computed(() => store.finalCopy);
</script>
