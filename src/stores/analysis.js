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
            dataViewImages: cachedResults?.dataViewImages || [], // 新增：数据视图卡片图片
            titleEmoji: cachedResults?.titleEmoji || "🤔", // Title Card emoji (default)
            titleTheme: cachedResults?.titleTheme || "cool", // Title Card color theme: warm/peach/sunset/cool/ocean/mint/sky/lavender/grape/forest/lime/alert/dark/cream
            platformStats: cachedResults?.platformStats || null, // 平台爬取统计 {platform_code: count}
            
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

            // 使用后端返回的真实平台统计数据
            const realStats = state.platformStats || {};
            const hasRealData = Object.keys(realStats).length > 0;
            
            // 计算最大值用于归一化
            const maxCount = hasRealData 
                ? Math.max(...Object.values(realStats), 1) 
                : 1;
            
            const platformData = platforms.map(p => {
                const platformName = platformNameMap[p] || p;
                
                if (hasRealData) {
                    // 使用真实数据：归一化到 50-100 范围
                    const count = realStats[p] || 0;
                    const normalized = count > 0 
                        ? 50 + (count / maxCount) * 50 
                        : 50;
                    return { name: platformName, value: Math.round(normalized) };
                } else {
                    // 无数据时显示基础值
                    return { name: platformName, value: 60 };
                }
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
                    const titleMatch = content.match(/TITLE:\s*(.+?)(?=\s*(?:SUB:|INSIGHT:|SUMMARY:|$))/is);
                    const summaryMatch = content.match(/SUMMARY:\s*(.+?)(?=\s*(?:TITLE:|INSIGHT:|SUB:|$))/is);
                    const insightMatch = content.match(/INSIGHT:\s*(.+?)(?=\s*(?:TITLE:|SUMMARY:|$))/is);
                    
                    const fullInsight = insightMatch ? insightMatch[1].trim() : '';
                    
                    // 优先使用 SUMMARY 字段（LLM 生成的精炼观点）
                    let summary = '';
                    if (summaryMatch) {
                        summary = summaryMatch[1].trim();
                    } else if (fullInsight) {
                        // 降级：提取第一句话
                        const firstSentence = fullInsight.match(/^[^。！？.!?]+[。！？.!?]/);
                        if (firstSentence) {
                            summary = firstSentence[0];
                        } else {
                            summary = fullInsight.substring(0, 40);
                        }
                    }
                    
                    return {
                        round: index + 1,
                        title: titleMatch ? titleMatch[1].trim() : '推理中...',
                        insight: fullInsight,
                        summary: summary, // LLM 生成的精炼观点，用于卡片
                        insightPreview: fullInsight.substring(0, 80) + (fullInsight.length > 80 ? '...' : '') // 80字预览
                    };
                });
        },

        // 趋势图数据
        trendChartData: (state) => {
            // 基于实际辩论数据生成趋势曲线
            const analystLogs = state.logs.filter(log => log.agent_name === 'Analyst');
            const debateRounds = analystLogs.length;
            
            if (debateRounds === 0) {
                return {
                    stage: '待分析',
                    growth: 0,
                    curve: [0, 0, 0, 0, 0, 0, 0]
                };
            }
            
            // 1. 分析每轮辩论的"热度"（基于内容长度和关键词密度）
            const heatKeywords = ['热议', '关注', '讨论', '争议', '热度', '爆发', '火爆', '刷屏'];
            const roundHeat = analystLogs.map(log => {
                const content = log.step_content || '';
                const contentLength = content.length;
                
                // 统计热度关键词出现次数
                let keywordCount = 0;
                heatKeywords.forEach(keyword => {
                    const regex = new RegExp(keyword, 'gi');
                    const matches = content.match(regex);
                    if (matches) keywordCount += matches.length;
                });
                
                // 综合评分：内容长度 + 关键词密度
                const lengthScore = Math.min(contentLength / 10, 50); // 最多50分
                const keywordScore = keywordCount * 10; // 每个关键词10分
                return Math.min(lengthScore + keywordScore, 100);
            });
            
            // 2. 生成7点趋势曲线（插值）
            let curve = [];
            if (debateRounds === 1) {
                // 单轮：模拟爆发
                const heat = roundHeat[0];
                curve = [heat * 0.3, heat * 0.5, heat * 0.7, heat, heat * 0.95, heat * 0.9, heat * 0.85];
            } else if (debateRounds === 2) {
                // 两轮：从第一轮到第二轮
                const [h1, h2] = roundHeat;
                curve = [h1 * 0.5, h1, h1 * 1.1, (h1 + h2) / 2, h2, h2 * 0.95, h2 * 0.9];
            } else {
                // 多轮：均匀分布
                curve = Array(7).fill(0).map((_, i) => {
                    const progress = i / 6;
                    const index = Math.floor(progress * (debateRounds - 1));
                    const nextIndex = Math.min(index + 1, debateRounds - 1);
                    const localProgress = (progress * (debateRounds - 1)) - index;
                    
                    // 线性插值
                    return Math.round(
                        roundHeat[index] * (1 - localProgress) + 
                        roundHeat[nextIndex] * localProgress
                    );
                });
            }
            
            // 3. 判断阶段和增速
            const firstHeat = curve[0];
            const lastHeat = curve[curve.length - 1];
            const avgHeat = curve.reduce((a, b) => a + b, 0) / curve.length;
            const growth = Math.round(((lastHeat - firstHeat) / Math.max(firstHeat, 1)) * 100);
            
            let stage = '扩散期';
            if (growth > 100) {
                stage = '爆发期';
            } else if (growth < -20) {
                stage = '回落期';
            } else if (avgHeat > 80) {
                stage = '高热期';
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
                dataViewImages: this.dataViewImages,
                titleEmoji: this.titleEmoji,
                titleTheme: this.titleTheme,
                platformStats: this.platformStats,
                selectedImageIndices: this.editableContent.selectedImageIndices,
                imageOrder: this.editableContent.imageOrder,
            };
            try {
                sessionStorage.setItem("grandchart_analysis_results", JSON.stringify(results));
            } catch (e) {
                console.error("Failed to save analysis results to sessionStorage:", e);
            }
        },

        // 设置数据视图图片
        setDataViewImages(images) {
            console.log('[AnalysisStore] 🔵 setDataViewImages 被调用:', {
                imagesCount: images.length,
                imageSizes: images.map(img => `${(img.length / 1024).toFixed(1)}KB`),
                currentDataViewImages: this.dataViewImages.length
            });
            // 使用 Vue 的响应式方式更新数组（确保触发响应式更新）
            this.dataViewImages = [...images];
            console.log('[AnalysisStore] 🟢 dataViewImages 已更新:', this.dataViewImages.length, '张');
            this.saveResultsToSession();
            console.log('[AnalysisStore] 💾 已调用 saveResultsToSession');
            
            // 重新初始化可编辑内容（包含新的 DataView 图片）
            if (this.finalCopy.title || this.finalCopy.body) {
                this.initEditableContent();
                console.log('[AnalysisStore] 🔄 已重新初始化 editableContent（包含 DataView 图片）');
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
            // 计算总图片数：Title Card + DataView 卡片 + AI 生图
            const totalImages = 1 + this.dataViewImages.length + this.imageUrls.length;
            this.editableContent = {
                title: this.finalCopy.title,
                body: this.finalCopy.body,
                selectedImageIndices: Array.from({ length: totalImages }, (_, i) => i), // 默认全选所有图片
                imageOrder: Array.from({ length: totalImages }, (_, i) => i), // 默认顺序
            };
            this.saveEditDraft();
            console.log('[AnalysisStore] initEditableContent - 默认全选所有图片:', {
                totalImages,
                dataViewCount: this.dataViewImages.length,
                aiImageCount: this.imageUrls.length,
                selectedImageIndices: this.editableContent.selectedImageIndices,
                imageOrder: this.editableContent.imageOrder
            });
        },

        // 停止分析（取消 SSE 请求）
        stopAnalysis() {
            console.log('[AnalysisStore] 🛑 停止分析');
            const aborted = api.abortAnalysis();
            this.isLoading = false;
            
            // 停止工作流状态轮询
            const workflowStore = useWorkflowStore();
            workflowStore.stopPolling();
            
            return aborted;
        },

        async startAnalysis(payload) {
            // 🧹 彻底清除所有旧数据（包括缓存）
            this.logs = [];
            this.finalCopy = { title: "", body: "" };
            this.insight = "";
            this.insightTitle = "";
            this.insightSubtitle = "";
            this.contrastData = null;
            this.dataUnlocked = false;
            this.imageUrls = [];
            this.dataViewImages = []; // 清空旧的 DataView 图片
            this.titleEmoji = "🤔";
            this.titleTheme = "cool";
            this.platformStats = null; // 清空平台统计
            this.isLoading = true;
            this.error = null;
            
            // 🔴 关键：清除编辑草稿缓存（防止旧内容污染新分析）
            this.editableContent = {
                title: "",
                body: "",
                selectedImageIndices: [0],
                imageOrder: [0],
            };
            this.originalContent = null;
            this.isEditing = false;
            
            // 清除 localStorage 中的编辑草稿
            try {
                localStorage.removeItem('xhs_edit_draft');
                console.log('[AnalysisStore] 🗑️ 已清除 localStorage 编辑草稿');
            } catch (e) {
                console.error('Failed to clear edit draft:', e);
            }
            
            // 清除 sessionStorage 中的旧分析结果
            try {
                sessionStorage.removeItem('grandchart_analysis_results');
                console.log('[AnalysisStore] 🗑️ 已清除 sessionStorage 分析结果缓存');
            } catch (e) {
                console.error('Failed to clear session results:', e);
            }
            
            console.log('[AnalysisStore] 🧹 已清空所有旧数据，包括 DataView 图片和所有缓存');

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
                        has_platform_stats: !!data.platform_stats,
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

                    // 处理 Crawler 输出，保存平台统计
                    if (data.agent_name === "Crawler") {
                        console.log("[AnalysisStore] 🔍 Crawler 数据检查:", {
                            has_platform_stats: !!data.platform_stats,
                            platform_stats: data.platform_stats,
                            all_keys: Object.keys(data)
                        });
                        if (data.platform_stats) {
                            this.platformStats = data.platform_stats;
                            console.log("[AnalysisStore] 📊 平台统计已保存:", this.platformStats);
                            this.saveResultsToSession();
                        }
                    }

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

                            // 解析 THEME - 只匹配主题值，不贪婪匹配后面的内容
                            const themeMatch = cleanContent.match(/THEME:\s*(warm|peach|sunset|cool|ocean|mint|sky|lavender|grape|forest|lime|alert|dark|cream)/i);
                            if (themeMatch && themeMatch[1]) {
                                this.titleTheme = themeMatch[1].toLowerCase();
                                console.log('[AnalysisStore] 🎨 解析到 Theme:', this.titleTheme);
                            }

                            // 解析正文内容
                            // 优先使用 CONTENT: 标记
                            const contentMatch = cleanContent.match(/CONTENT:\s*([\s\S]+)$/i);
                            if (contentMatch && contentMatch[1]) {
                                body = contentMatch[1].trim();
                            } else {
                                // 如果没有 CONTENT: 标记，提取 THEME 值之后的所有内容作为正文
                                // 匹配模式：THEME: <主题值><正文内容>
                                const themeBodyMatch = cleanContent.match(/THEME:\s*(?:warm|peach|sunset|cool|ocean|mint|sky|lavender|grape|forest|lime|alert|dark|cream)\s*([\s\S]+)$/i);
                                if (themeBodyMatch && themeBodyMatch[1]) {
                                    body = themeBodyMatch[1].trim();
                                    console.log('[AnalysisStore] 🔧 使用 THEME 后内容作为正文（无 CONTENT 标记）');
                                } else {
                                    // 最后的 fallback：移除所有已知标记
                                    body = cleanContent
                                        .replace(/TITLE:\s*.+?(?=\s*(?:EMOJI:|THEME:|CONTENT:|$))/is, '')
                                        .replace(/EMOJI:\s*.+?(?=\s*(?:THEME:|CONTENT:|$))/is, '')
                                        .replace(/THEME:\s*(?:warm|peach|sunset|cool|ocean|mint|sky|lavender|grape|forest|lime|alert|dark|cream)/i, '')
                                        .trim();
                                    console.log('[AnalysisStore] 🔧 使用 fallback 解析正文');
                                }
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
                        
                        // 触发 DataView 卡片生成
                        console.log('[AnalysisStore] 📊 Writer 完成，触发 DataView 卡片生成');
                        setTimeout(() => {
                            window.dispatchEvent(new CustomEvent('generate-dataview-cards'));
                            console.log('[AnalysisStore] ✅ 已触发 generate-dataview-cards 事件');
                        }, 500);
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

                    // 处理 DataView Generator 输出
                    if (
                        data.agent_name === "DataView Generator" &&
                        data.dataview_images
                    ) {
                        console.log(
                            "[AnalysisStore] 🖼️ 收到DataView卡片:",
                            data.dataview_images
                        );
                        this.dataViewImages = data.dataview_images;
                        
                        // 重新初始化可编辑内容（包含新的DataView卡片）
                        if (this.finalCopy.title || this.finalCopy.body) {
                            this.initEditableContent();
                            console.log('[AnalysisStore] ✅ editableContent 已重新初始化（包含DataView卡片）');
                        }
                        
                        this.saveResultsToSession();
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
