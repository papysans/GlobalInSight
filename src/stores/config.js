import { defineStore } from 'pinia';
import { api } from '../api';

export const useConfigStore = defineStore('config', {
    state: () => ({
        config: null,
        loading: false,
        error: null,
    }),

    getters: {
        llmProviders: (state) => (state.config && state.config.llm_providers) || {},
        crawlerLimits: (state) => (state.config && state.config.crawler_limits) || {},
        debateMaxRounds: (state) => (state.config && state.config.debate_max_rounds) || 4,
        defaultPlatforms: (state) => (state.config && state.config.default_platforms) || [],
        getUserApis: () => {
            const saved = localStorage.getItem('grandchart_user_apis_v2');
            if (saved) {
                try {
                    return JSON.parse(saved);
                } catch (e) {
                    return [];
                }
            }
            return [];
        },
    },

    actions: {
        async fetchConfig() {
            this.loading = true;
            this.error = null;
            try {
                this.config = await api.getConfig();
            } catch (err) {
                this.error = err.message;
                console.error('Failed to fetch config:', err);
            } finally {
                this.loading = false;
            }
        },

        async updateConfig(updates) {
            this.loading = true;
            this.error = null;
            try {
                const result = await api.updateConfig(updates);
                // 更新本地配置
                if (this.config) {
                    if (updates.debate_max_rounds !== undefined) {
                        this.config.debate_max_rounds = updates.debate_max_rounds;
                    }
                    if (updates.crawler_limits) {
                        Object.assign(this.config.crawler_limits, updates.crawler_limits);
                    }
                    if (updates.default_platforms) {
                        this.config.default_platforms = updates.default_platforms;
                    }
                }
                return result;
            } catch (err) {
                this.error = err.message;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        saveUserApis(apis) {
            localStorage.setItem('grandchart_user_apis_v2', JSON.stringify(apis));
        },
    },
});