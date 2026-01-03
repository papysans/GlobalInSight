/**
 * API 服务
 * 统一管理所有后端接口调用
 */

const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * 通用请求函数
 */
async function request(url, options = {}) {
    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response
            .json()
            .catch(() => ({ detail: response.statusText }));
        throw new Error(
            error.detail || `HTTP error! status: ${response.status}`
        );
    }

    return response.json();
}

/**
 * 流式请求（SSE）
 */
async function streamRequest(url, options = {}, onMessage) {
    console.log("[API] 开始SSE请求:", url, options);

    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    console.log("[API] SSE响应状态:", response.status, response.ok);

    if (!response.ok || !response.body) {
        const errorText = await response.text().catch(() => "Unknown error");
        console.error("[API] SSE响应错误:", response.status, errorText);
        throw new Error(
            `Network response was not ok: ${response.status} ${errorText}`
        );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let eventCount = 0;

    console.log("[API] 开始读取SSE流");

    while (true) {
        const { value, done } = await reader.read();
        if (done) {
            console.log("[API] SSE流读取完成，共处理", eventCount, "个事件");
            break;
        }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
            if (!part.trim()) continue;

            if (!part.startsWith("data: ")) {
                console.log("[API] 跳过非data行:", part.substring(0, 50));
                continue;
            }

            const jsonStr = part.replace(/^data: /, "");
            try {
                const data = JSON.parse(jsonStr);
                eventCount++;
                console.log(`[API] 解析SSE事件 #${eventCount}:`, {
                    agent_name: data.agent_name,
                    status: data.status,
                    content_length: (data.step_content || "").length,
                });
                onMessage(data);
            } catch (e) {
                console.warn(
                    "[API] JSON解析错误:",
                    e,
                    "原始数据:",
                    jsonStr.substring(0, 100)
                );
            }
        }
    }
}

export const api = {
    /**
     * 执行完整工作流分析
     * @param {Object} payload - { topic, urls?, platforms? }
     * @param {Function} onMessage - SSE 消息回调
     */
    async analyze(payload, onMessage) {
        return streamRequest(
            "/analyze", {
                method: "POST",
                body: JSON.stringify(payload),
            },
            onMessage
        );
    },

    /**
     * 获取配置
     */
    async getConfig() {
        return request("/config");
    },

    /**
     * 更新配置
     * @param {Object} config - 部分配置更新
     */
    async updateConfig(config) {
        return request("/config", {
            method: "PUT",
            body: JSON.stringify(config),
        });
    },

    /**
     * 获取历史输出文件列表
     * @param {number} limit - 数量限制
     * @param {number} offset - 偏移量
     */
    async getOutputFiles(limit = 20, offset = 0) {
        return request(`/outputs?limit=${limit}&offset=${offset}`);
    },

    /**
     * 获取指定输出文件内容
     * @param {string} filename - 文件名
     */
    async getOutputFile(filename) {
        return request(`/outputs/${encodeURIComponent(filename)}`);
    },

    /**
     * 获取热榜（TopHub）数据
     * @param {number} limit - 返回条数
     * @param {string} source - "hot"=全榜，"all"=全部榜单，其它=指定source_id
     * @param {boolean} forceRefresh - 是否跳过缓存强制刷新
     */
    async getHotNews(limit = 10, source = "hot", forceRefresh = false) {
        const params = new URLSearchParams({
            limit: String(limit),
            source,
            force_refresh: String(forceRefresh),
        });
        return request(`/hotnews?${params.toString()}`);
    },

    /**
     * 获取工作流状态
     */
    async getWorkflowStatus() {
        return request("/workflow/status");
    },

    /**
     * 生成舆论对比数据
     * @param {Object} payload - { topic, insight }
     */
    async generateContrastData(payload) {
        return request("/generate-data/contrast", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },

    /**
     * 生成情感光谱数据
     * @param {Object} payload - { topic, insight }
     */
    async generateSentimentData(payload) {
        return request("/generate-data/sentiment", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },

    /**
     * 生成关键词数据
     * @param {Object} payload - { topic, crawler_data? }
     */
    async generateKeywordsData(payload) {
        return request("/generate-data/keywords", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },

    /**
     * 获取热点新闻列表（对齐后的数据）
     * @param {Object} payload - { platforms?: string[], force_refresh?: boolean }
     */
    async getHotNewsTrending(payload = {}) {
        return request("/hot-news/collect", {
            method: "POST",
            body: JSON.stringify({
                platforms: payload.platforms || ["all"],
                force_refresh: payload.force_refresh || false,
            }),
        });
    },
};