<template>
    <div class="bg-white shadow-sm rounded-xl p-4 border border-slate-100 h-full">
        <h2 class="text-lg font-semibold mb-3">多智能体思考流</h2>
        <div class="space-y-3 overflow-y-auto max-h-[70vh] pr-2">
            <div v-for="(log, idx) in logs" :key="idx" class="flex items-start space-x-3">
                <div
                    :class="['w-10 h-10 rounded-full flex items-center justify-center text-white font-bold', avatarColor(log.agent_name)]">
                    {{ initials(log.agent_name) }}
                </div>
                <div class="flex-1">
                    <div class="flex items-center space-x-2">
                        <span class="font-semibold" :class="textColor(log.agent_name)">{{ log.agent_name }}</span>
                        <span class="text-xs text-slate-400">{{ log.status }}</span>
                    </div>
                    <div class="text-sm text-slate-700 leading-relaxed mt-1 prose prose-sm max-w-none prose-slate"
                        v-html="renderMarkdown(log.step_content)"></div>
                </div>
            </div>
            <div v-if="isLoading" class="text-sm text-slate-400">流式更新中...</div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAnalysisStore } from '../stores/analysis';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();
const store = useAnalysisStore();
const logs = computed(() => store.logs);
const isLoading = computed(() => store.isLoading);

const renderMarkdown = (text) => {
    return md.render(text || '');
};

const avatarColor = (name) => {
    const map = {
        Reporter: 'bg-emerald-500',
        Analyst: 'bg-blue-500',
        Debater: 'bg-red-500',
        Writer: 'bg-purple-500',
        System: 'bg-slate-400',
    };
    return map[name] || 'bg-slate-500';
};

const textColor = (name) => {
    const map = {
        Analyst: 'text-blue-600',
        Debater: 'text-red-600',
        Reporter: 'text-emerald-600',
        Writer: 'text-purple-600',
        System: 'text-slate-500',
    };
    return map[name] || 'text-slate-700';
};

const initials = (name) => name?.[0] ?? 'A';
</script>
