import { defineStore } from "pinia";
import { api } from "../api";
import { useWorkflowStore } from "./workflow";

export const useAnalysisStore = defineStore("analysis", {
    state: () => {
        // 从 localStorage 恢复平台选择
        const loadPlatformsFromStorage = () => {
            const saved = localStorage.getItem("grandchart_selected_platforms");
            if (saved) {
                try {
                    const platforms = JSON.parse(saved);
                    if (Array.isArray(platforms) && platforms.length > 0) {
                        return platforms;
                    }
                } catch (e) {
                    console.error(
                        "Failed to load platform selection from localStorage:",
                        e
                    );
                }
            }
            return [];
        };

        // 从 sessionStorage 恢复分析结果（页面导航时保留）
        const loadResultsFromSession = () => {
            const saved = sessionStorage.getItem("grandchart_analysis_results");
            if (saved) {
                try {
                    return JSON.parse(saved);
                } catch (e) {
                    console.error("Failed to load analysis results from sessionStorage:", e);
                }
            }
            return null;
        };

        const cachedResults = loadResultsFromSession();

        return {
            logs: cachedResults?.logs || [],
            finalCopy: cachedResults?.finalCopy || { title: "", body: "" },
            isLoading: false,
            error: null,
            selectedPlatforms: loadPlatformsFromStorage(), // 从 localStorage 恢复选中的平台
            insight: cachedResults?.insight || "", // 核心洞察
            insightTitle: cachedResults?.insightTitle || "", // 洞察标题
            insightSubtitle: cachedResults?.insightSubtitle || "", // 洞察副标题
            contrastData: cachedResults?.contrastData || null, // 舆论对比数据
            dataUnlocked: cachedResults?.dataUnlocked || false, // 数据是否解锁
            imageUrls: cachedResults?.imageUrls || [], // 生成的配图 URL
            titleEmoji: cachedResults?.titleEmoji || "🤔", // Title Card emoji (default)
            titleTheme: cachedResults?.titleTheme || "cool", // Title Card color theme: warm/cool/alert/dark
            
            // 编辑状态
            isEditing: false,
            editableContent: {
                title: cachedResults?.finalCopy?.title || "",
                body: cachedResults?.finalCopy?.body || "",
                selectedImageIndices: cachedResults?.selectedImageIndices || [0], // 默认选中标题卡（索引0）
                imageOrder: cachedResults?.imageOrder || [0], // 默认顺序
            },
            originalContent: null, // 用于取消时恢复
        };
    },

    getters: {
        availablePlatforms: () => [
            { code: "wb", name: "微博" },
            { code: "bili", name: "B站" },
            { code: "xhs", name: "小红书" },
            { code: "dy", name: "抖音" },
            { code: "ks", name: "快手" },
            { code: "tieba", name: "贴吧" },
            { code: "zhihu", name: "知乎" },
            { code: "hn", name: "Hacker News" },
        ],
    },

    actions: {
        setSelectedPlatforms(platforms) {
            this.selectedPlatforms = platforms;
            // 同步到 localStorage
            if (platforms && platforms.length > 0) {
                localStorage.setItem(
                    "grandchart_selected_platforms",
                    JSON.stringify(platforms)
                );
            } else {
                localStorage.removeItem("grandchart_selected_platforms");
            }
        },

        // 保存分析结果到 sessionStorage（页面导航时保留）
        saveResultsToSession() {
            const results = {
                logs: this.logs,
                finalCopy: this.finalCopy,
                insight: this.insight,
                insightTitle: this.insightTitle,
                insightSubtitle: this.insightSubtitle,
                contrastData: this.contrastData,
                dataUnlocked: this.dataUnlocked,
                imageUrls: this.imageUrls,
                titleEmoji: this.titleEmoji,
                titleTheme: this.titleTheme,
                selectedImageIndices: this.editableContent.selectedImageIndices,
                imageOrder: this.editableContent.imageOrder,
            };
            try {
                sessionStorage.setItem("grandchart_analysis_results", JSON.stringify(results));
            } catch (e) {
                console.error("Failed to save analysis results to sessionStorage:", e);
            }
        },

        // 编辑相关 actions
        startEditing() {
            this.isEditing = true;
            // 备份原始内容
            this.originalContent = JSON.parse(JSON.stringify(this.editableContent));
            console.log('[AnalysisStore] 开始编辑模式');
        },

        updateEditableContent(field, value) {
            this.editableContent[field] = value;
            // 自动保存到 localStorage
            this.saveEditDraft();
        },

        saveEditing() {
            this.isEditing = false;
            // 更新 finalCopy
            this.finalCopy = {
                title: this.editableContent.title,
                body: this.editableContent.body,
            };
            this.saveEditDraft();
            this.saveResultsToSession();
            console.log('[AnalysisStore] 编辑已保存');
        },

        cancelEditing() {
            this.isEditing = false;
            // 恢复原始内容
            if (this.originalContent) {
                this.editableContent = JSON.parse(JSON.stringify(this.originalContent));
            }
            console.log('[AnalysisStore] 编辑已取消');
        },

        saveEditDraft() {
            try {
                localStorage.setItem('xhs_edit_draft', JSON.stringify(this.editableContent));
            } catch (e) {
                console.error('Failed to save edit draft:', e);
            }
        },

        loadEditDraft() {
            try {
                const draft = localStorage.getItem('xhs_edit_draft');
                if (draft) {
                    const parsed = JSON.parse(draft);
                    this.editableContent = parsed;
                }
            } catch (e) {
                console.error('Failed to load edit draft:', e);
            }
        },

        // 初始化可编辑内容（当新文案生成时调用）
        initEditableContent() {
            const totalImages = this.imageUrls.length + 1; // +1 for title card
            this.editableContent = {
                title: this.finalCopy.title,
                body: this.finalCopy.body,
                selectedImageIndices: Array.from({ length: totalImages }, (_, i) => i), // 默认全选
                imageOrder: Array.from({ length: totalImages }, (_, i) => i), // 默认顺序
            };
            this.saveEditDraft();
        },

        async startAnalysis(payload) {
            this.logs = [];
            this.finalCopy = { title: "", body: "" };
            this.insight = "";
            this.insightTitle = "";
            this.insightSubtitle = "";
            this.contrastData = null;
            this.dataUnlocked = false;
            this.imageUrls = [];
            this.titleEmoji = "🤔";
            this.titleTheme = "cool";
            this.isLoading = true;
            this.error = null;

            // 确保从 localStorage 加载最新的平台选择（防止时序问题）
            const saved = localStorage.getItem("grandchart_selected_platforms");
            if (saved) {
                try {
                    const platforms = JSON.parse(saved);
                    if (Array.isArray(platforms) && platforms.length > 0) {
                        this.selectedPlatforms = platforms;
                        console.log(
                            "[AnalysisStore] 从 localStorage 恢复平台选择:",
                            platforms
                        );
                    }
                } catch (e) {
                    console.error("Failed to load platform selection:", e);
                }
            }

            // 如果选择了平台，添加到 payload
            // 优先使用 store 中的 selectedPlatforms，如果为空则使用 payload.platforms，都没有则传 undefined 让后端使用默认平台
            const requestPayload = {
                ...payload,
                platforms:
                    this.selectedPlatforms.length > 0
                        ? this.selectedPlatforms
                        : payload.platforms || undefined,
            };

            console.log("[AnalysisStore] 最终请求 payload:", {
                topic: requestPayload.topic,
                platforms: requestPayload.platforms,
                selectedPlatforms: this.selectedPlatforms,
            });

            // 启动工作流状态轮询
            const workflowStore = useWorkflowStore();
            workflowStore.startPolling();

            try {
                console.log(
                    "[AnalysisStore] 开始调用 analyze API，payload:",
                    requestPayload
                );
                await api.analyze(requestPayload, (data) => {
                    console.log("[AnalysisStore] 📥 收到SSE数据:", {
                        agent_name: data.agent_name,
                        status: data.status,
                        content_preview: (data.step_content || "").substring(
                            0,
                            50
                        ),
                        has_model: !!data.model,
                    });

                    // 使用 Vue 的响应式方式更新数组
                    this.logs = [...this.logs, data];
                    console.log(
                        "[AnalysisStore] ✅ 日志已添加，当前数量:",
                        this.logs.length
                    );
                    console.log("[AnalysisStore] 📋 最新日志:", {
                        agent: data.agent_name,
                        content_length: (data.step_content || "").length,
                    });

                    // 处理Analyst输出，解析洞察
                    if (data.agent_name === "Analyst" && data.step_content) {
                        const content = data.step_content;
                        if (content.includes("INSIGHT:")) {
                            const parts = content.split("INSIGHT:");
                            if (parts[1]) {
                                const insightPart = parts[1]
                                    .split("TITLE:")[0]
                                    .trim();
                                this.insight = insightPart;
                            }
                        } else {
                            this.insight = content;
                        }

                        // 解析标题和副标题
                        if (content.includes("TITLE:")) {
                            const parts = content.split("TITLE:");
                            if (parts[1]) {
                                const titlePart = parts[1]
                                    .split("SUB:")[0]
                                    .trim();
                                this.insightTitle = titlePart;
                            }
                        }
                        if (content.includes("SUB:")) {
                            const parts = content.split("SUB:");
                            if (parts[1]) {
                                this.insightSubtitle = parts[1].trim();
                            }
                        }
                        this.saveResultsToSession(); // Persist after Analyst insight
                    }

                    // Update final copy if writer finished
                    if (data.agent_name === "Writer" && data.step_content) {
                        // Strip agent prefix "Writer: " if present
                        // Strip agent prefix "Writer: " if present (robust regex)
                        const cleanContent = data.step_content.replace(/(?:^|\n)Writer:\s*/i, '').trim();
                        const content = cleanContent;
                        let title = "生成文案";
                        let body = content;

                        if (content.includes("TITLE:")) {
                            const parts = content.split("CONTENT:");
                            const headerPart = parts[0];
                            title = headerPart.split("EMOJI:")[0].replace("TITLE:", "").trim();
                            // Double check: remove Writer prefix if it still exists in title
                            title = title.replace(/^Writer:\s*/i, '').replace(/^TITLE:\s*/i, '').trim();
                            body = parts[1] ? parts[1].trim() : "";

                            // Parse EMOJI if present
                            const emojiMatch = headerPart.match(/EMOJI:\s*(.+?)(?:\n|THEME:|$)/i);
                            if (emojiMatch && emojiMatch[1]) {
                                this.titleEmoji = emojiMatch[1].trim();
                            }

                            // Parse THEME if present
                            const themeMatch = headerPart.match(/THEME:\s*(warm|cool|alert|dark)/i);
                            if (themeMatch && themeMatch[1]) {
                                this.titleTheme = themeMatch[1].toLowerCase();
                            }
                        }

                        this.finalCopy = {
                            title: title,
                            body: body,
                        };
                        // 初始化可编辑内容
                        this.initEditableContent();
                        this.saveResultsToSession(); // Persist after Writer output
                    }

                    // 处理 Image Generator 输出
                    if (
                        data.agent_name === "Image Generator" &&
                        data.image_urls
                    ) {
                        console.log(
                            "[AnalysisStore] 🖼️ 收到生成的图片:",
                            data.image_urls
                        );
                        this.imageUrls = data.image_urls;
                        this.saveResultsToSession(); // Persist after Image Generator output
                    }

                    // 如果完成，解锁数据
                    if (data.status === "finished") {
                        this.dataUnlocked = true;
                        this.saveResultsToSession(); // Persist final state
                        workflowStore.stopPolling();
                        workflowStore.fetchStatus(); // 最后更新一次状态
                    }

                    // 如果出错，停止轮询
                    if (data.status === "error") {
                        workflowStore.stopPolling();
                        workflowStore.fetchStatus();
                    }
                });
            } catch (err) {
                console.error("startAnalysis error", err);
                this.error = err.message || "请求失败，请检查后端服务是否启动";
                workflowStore.stopPolling();
            } finally {
                this.isLoading = false;
            }
        },
    },
});
