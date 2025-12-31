import { defineStore } from "pinia";
import { api } from '../api';
import { useWorkflowStore } from './workflow';

export const useAnalysisStore = defineStore("analysis", {
    state: () => ({
        logs: [],
        finalCopy: { title: "", body: "" },
        isLoading: false,
        error: null,
        selectedPlatforms: [], // 选中的平台
        insight: "", // 核心洞察
        insightTitle: "", // 洞察标题
        insightSubtitle: "", // 洞察副标题
        contrastData: null, // 舆论对比数据
        dataUnlocked: false, // 数据是否解锁
    }),

    getters: {
        availablePlatforms: () => [
            { code: 'wb', name: '微博' },
            { code: 'bili', name: 'B站' },
            { code: 'xhs', name: '小红书' },
            { code: 'dy', name: '抖音' },
            { code: 'ks', name: '快手' },
            { code: 'tieba', name: '贴吧' },
            { code: 'zhihu', name: '知乎' },
        ],
    },

    actions: {
        setSelectedPlatforms(platforms) {
            this.selectedPlatforms = platforms;
        },

        async startAnalysis(payload) {
            this.logs = [];
            this.finalCopy = { title: "", body: "" };
            this.insight = "";
            this.insightTitle = "";
            this.insightSubtitle = "";
            this.contrastData = null;
            this.dataUnlocked = false;
            this.isLoading = true;
            this.error = null;

            // 如果选择了平台，添加到 payload
            const requestPayload = {
                ...payload,
                platforms: this.selectedPlatforms.length > 0 ? this.selectedPlatforms : payload.platforms,
            };

            // 启动工作流状态轮询
            const workflowStore = useWorkflowStore();
            workflowStore.startPolling();

            try {
                await api.analyze(requestPayload, (data) => {
                    this.logs.push(data);

                    // 处理Analyst输出，解析洞察
                    if (data.agent_name === "Analyst" && data.step_content) {
                        const content = data.step_content;
                        if (content.includes("INSIGHT:")) {
                            const parts = content.split("INSIGHT:");
                            if (parts[1]) {
                                const insightPart = parts[1].split("TITLE:")[0].trim();
                                this.insight = insightPart;
                            }
                        } else {
                            this.insight = content;
                        }

                        // 解析标题和副标题
                        if (content.includes("TITLE:")) {
                            const parts = content.split("TITLE:");
                            if (parts[1]) {
                                const titlePart = parts[1].split("SUB:")[0].trim();
                                this.insightTitle = titlePart;
                            }
                        }
                        if (content.includes("SUB:")) {
                            const parts = content.split("SUB:");
                            if (parts[1]) {
                                this.insightSubtitle = parts[1].trim();
                            }
                        }
                    }

                    // Update final copy if writer finished
                    if (data.agent_name === "Writer" && data.step_content) {
                        const content = data.step_content;
                        let title = "生成文案";
                        let body = content;

                        if (content.includes("TITLE:")) {
                            const parts = content.split("CONTENT:");
                            title = parts[0].replace("TITLE:", "").trim();
                            body = parts[1] ? parts[1].trim() : "";
                        }

                        this.finalCopy = {
                            title: title,
                            body: body,
                        };
                    }

                    // 如果完成，解锁数据
                    if (data.status === 'finished') {
                        this.dataUnlocked = true;
                        workflowStore.stopPolling();
                        workflowStore.fetchStatus(); // 最后更新一次状态
                    }

                    // 如果出错，停止轮询
                    if (data.status === 'error') {
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