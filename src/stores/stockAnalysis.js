import { defineStore } from 'pinia';
import { api } from '../api';

/**
 * 行情推演与内容生成状态管理
 * 合并推演 + 社交内容，因为内容生成集成在推演页面中。
 * 复用现有 analysis store 的 SSE 处理模式和编辑模式逻辑。
 */
export const useStockAnalysisStore = defineStore('stockAnalysis', {
    state: () => ({
        // 推演相关
        currentAnalysis: null,
        analysisSteps: [],
        isAnalyzing: false,
        history: [],
        error: null,

        // 内容生成相关
        finalCopy: { title: '', body: '' },
        selectedPlatform: 'xhs',
        imageUrls: [],
        titleEmoji: '🤔',
        titleTheme: 'cool',

        // 编辑模式
        isEditing: false,
        editableContent: {
            title: '',
            body: '',
            selectedImageIndices: [0],
            imageOrder: [0],
        },

        // 多平台内容副本
        platformContents: {
            xhs: { title: '', body: '', images: [], tags: [], titleEmoji: '', titleTheme: '' },
            weibo: { title: '', body: '', images: [], tags: [] },
            xueqiu: { title: '', body: '', images: [], tags: [] },
            zhihu: { title: '', body: '', images: [], tags: [] },
        },

        // 发布相关
        isPublishing: false,
        contentHistory: [],
    }),

    getters: {
        currentPlatformContent(state) {
            return state.platformContents[state.selectedPlatform] || {};
        },
    },

    actions: {
        /**
         * SSE 流式推演
         * @param {Object} payload - { topic, debate_rounds }
         */
        async startAnalysis(payload) {
            // 清空旧数据
            this.analysisSteps = [];
            this.currentAnalysis = null;
            this.finalCopy = { title: '', body: '' };
            this.imageUrls = [];
            this.titleEmoji = '🤔';
            this.titleTheme = 'cool';
            this.isAnalyzing = true;
            this.error = null;
            this.isEditing = false;
            this.editableContent = { title: '', body: '', selectedImageIndices: [0], imageOrder: [0] };
            this._resetPlatformContents();

            try {
                await api.analyzeStock(payload, (data) => {
                    this.analysisSteps = [...this.analysisSteps, data];

                    // 解析 Writer 输出
                    if (data.agent_name === 'Writer' && data.step_content) {
                        this._parseWriterOutput(data.step_content);
                    }

                    // 解析配图
                    if (data.agent_name === 'ImageGenerator' && data.step_content) {
                        try {
                            const urls = JSON.parse(data.step_content);
                            if (Array.isArray(urls)) this.imageUrls = urls;
                        } catch { /* ignore parse errors */ }
                    }

                    // 推演完成
                    if (data.status === 'completed') {
                        this.currentAnalysis = data;
                    }
                });
            } catch (err) {
                if (err.name !== 'AbortError') {
                    this.error = err.message;
                    console.error('Stock analysis failed:', err);
                }
            } finally {
                this.isAnalyzing = false;
            }
        },

        stopAnalysis() {
            api.abortAnalysis();
            this.isAnalyzing = false;
        },

        async fetchHistory(limit = 20, offset = 0) {
            try {
                const result = await api.getStockAnalysisHistory(limit, offset);
                this.history = result.items || [];
            } catch (err) {
                console.error('Failed to fetch analysis history:', err);
            }
        },

        async fetchDetail(analysisId) {
            try {
                const result = await api.getStockAnalysisDetail(analysisId);
                this.currentAnalysis = result.data || null;
                return result.data;
            } catch (err) {
                console.error('Failed to fetch analysis detail:', err);
                return null;
            }
        },

        // ========== 内容生成 ==========

        /**
         * 生成社交内容，结果存入 platformContents[platform]
         */
        async generateContent(analysisId, platform) {
            try {
                const result = await api.generateSocialContent(analysisId, platform);
                const content = result.data;
                if (content) {
                    this.platformContents[platform] = {
                        title: content.title || '',
                        body: content.body || '',
                        images: content.image_urls || [],
                        tags: content.tags || [],
                        ...(platform === 'xhs' ? {
                            titleEmoji: content.title_emoji || this.titleEmoji,
                            titleTheme: content.title_theme || this.titleTheme,
                        } : {}),
                    };
                }
                return content;
            } catch (err) {
                console.error(`Failed to generate ${platform} content:`, err);
                throw err;
            }
        },

        async publishToXhs(contentId) {
            this.isPublishing = true;
            try {
                const result = await api.publishToXiaohongshu(contentId);
                return result;
            } catch (err) {
                console.error('Failed to publish to XHS:', err);
                throw err;
            } finally {
                this.isPublishing = false;
            }
        },

        // ========== 多平台预览 ==========

        switchPlatform(platform) {
            this.selectedPlatform = platform;
            if (this.isEditing) {
                // 切换平台时退出编辑模式
                this.isEditing = false;
            }
        },

        /**
         * 从推演结果为每个平台生成初始内容副本
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
                        titleEmoji: baseContent.titleEmoji || this.titleEmoji,
                        titleTheme: baseContent.titleTheme || this.titleTheme,
                    } : {}),
                };
            }
        },

        // ========== 编辑模式 ==========

        startEditing() {
            this.isEditing = true;
            this._originalContent = JSON.parse(JSON.stringify(this.editableContent));
            const current = this.platformContents[this.selectedPlatform];
            this.editableContent = {
                title: current.title || this.finalCopy.title || '',
                body: current.body || this.finalCopy.body || '',
                selectedImageIndices: current.images?.map((_, i) => i) || [0],
                imageOrder: current.images?.map((_, i) => i) || [0],
            };
        },

        /**
         * 更新单个 editableContent 字段（CopywritingEditor 兼容）
         */
        updateEditableContent(field, value) {
            this.editableContent[field] = value;
        },

        /**
         * 保存编辑（CopywritingEditor 兼容）
         */
        saveEditing() {
            this.isEditing = false;
            this.finalCopy = {
                title: this.editableContent.title,
                body: this.editableContent.body,
            };
            // 同步到当前平台内容
            const platform = this.selectedPlatform;
            this.platformContents[platform] = {
                ...this.platformContents[platform],
                title: this.editableContent.title,
                body: this.editableContent.body,
            };
        },

        /**
         * 取消编辑（CopywritingEditor 兼容）
         */
        cancelEditing() {
            this.isEditing = false;
            if (this._originalContent) {
                this.editableContent = JSON.parse(JSON.stringify(this._originalContent));
            }
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
            // 同步到 editableContent
            if (updates.title !== undefined) this.editableContent.title = updates.title;
            if (updates.body !== undefined) this.editableContent.body = updates.body;
        },

        // ========== 内部辅助 ==========

        _resetPlatformContents() {
            this.platformContents = {
                xhs: { title: '', body: '', images: [], tags: [], titleEmoji: '', titleTheme: '' },
                weibo: { title: '', body: '', images: [], tags: [] },
                xueqiu: { title: '', body: '', images: [], tags: [] },
                zhihu: { title: '', body: '', images: [], tags: [] },
            };
        },

        _parseWriterOutput(raw) {
            let clean = raw.replace(/(?:^|\n)Writer:\s*/gi, '').trim();
            let title = '生成文案';
            let body = clean;

            if (clean.includes('TITLE:')) {
                const titleMatch = clean.match(/TITLE:\s*(.+?)(?=\s*(?:EMOJI:|THEME:|CONTENT:|$))/is);
                if (titleMatch?.[1]) title = titleMatch[1].trim();

                const emojiMatch = clean.match(/EMOJI:\s*(.+?)(?=\s*(?:THEME:|CONTENT:|$))/is);
                if (emojiMatch?.[1]) this.titleEmoji = emojiMatch[1].trim();

                const themeMatch = clean.match(/THEME:\s*(warm|peach|sunset|cool|ocean|mint|sky|lavender|grape|forest|lime|alert|dark|cream)/i);
                if (themeMatch?.[1]) this.titleTheme = themeMatch[1].toLowerCase();

                const contentMatch = clean.match(/CONTENT:\s*([\s\S]+)$/i);
                if (contentMatch?.[1]) {
                    body = contentMatch[1].trim();
                } else {
                    body = clean
                        .replace(/TITLE:\s*.+?(?=\s*(?:EMOJI:|THEME:|CONTENT:|$))/is, '')
                        .replace(/EMOJI:\s*.+?(?=\s*(?:THEME:|CONTENT:|$))/is, '')
                        .replace(/THEME:\s*(?:warm|peach|sunset|cool|ocean|mint|sky|lavender|grape|forest|lime|alert|dark|cream)/i, '')
                        .trim();
                }
            }

            this.finalCopy = { title, body };
            this.editableContent = {
                title,
                body,
                selectedImageIndices: [0],
                imageOrder: [0],
            };
        },
    },
});
