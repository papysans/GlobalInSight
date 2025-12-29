<template>
    <div class="min-h-screen p-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="col-span-1">
            <NewsInput />
        </div>
        <div class="col-span-1 lg:col-span-1">
            <ThinkingChain />
        </div>
        <div class="col-span-1">
            <XiaohongshuCard />
        </div>
    </div>
</template>

<script setup>
import NewsInput from './components/NewsInput.vue';
import ThinkingChain from './components/ThinkingChain.vue';
import XiaohongshuCard from './components/XiaohongshuCard.vue';
</script>
