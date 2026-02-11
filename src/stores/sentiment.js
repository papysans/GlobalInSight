import { defineStore } from 'pinia';
import { api } from '../api';

/**
 * 散户情绪分析状态管理
 * 管理大盘/个股情绪指数、历史数据、数据源状态和权重配置。
 * Requirements: 9.21, 9.22, 9.23, 9.29
 */
export const useSentimentStore = defineStore('sentiment', {
    state: () => ({
        marketIndex: null,        // 大盘情绪指数 SentimentSnapshot（含 sub_scores）
        stockIndices: {},         // { stock_code: SentimentSnapshot }
        marketHistory: [],        // 大盘情绪历史 SentimentSnapshot[]
        stockHistory: {},         // { stock_code: SentimentSnapshot[] }
        sourceStatus: {
            crawler: {},          // 评论爬虫源状态
            aggregate: {},        // 聚合指标源状态
        },
        sentimentWeights: {},     // 各分项权重配置
        loading: false,
        error: null,
    }),

    actions: {
        /**
         * 获取大盘整体情绪指数
         */
        async fetchMarketIndex() {
            this.loading = true;
            this.error = null;
            try {
                const result = await api.getSentimentIndex();
                this.marketIndex = result.data || null;
            } catch (err) {
                this.error = err.message;
                console.error('Failed to fetch market sentiment index:', err);
            } finally {
                this.loading = false;
            }
        },

        /**
         * 获取个股情绪指数
         * @param {string} stockCode
         */
        async fetchStockIndex(stockCode) {
            this.loading = true;
            this.error = null;
            try {
                const result = await api.getSentimentIndex(stockCode);
                if (result.data) {
                    this.stockIndices[stockCode] = result.data;
                }
            } catch (err) {
                this.error = err.message;
                console.error(`Failed to fetch sentiment for ${stockCode}:`, err);
            } finally {
                this.loading = false;
            }
        },

        /**
         * 获取情绪指数历史数据
         * @param {string|null} stockCode - 为空时获取大盘历史
         * @param {number} [days=30]
         */
        async fetchHistory(stockCode = null, days = 30) {
            this.loading = true;
            this.error = null;
            try {
                const result = await api.getSentimentHistory(stockCode, days);
                const items = result.items || [];
                if (stockCode) {
                    this.stockHistory[stockCode] = items;
                } else {
                    this.marketHistory = items;
                }
            } catch (err) {
                this.error = err.message;
                console.error('Failed to fetch sentiment history:', err);
            } finally {
                this.loading = false;
            }
        },

        /**
         * 获取各数据源采集状态
         */
        async fetchSourceStatus() {
            try {
                const result = await api.getSentimentStatus();
                this.sourceStatus = {
                    crawler: result.crawler_sources || {},
                    aggregate: result.aggregate_sources || {},
                };
            } catch (err) {
                console.error('Failed to fetch source status:', err);
            }
        },

        /**
         * 手动触发一轮情绪采集和分析
         * @param {Object} [payload] - { stock_code, time_window_hours }
         */
        async triggerAnalysis(payload = {}) {
            this.loading = true;
            this.error = null;
            try {
                const result = await api.triggerSentimentAnalysis(payload);
                if (result.success && result.data) {
                    // 更新大盘或个股指数
                    if (payload.stock_code) {
                        this.stockIndices[payload.stock_code] = result.data;
                    } else {
                        this.marketIndex = result.data;
                    }
                }
                return result;
            } catch (err) {
                this.error = err.message;
                console.error('Failed to trigger sentiment analysis:', err);
                throw err;
            } finally {
                this.loading = false;
            }
        },

        /**
         * 更新各分项权重配置
         * @param {Object} weights - { comment_sentiment, baidu_vote, akshare_aggregate, news_sentiment, margin_trading }
         */
        async updateWeights(weights) {
            try {
                const result = await api.updateSentimentWeights(weights);
                if (result.current_weights) {
                    this.sentimentWeights = result.current_weights;
                }
                return result;
            } catch (err) {
                this.error = err.message;
                console.error('Failed to update sentiment weights:', err);
                throw err;
            }
        },
    },
});
