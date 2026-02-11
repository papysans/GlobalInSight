import { defineStore } from 'pinia';
import { api } from '../api';

export const useStockNewsStore = defineStore('stockNews', {
    state: () => ({
        // 聚类模式数据
        clusters: [],
        rawCount: 0,
        crossPlatformCount: 0,
        sourceStats: {},
        categoryStats: {},
        collectionTime: '',
        fromCache: false,
        loading: false,
        error: null,
        selectedSource: 'all',
        selectedTopic: null,
    }),

    getters: {
        /** 按数据源筛选后的聚类列表 */
        filteredClusters(state) {
            let items = state.clusters;
            if (state.selectedSource !== 'all') {
                items = items.filter(c =>
                    (c.platform_ids || []).includes(state.selectedSource)
                );
            }
            return items;
        },

        /** 当前可用的数据源列表 */
        availableSources(state) {
            const sources = new Set();
            for (const c of state.clusters) {
                for (const pid of (c.platform_ids || [])) {
                    sources.add(pid);
                }
            }
            return Array.from(sources).sort();
        },

        /** 取前 N 条热点用于推演页面热搜标签 */
        trendingTopics(state) {
            return state.clusters.slice(0, 10).map(c => ({
                title: c.title,
                source: c.platform_label,
                category: c.category,
                heat: c.hot_value,
            }));
        },
    },

    actions: {
        async fetchNews(forceRefresh = false) {
            this.loading = true;
            this.error = null;
            try {
                const result = await api.getHotNews(forceRefresh);
                this.clusters = result.clusters || [];
                this.rawCount = result.raw_count || 0;
                this.crossPlatformCount = result.cross_platform_count || 0;
                this.sourceStats = result.source_stats || {};
                this.collectionTime = result.collection_time || '';
                this.fromCache = result.from_cache || false;
            } catch (err) {
                this.error = err.message;
                console.error('Failed to fetch hot news:', err);
            } finally {
                this.loading = false;
            }
        },

        selectTopic(topic) {
            this.selectedTopic = topic;
        },
    },
});
