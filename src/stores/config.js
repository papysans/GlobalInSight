import { defineStore } from 'pinia';
import { api } from '../api';

export const useConfigStore = defineStore('config', {
    state: () => ({
        config: null,
        loading: false,
        error: null,
        modelsByProvider: null, // 缓存的模型列表
        modelsCacheTime: null, // 缓存时间戳
        darkMode: localStorage.getItem('grandchart_dark_mode') === 'true', // 深色模式
    }),

    getters: {
        llmProviders: (state) => (state.config && state.config.llm_providers) || {},
        crawlerLimits: (state) => (state.config && state.config.crawler_limits) || {},
        debateMaxRounds: (state) => (state.config && state.config.debate_max_rounds) || 4,
        defaultPlatforms: (state) => (state.config && state.config.default_platforms) || [],
        isDarkMode: (state) => state.darkMode,
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
        // 获取指定提供商的模型列表
        getModelsForProvider: (state) => (providerKey) => {
            if (!state.modelsByProvider) return [];
            return state.modelsByProvider[providerKey] || [];
        },
        // 获取指定提供商的默认模型
        getDefaultModel: (state) => (providerKey) => {
            if (!state.modelsByProvider) return null;
            const models = state.modelsByProvider[providerKey] || [];
            const defaultModel = models.find(m => m.is_default);
            return defaultModel ? defaultModel.id : (models[0] ? models[0].id : null);
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

        // 缓存模型列表
        cacheModels(models) {
            this.modelsByProvider = models;
            this.modelsCacheTime = Date.now();
            // 保存到 localStorage（24小时有效期）
            localStorage.setItem('grandchart_models_cache', JSON.stringify({
                models,
                timestamp: this.modelsCacheTime
            }));
        },

        // 加载缓存的模型列表
        loadCachedModels() {
            const cached = localStorage.getItem('grandchart_models_cache');
            if (cached) {
                try {
                    const { models, timestamp } = JSON.parse(cached);
                    const age = Date.now() - timestamp;
                    const maxAge = 24 * 60 * 60 * 1000; // 24小时
                    
                    if (age < maxAge) {
                        this.modelsByProvider = models;
                        this.modelsCacheTime = timestamp;
                        return true;
                    }
                } catch (e) {
                    console.error('Failed to load cached models:', e);
                }
            }
            return false;
        },

        // 获取模型列表（优先使用缓存）
        async fetchModels(forceRefresh = false) {
            // 如果不强制刷新，先尝试加载缓存
            if (!forceRefresh && this.loadCachedModels()) {
                return this.modelsByProvider;
            }

            // 从后端获取最新模型列表
            try {
                const models = await api.getModels();
                this.cacheModels(models);
                return models;
            } catch (err) {
                console.error('Failed to fetch models:', err);
                // 如果获取失败但有缓存，使用缓存
                if (this.modelsByProvider) {
                    return this.modelsByProvider;
                }
                throw err;
            }
        },

        // 切换深色模式
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('grandchart_dark_mode', this.darkMode.toString());
            this.applyDarkMode();
        },

        // 设置深色模式
        setDarkMode(value) {
            this.darkMode = value;
            localStorage.setItem('grandchart_dark_mode', value.toString());
            this.applyDarkMode();
        },

        // 应用深色模式到 DOM
        applyDarkMode() {
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },

        // 初始化深色模式（应用启动时调用）
        initDarkMode() {
            this.applyDarkMode();
        },
    },
});