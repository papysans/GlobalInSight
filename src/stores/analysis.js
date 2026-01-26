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

        // 洞察卡数据
        insightCardData: (state) => {
            // Workflow 数据源
            if (state.dataUnlocked) {
                const debateRounds = state.logs.filter(log => log.agent_name === 'Analyst').length;
                const critiqueCount = state.logs.filter(log => log.agent_name === 'Debater').length;
                const controversy = critiqueCount > 3 ? '高' : critiqueCount > 1 ? '中' : '低';
                
                // 计算平台覆盖（从日志中提取）
                const platformCount = state.selectedPlatforms?.length || 0;
                
                return {
                    conclusion: state.insight || '暂无洞察',
                    coverage: {
                        platforms: platformCount,
                        debateRounds,
                        controversy
                    },
                    keyFinding: extractKeyFinding(state.insight)
                };
            }
            
            // 默认返回空数据
            return {
                conclusion: '暂无洞察',
                coverage: {
                    platforms: 0,
                    debateRounds: 0,
                    controversy: '低'
                },
                keyFinding: ''
            };
        },

        // 雷达图数据
        radarChartData: (state) => {
            // 从选中的平台生成雷达图数据
            const platforms = state.selectedPlatforms || [];
            if (platforms.length === 0) {
                return {
                    labels: [],
                    datasets: [{
                        label: '平台覆盖',
                        data: [],
                        backgroundColor: 'rgba(59, 130, 246, 0.2)',
                        borderColor: 'rgb(59, 130, 246)'
                    }]
                };
            }

            // 为每个平台生成一个基础热度值（可以后续从实际数据中获取）
            const platformData = platforms.map(p => {
                const platformName = platformNameMap[p] || p;
                // 生成一个基于平台的伪随机值（60-95之间）
                const baseValue = 60 + (platformName.charCodeAt(0) % 35);
                return { name: platformName, value: baseValue };
            });

            return {
                labels: platformData.map(p => p.name),
                datasets: [{
                    label: '平台覆盖',
                    data: platformData.map(p => p.value),
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgb(59, 130, 246)',
                    pointBackgroundColor: 'rgb(59, 130, 246)'
                }]
            };
        },

        // 辩论时间线数据
        debateTimelineData: (state) => {
            return state.logs
                .filter(log => log.agent_name === 'Analyst')
                .map((log, index) => {
                    const content = log.step_content || '';
                    const titleMatch = content.match(/TITLE:\s*(.+?)(?=\s*(?:SUB:|INSIGHT:|$))/is);
                    const insightMatch = content.match(/INSIGHT:\s*(.+?)(?=\s*(?:TITLE:|$))/is);
                    
                    const fullInsight = insightMatch ? insightMatch[1].trim() : '';
                    
                    // 生成一句话总结（用于卡片展示）
                    // 提取第一句话，或者截取前40字
                    let summary = '';
                    if (fullInsight) {
                        const firstSentence = fullInsight.match(/^[^。！？.!?]+[。！？.!?]/);
                        if (firstSentence) {
                            summary = firstSentence[0];
                        } else {
                            summary = fullInsight.substring(0, 40) + (fullInsight.length > 40 ? '...' : '');
                        }
                    }
                    
                    return {
                        round: index + 1,
                        title: titleMatch ? titleMatch[1].trim() : '推理中...',
                        insight: fullInsight,
                        summary: summary, // 一句话总结，用于卡片
                        insightPreview: fullInsight.substring(0, 80) + (fullInsight.length > 80 ? '...' : '') // 80字预览
                    };
                });
        },

        // 趋势图数据
        trendChartData: (state) => {
            // 基于分析状态生成趋势数据
            const debateRounds = state.logs.filter(log => log.agent_name === 'Analyst').length;
            
            // 根据辩论轮次判断阶段
            let stage = '扩散期';
            let growth = 50;
            let curve = [40, 55, 70, 80, 90, 95, 92];
            
            if (debateRounds <= 2) {
                // 早期：爆发期
                stage = '爆发期';
                growth = 999;
                curve = [10, 30, 60, 85, 95, 100, 98];
            } else if (debateRounds > 4) {
                // 后期：回落期
                stage = '回落期';
                growth = -20;
                curve = [80, 75, 65, 50, 35, 25, 20];
            }
            
            return {
                stage,
                growth,
                curve
            };
        }
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
                        console.log('[AnalysisStore] 📝 Writer 输出原始内容:', {
                            length: data.step_content.length,
                            preview: data.step_content.substring(0, 200),
                            hasTITLE: data.step_content.includes("TITLE:"),
                            hasCONTENT: data.step_content.includes("CONTENT:"),
                            hasEMOJI: data.step_content.includes("EMOJI:"),
                            hasTHEME: data.step_content.includes("THEME:")
                        });
                        
                        // Strip agent prefix "Writer: " if present (robust regex)
                        let cleanContent = data.step_content.replace(/(?:^|\n)Writer:\s*/gi, '').trim();
                        console.log('[AnalysisStore] 🧹 清理后的内容:', {
                            length: cleanContent.length,
                            preview: cleanContent.substring(0, 200)
                        });
                        
                        let title = "生成文案";
                        let body = cleanContent;

                        if (cleanContent.includes("TITLE:")) {
                            // 解析标题
                            const titleMatch = cleanContent.match(/TITLE:\s*(.+?)(?=\s*(?:EMOJI:|THEME:|CONTENT:|$))/is);
                            if (titleMatch && titleMatch[1]) {
                                title = titleMatch[1].trim();
                            }

                            // 解析 EMOJI
                            const emojiMatch = cleanContent.match(/EMOJI:\s*(.+?)(?=\s*(?:THEME:|CONTENT:|$))/is);
                            if (emojiMatch && emojiMatch[1]) {
                                this.titleEmoji = emojiMatch[1].trim();
                                console.log('[AnalysisStore] 😀 解析到 Emoji:', this.titleEmoji);
                            }

                            // 解析 THEME
                            const themeMatch = cleanContent.match(/THEME:\s*(warm|cool|alert|dark)/i);
                            if (themeMatch && themeMatch[1]) {
                                this.titleTheme = themeMatch[1].toLowerCase();
                                console.log('[AnalysisStore] 🎨 解析到 Theme:', this.titleTheme);
                            }

                            // 解析正文内容（CONTENT: 之后的所有内容）
                            const contentMatch = cleanContent.match(/CONTENT:\s*([\s\S]+)$/i);
                            if (contentMatch && contentMatch[1]) {
                                body = contentMatch[1].trim();
                            } else {
                                // 如果没有 CONTENT: 标记，尝试移除所有元数据标记
                                body = cleanContent
                                    .replace(/TITLE:\s*.+?(?=\s*(?:EMOJI:|THEME:|CONTENT:|$))/is, '')
                                    .replace(/EMOJI:\s*.+?(?=\s*(?:THEME:|CONTENT:|$))/is, '')
                                    .replace(/THEME:\s*.+?(?=\s*CONTENT:|$)/is, '')
                                    .trim();
                            }

                            console.log('[AnalysisStore] 📋 解析结果:', {
                                title,
                                bodyLength: body.length,
                                bodyPreview: body.substring(0, 100)
                            });
                        } else {
                            console.warn('[AnalysisStore] ⚠️ 内容中没有找到 TITLE: 标记，使用原始内容');
                        }

                        this.finalCopy = {
                            title: title,
                            body: body,
                        };
                        
                        console.log('[AnalysisStore] ✅ finalCopy 已更新:', {
                            title: this.finalCopy.title,
                            bodyLength: this.finalCopy.body.length,
                            bodyPreview: this.finalCopy.body.substring(0, 100)
                        });
                        
                        // 初始化可编辑内容
                        this.initEditableContent();
                        console.log('[AnalysisStore] ✅ editableContent 已初始化:', {
                            title: this.editableContent.title,
                            bodyLength: this.editableContent.body.length,
                            selectedImageIndices: this.editableContent.selectedImageIndices,
                            imageOrder: this.editableContent.imageOrder
                        });
                        
                        this.saveResultsToSession(); // Persist after Writer output
                        console.log('[AnalysisStore] 💾 已保存到 sessionStorage');
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
                        
                        // 重新初始化可编辑内容（包含新的图片）
                        this.initEditableContent();
                        console.log('[AnalysisStore] ✅ editableContent 已重新初始化（包含AI图片）:', {
                            selectedImageIndices: this.editableContent.selectedImageIndices,
                            imageOrder: this.editableContent.imageOrder,
                            totalImages: this.imageUrls.length + 1
                        });
                        
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

// 辅助函数
function extractKeyFinding(insight) {
    if (!insight) return '';
    const match = insight.match(/背后是(.+?)。|反映了(.+?)。/);
    return match ? (match[1] || match[2]).trim() : '';
}

const platformNameMap = {
    wb: '微博',
    bili: 'B站',
    xhs: '小红书',
    dy: '抖音',
    ks: '快手',
    tieba: '贴吧',
    zhihu: '知乎',
    hn: 'Hacker News',
    baidu: '百度',
    kuaishou: '快手',
    weibo: '微博',
    bilibili: 'B站',
    douyin: '抖音'
};
