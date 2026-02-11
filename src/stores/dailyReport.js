import { defineStore } from 'pinia';
import { api } from '../api';

/**
 * 每日速报状态管理
 * 管理速报生成、多平台预览、编辑和发布流程。
 */
export const useDailyReportStore = defineStore('dailyReport', {
    state: () => ({
        currentReport: null,
        reportHistory: [],
        isGenerating: false,
        isPublishing: false,
        platformStatuses: {
            xhs: 'idle',    // idle / publishing / published / failed
            weibo: 'idle',
            xueqiu: 'idle',
            zhihu: 'idle',
        },
        selectedPlatform: 'xhs',
        platformContents: {
            xhs: { title: '', body: '', images: [], tags: [], titleEmoji: '', titleTheme: '' },
            weibo: { title: '', body: '', images: [], tags: [] },
            xueqiu: { title: '', body: '', images: [], tags: [] },
            zhihu: { title: '', body: '', images: [], tags: [] },
        },
        isEditing: false,
        editableContent: {
            title: '',
            body: '',
            selectedImageIndices: [],
            imageOrder: [],
        },
        error: null,
    }),

    getters: {
        currentPlatformContent(state) {
            return state.platformContents[state.selectedPlatform] || {};
        },
    },

    actions: {
        /**
         * 手动触发速报生成，生成后为每个平台初始化内容副本
         */
        async generateReport() {
            this.isGenerating = true;
            this.error = null;
            try {
                const result = await api.generateDailyReport();
                const data = result.data || {};

                // 后端返回 { xhs: SocialContent, weibo: ..., ... }
                for (const [platform, content] of Object.entries(data)) {
                    if (this.platformContents[platform]) {
                        this.platformContents[platform] = {
                            title: content.title || '',
                            body: content.body || '',
                            images: content.image_urls || [],
                            tags: content.tags || [],
                            ...(platform === 'xhs' ? {
                                titleEmoji: content.title_emoji || '📊',
                                titleTheme: content.title_theme || 'cool',
                            } : {}),
                        };
                    }
                }

                // 取 xhs 作为 currentReport 的代表
                this.currentReport = data.xhs || data[Object.keys(data)[0]] || null;
                return result;
            } catch (err) {
                this.error = err.message;
                console.error('Failed to generate daily report:', err);
                throw err;
            } finally {
                this.isGenerating = false;
            }
        },

        async fetchLatest() {
            try {
                const result = await api.getDailyReportLatest();
                if (result.data) {
                    for (const [platform, content] of Object.entries(result.data)) {
                        if (this.platformContents[platform]) {
                            this.platformContents[platform] = {
                                title: content.title || '',
                                body: content.body || '',
                                images: content.image_urls || [],
                                tags: content.tags || [],
                                ...(platform === 'xhs' ? {
                                    titleEmoji: content.title_emoji || '📊',
                                    titleTheme: content.title_theme || 'cool',
                                } : {}),
                            };
                        }
                    }
                    this.currentReport = result.data.xhs || result.data[Object.keys(result.data)[0]] || null;
                }
                return result;
            } catch (err) {
                console.error('Failed to fetch latest report:', err);
                return null;
            }
        },

        async fetchHistory(limit = 20, offset = 0) {
            try {
                const result = await api.getDailyReportHistory(limit, offset);
                this.reportHistory = result.items || [];
                return result;
            } catch (err) {
                console.error('Failed to fetch report history:', err);
                return null;
            }
        },

        async publishAllPlatforms() {
            this.isPublishing = true;
            this.platformStatuses.xhs = 'publishing';
            try {
                const result = await api.publishDailyReportAllPlatforms();
                const results = result.results || {};
                for (const [platform, status] of Object.entries(results)) {
                    this.platformStatuses[platform] = status.status === 'published' ? 'published' : 'failed';
                }
                return result;
            } catch (err) {
                this.platformStatuses.xhs = 'failed';
                console.error('Failed to publish all platforms:', err);
                throw err;
            } finally {
                this.isPublishing = false;
            }
        },

        async publishToSinglePlatform(contentId, platform) {
            this.platformStatuses[platform] = 'publishing';
            try {
                if (platform === 'xhs') {
                    const result = await api.publishToXiaohongshu(contentId);
                    this.platformStatuses[platform] = result.success ? 'published' : 'failed';
                    return result;
                }
                // 非小红书平台暂不支持自动发布
                this.platformStatuses[platform] = 'idle';
                return { success: false, message: '该平台暂不支持自动发布，请使用复制到剪贴板功能' };
            } catch (err) {
                this.platformStatuses[platform] = 'failed';
                throw err;
            }
        },

        switchPlatform(platform) {
            this.selectedPlatform = platform;
            if (this.isEditing) {
                this.isEditing = false;
            }
        },

        startEditing() {
            this.isEditing = true;
            const current = this.platformContents[this.selectedPlatform];
            this.editableContent = {
                title: current.title || '',
                body: current.body || '',
                selectedImageIndices: current.images?.map((_, i) => i) || [],
                imageOrder: current.images?.map((_, i) => i) || [],
            };
        },

        /**
         * 更新当前平台的内容副本，不影响其他平台
         */
        updateContent(updates) {
            const platform = this.selectedPlatform;
            this.platformContents[platform] = {
                ...this.platformContents[platform],
                ...updates,
            };
            if (updates.title !== undefined) this.editableContent.title = updates.title;
            if (updates.body !== undefined) this.editableContent.body = updates.body;
        },

        /**
         * 从速报基础内容为每个平台生成初始内容副本
         */
        initPlatformContents(baseContent) {
            const platforms = ['xhs', 'weibo', 'xueqiu', 'zhihu'];
            for (const p of platforms) {
                this.platformContents[p] = {
                    title: baseContent.title || '',
                    body: baseContent.body || '',
                    images: baseContent.images || [],
                    tags: baseContent.tags || [],
                    ...(p === 'xhs' ? {
                        titleEmoji: baseContent.titleEmoji || '📊',
                        titleTheme: baseContent.titleTheme || 'cool',
                    } : {}),
                };
            }
        },
    },
});
