import { defineStore } from "pinia";

export const useAnalysisStore = defineStore("analysis", {
    state: () => ({
        logs: [],
        finalCopy: { title: "", body: "" },
        isLoading: false,
        error: null,
    }),
    actions: {
        async startAnalysis(payload) {
            this.logs = [];
            this.finalCopy = { title: "", body: "" };
            this.isLoading = true;
            this.error = null;

            try {
                await this.readStream(payload);
            } catch (err) {
                console.error("startAnalysis error", err);
                this.error = err.message || "请求失败，请检查后端服务是否启动";
            } finally {
                this.isLoading = false;
            }
        },

        async readStream(payload) {
            const response = await fetch("http://127.0.0.1:8000/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!response.ok || !response.body) {
                throw new Error("Network response was not ok");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split("\n\n");
                buffer = parts.pop() || "";

                for (const part of parts) {
                    if (!part.startsWith("data: ")) continue;
                    const jsonStr = part.replace(/^data: /, "");
                    try {
                        const evt = JSON.parse(jsonStr);
                        this.logs.push(evt);

                        // Update final copy if writer finished
                        if (evt.agent_name === "Writer" && evt.step_content) {
                            this.finalCopy = {
                                title: "生成文案",
                                body: evt.step_content,
                            };
                        }
                    } catch (e) {
                        console.warn("parse error", e, part);
                    }
                }
            }
        },
    },
});
