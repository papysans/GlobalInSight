/**
 * API 服务
 * 统一管理所有后端接口调用
 */

const API_BASE_URL = "http://127.0.0.1:8000/api";

// 当前活跃的 SSE AbortController（用于取消请求）
let currentAbortController = null;

/**
 * 通用请求函数
 */
async function request(url, options = {}) {
    console.log(`[API] Request: ${options.method || 'GET'} ${url}`, options.body ? JSON.parse(options.body) : '');
    
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
        console.error(`[API] Error response:`, error);
        
        // 如果 detail 是数组（Pydantic 验证错误），格式化输出
        if (Array.isArray(error.detail)) {
            const errorMessages = error.detail.map(err => {
                const loc = err.loc ? err.loc.join(' -> ') : 'unknown';
                return `${loc}: ${err.msg} (type: ${err.type})`;
            }).join('\n');
            console.error('[API] Validation errors:\n', errorMessages);
            throw new Error(`Validation failed:\n${errorMessages}`);
        }
        
        throw new Error(
            error.detail || `HTTP error! status: ${response.status}`
        );
    }

    const data = await response.json();
    console.log(`[API] Response:`, data);
    return data;
}

/**
 * 流式请求（SSE）
 */
async function streamRequest(url, options = {}, onMessage) {
    console.log("[API] 开始SSE请求:", url, options);

    // 创建新的 AbortController
    currentAbortController = new AbortController();
    const signal = currentAbortController.signal;

    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        signal,
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
            currentAbortController = null;
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
     * 取消当前正在进行的 SSE 请求
     */
    abortAnalysis() {
        if (currentAbortController) {
            console.log("[API] 🛑 取消 SSE 请求");
            currentAbortController.abort();
            currentAbortController = null;
            return true;
        }
        console.log("[API] ⚠️ 没有活跃的 SSE 请求可取消");
        return false;
    },

    /**
     * 执行行情推演（SSE 流式）— 旧接口已移除，使用 analyzeStock
     */

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
     * 获取用户设置（LLM keys / 即梦配置）
     */
    async getUserSettings() {
        return request("/user-settings");
    },

    /**
     * 更新用户设置（部分更新）
     * @param {Object} payload - { llm_apis?, volcengine? }
     */
    async updateUserSettings(payload) {
        return request("/user-settings", {
            method: "PUT",
            body: JSON.stringify(payload),
        });
    },

    // --- 小红书 MCP 发布接口 ---

    /**
     * 获取小红书 MCP 服务状态
     * @returns {Promise<{mcp_available: boolean, login_status: boolean, message: string}>}
     */
    async getXhsStatus() {
        return request("/xhs/status");
    },

    /**
     * 发布内容到小红书
     * @param {Object} payload - { title: string, content: string, images: string[] }
     * @returns {Promise<{success: boolean, message: string, data?: any}>}
     */
    async publishToXhs(payload) {
        return request("/xhs/publish", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },

    // --- 模型管理接口 ---

    /**
     * 获取所有提供商的模型列表
     * @returns {Promise<Object>} - { "deepseek": [...], "gemini": [...], ... }
     */
    async getModels() {
        return request("/models");
    },

    /**
     * 验证提供商-模型组合是否有效
     * @param {Object} payload - { provider: string, model: string }
     * @returns {Promise<{valid: boolean, message: string}>}
     */
    async validateModel(payload) {
        return request("/validate-model", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },

    // ========== 股票资讯 API ==========

    /**
     * 获取热榜聚类数据（话题聚类 + 跨平台对齐）
     * @param {boolean} [forceRefresh=false] - 是否跳过缓存
     */
    async getHotNews(forceRefresh = false) {
        const params = new URLSearchParams({ force_refresh: String(forceRefresh) });
        return request(`/stock/hot?${params.toString()}`);
    },

    /**
     * 获取股票资讯列表
     * @param {Object} params - { limit, source, category, forceRefresh }
     * @param {number} [params.limit=50] - 返回条数
     * @param {string} [params.source] - 按数据源筛选
     * @param {string} [params.category] - 按类别筛选 domestic/international/research_report
     * @param {boolean} [params.forceRefresh=false] - 是否跳过缓存
     */
    async getStockNews({ limit = 50, source, category, forceRefresh = false } = {}) {
        const params = new URLSearchParams({ limit: String(limit), force_refresh: String(forceRefresh) });
        if (source) params.set("source", source);
        if (category) params.set("category", category);
        return request(`/stock/news?${params.toString()}`);
    },

    /**
     * 获取支持的数据源列表及状态
     */
    async getStockSources() {
        return request("/stock/sources");
    },

    /**
     * 触发行情推演（SSE 流式）
     * @param {Object} payload - { topic, debate_rounds, news_items? }
     * @param {Function} onMessage - SSE 消息回调
     */
    async analyzeStock(payload, onMessage) {
        return streamRequest(
            "/stock/analyze",
            { method: "POST", body: JSON.stringify(payload) },
            onMessage,
        );
    },

    /**
     * 获取历史推演记录列表
     * @param {number} [limit=20]
     * @param {number} [offset=0]
     */
    async getStockAnalysisHistory(limit = 20, offset = 0) {
        return request(`/stock/analyze/history?limit=${limit}&offset=${offset}`);
    },

    /**
     * 获取单条推演结果详情
     * @param {string} analysisId
     */
    async getStockAnalysisDetail(analysisId) {
        return request(`/stock/analyze/${encodeURIComponent(analysisId)}`);
    },

    // ========== 投行研报 API ==========

    /**
     * 获取指定股票的共识评级
     * @param {string} symbol - 股票代码
     */
    async getConsensusRating(symbol) {
        return request(`/stock/research/consensus/${encodeURIComponent(symbol)}`);
    },

    /**
     * 获取指定股票的分析师评级列表
     * @param {string} symbol - 股票代码
     * @param {string} [source] - 按数据源筛选
     */
    async getAnalystRatings(symbol, source) {
        const params = new URLSearchParams();
        if (source) params.set("source", source);
        const qs = params.toString();
        return request(`/stock/research/ratings/${encodeURIComponent(symbol)}${qs ? '?' + qs : ''}`);
    },

    // ========== 社交内容生成与发布 API ==========

    /**
     * 根据推演结果生成指定平台格式内容
     * @param {string} analysisId - 推演结果 ID
     * @param {string} platform - 目标平台 xhs/weibo/xueqiu/zhihu
     */
    async generateSocialContent(analysisId, platform) {
        return request("/content/generate", {
            method: "POST",
            body: JSON.stringify({ analysis_id: analysisId, platform }),
        });
    },

    /**
     * 生成每日股市速报
     * @param {Object} [params] - { platform, include_analysis }
     */
    async generateDailyReport(params = {}) {
        return request("/content/daily-report", {
            method: "POST",
            body: JSON.stringify(params),
        });
    },

    /**
     * 获取当日最新速报内容
     */
    async getDailyReportLatest() {
        return request("/content/daily-report/latest");
    },

    /**
     * 获取历史速报列表
     * @param {number} [limit=20]
     * @param {number} [offset=0]
     */
    async getDailyReportHistory(limit = 20, offset = 0) {
        return request(`/content/daily-report/history?limit=${limit}&offset=${offset}`);
    },

    /**
     * 一键发布速报到全平台
     */
    async publishDailyReportAllPlatforms() {
        return request("/content/daily-report/publish-all", { method: "POST" });
    },

    /**
     * 发布指定内容到小红书
     * @param {string} contentId - 内容 ID
     */
    async publishToXiaohongshu(contentId) {
        return request(`/content/publish/xhs?content_id=${encodeURIComponent(contentId)}`, {
            method: "POST",
        });
    },

    /**
     * 获取社交内容历史记录
     * @param {number} [limit=20]
     * @param {number} [offset=0]
     * @param {string} [platform] - 按平台筛选
     */
    async getSocialContentHistory(limit = 20, offset = 0, platform) {
        const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
        if (platform) params.set("platform", platform);
        return request(`/content/history?${params.toString()}`);
    },

    // ========== 散户情绪分析 API ==========

    /**
     * 获取情绪指数
     * @param {string|null} [stockCode=null] - 股票代码，为空时返回大盘情绪
     */
    async getSentimentIndex(stockCode = null) {
        if (stockCode) {
            return request(`/sentiment/index/${encodeURIComponent(stockCode)}`);
        }
        return request("/sentiment/index");
    },

    /**
     * 获取情绪指数历史数据
     * @param {string|null} [stockCode=null] - 股票代码，为空时返回大盘历史
     * @param {number} [days=30] - 历史天数
     */
    async getSentimentHistory(stockCode = null, days = 30) {
        const params = new URLSearchParams({ days: String(days) });
        if (stockCode) params.set("stock_code", stockCode);
        return request(`/sentiment/history?${params.toString()}`);
    },

    /**
     * 获取各情绪数据源采集状态
     */
    async getSentimentStatus() {
        return request("/sentiment/status");
    },

    /**
     * 手动触发一轮情绪采集和分析
     * @param {Object} [payload] - { stock_code, time_window_hours }
     */
    async triggerSentimentAnalysis(payload = {}) {
        return request("/sentiment/trigger", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },

    /**
     * 更新情绪分析各分项权重配置
     * @param {Object} weights - { comment_sentiment, baidu_vote, akshare_aggregate, news_sentiment, margin_trading }
     */
    async updateSentimentWeights(weights) {
        return request("/sentiment/weights", {
            method: "PUT",
            body: JSON.stringify(weights),
        });
    },

    // ========== 数据源管理 API ==========

    /**
     * 获取所有数据源配置状态
     */
    async getDataSourceConfig() {
        return request("/stock/datasource/config");
    },

    /**
     * 保存数据源配置
     * @param {Object} config - { sources: DataSourceConfig[] }
     */
    async saveDataSourceConfig(config) {
        return request("/stock/datasource/config", {
            method: "PUT",
            body: JSON.stringify(config),
        });
    },

    /**
     * 测试指定数据源连通性
     * @param {string} sourceId - 数据源 ID
     */
    async testDataSourceConnection(sourceId) {
        return request(`/stock/datasource/test/${encodeURIComponent(sourceId)}`, {
            method: "POST",
        });
    },
};