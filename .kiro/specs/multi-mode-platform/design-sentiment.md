# 设计文档：散户情绪分析

> 本文件是 design.md 拆分后的子文件。完整设计文档包含：
> - [design-overview.md](design-overview.md)  概述、依赖、策略、架构、数据库
> - [design-frontend.md](design-frontend.md)  前端组件、路由、状态管理
> - [design-backend-services.md](design-backend-services.md)  后端服务（爬虫、推演、内容生成、合规脱敏）
> - [design-sentiment.md](design-sentiment.md) — 散户情绪分析全链路
> - [design-data-models.md](design-data-models.md)  数据模型、正确性属性、错误处理、测试策略

#### 10. 散户情绪爬虫服务（`app/services/sentiment_crawler.py`）

采集主流股票讨论社区的散户评论数据，支持反爬对抗和增量采集：

```python
class ProxyPoolManager:
    """IP 代理池管理器，支持 HTTP/SOCKS5 代理轮换"""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []  # ["http://ip:port", "socks5://ip:port"]
        self.failed_proxies: Set[str] = set()
    
    def get_random_proxy(self) -> Optional[str]:
        """随机选择一个可用代理，排除已失败的"""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        return random.choice(available) if available else None
    
    def mark_failed(self, proxy: str):
        """标记代理为失败"""
        self.failed_proxies.add(proxy)
    
    def reset_failed(self):
        """定期重置失败代理列表，重新尝试"""
        self.failed_proxies.clear()


class CookiePoolManager:
    """Cookie 池管理器，维护多组有效 Cookie 轮换使用
    
    Cookie 获取方式：用户通过 SettingsView 的"情绪采集 Cookie 管理"面板手动导入。
    操作流程：
    1. 用户在浏览器中登录目标平台（雪球/同花顺）
    2. 打开浏览器开发者工具 → Network → 复制请求中的 Cookie 头
    3. 在设置页面的 Cookie 导入对话框中粘贴（支持多组，每行一组）
    4. 系统自动解析并验证 Cookie 有效性
    5. 有效 Cookie 加入轮换池，失效 Cookie 标记并提示用户更新
    
    不使用 Playwright 自动登录的原因：
    - 雪球/同花顺登录涉及短信验证码、滑块验证等，自动化成本高
    - 自动登录易触发平台风控，导致账号被封
    - 手动导入虽需用户操作，但更稳定可靠
    """
    
    def __init__(self):
        self.cookie_pool: Dict[str, List[Dict]] = {}  # source -> [cookie_dict, ...]
        self.cookie_status: Dict[str, List[bool]] = {}  # source -> [is_valid, ...]
    
    def get_cookie(self, source: str) -> Optional[Dict]:
        """获取指定数据源的一组有效 Cookie，轮换使用"""
    
    def mark_invalid(self, source: str, index: int):
        """标记某组 Cookie 为失效"""
    
    async def refresh_cookie(self, source: str, index: int) -> bool:
        """尝试刷新失效的 Cookie"""


class AdaptiveRateController:
    """请求频率自适应控制器"""
    
    def __init__(self, base_cooldown: float = 2.0):
        self.base_cooldown = base_cooldown
        self.current_cooldown: Dict[str, float] = {}
        self.consecutive_success: Dict[str, int] = {}
    
    def detect_anti_crawl(self, status_code: int, response_body: str) -> bool:
        """检测反爬信号：HTTP 403/429、验证码页面、空响应"""
        if status_code in (403, 429):
            return True
        if '验证码' in response_body or 'captcha' in response_body.lower():
            return True
        if len(response_body.strip()) == 0:
            return True
        return False
    
    def on_anti_crawl_detected(self, source: str):
        """检测到反爬信号时降速：cooldown 翻倍"""
        current = self.current_cooldown.get(source, self.base_cooldown)
        self.current_cooldown[source] = min(current * 2, 60.0)  # 最大 60 秒
        self.consecutive_success[source] = 0
    
    def on_success(self, source: str):
        """请求成功时计数，连续 3 次成功后恢复原速"""
        self.consecutive_success[source] = self.consecutive_success.get(source, 0) + 1
        if self.consecutive_success[source] >= 3:
            self.current_cooldown[source] = self.base_cooldown
    
    def get_cooldown(self, source: str) -> float:
        """获取当前数据源的 cooldown 间隔"""
        return self.current_cooldown.get(source, self.base_cooldown)


class SentimentCrawler:
    """散户情绪评论采集服务"""
    
    def __init__(self):
        self.proxy_pool = ProxyPoolManager()
        self.cookie_pool = CookiePoolManager()
        self.rate_controller = AdaptiveRateController(base_cooldown=2.0)
        self.source_ban_until: Dict[str, float] = {}  # source -> ban_expire_timestamp
        self.source_fail_count: Dict[str, int] = {}
        self.spam_keywords: List[str] = []  # 广告/垃圾关键词黑名单
    
    async def fetch_eastmoney_comments(self, stock_code: str = None,
                                        time_window_hours: int = 24) -> List[SentimentComment]:
        """采集东方财富股吧评论
        - stock_code 为 None 时采集综合讨论区
        - 增量采集：仅获取 time_window_hours 内的新评论
        - 通过 AKShare 或 HTTP 抓取东方财富股吧页面
        - 使用代理池和 Cookie 池
        """
    
    async def fetch_xueqiu_comments(self, stock_code: str = None,
                                     time_window_hours: int = 24) -> List[SentimentComment]:
        """采集雪球社区评论
        - 雪球反爬较严格，需 Cookie + User-Agent 轮换
        - 增量采集：基于时间窗口过滤
        """
    
    async def fetch_10jqka_comments(self, stock_code: str = None,
                                     time_window_hours: int = 24) -> List[SentimentComment]:
        """采集同花顺社区评论
        - 增量采集：基于时间窗口过滤
        """
    
    def clean_comments(self, comments: List[SentimentComment]) -> List[SentimentComment]:
        """评论基础清洗
        - 去除纯表情/纯符号评论（正则匹配）
        - 去除广告和垃圾内容（关键词黑名单过滤）
        - 去除重复评论（基于 content_hash 去重）
        """
    
    def is_source_banned(self, source: str) -> bool:
        """检查数据源是否处于封禁降级状态"""
        ban_until = self.source_ban_until.get(source, 0)
        return time.time() < ban_until
    
    def ban_source(self, source: str, duration_minutes: int = 30):
        """对数据源执行降级：暂停采集指定时长"""
        self.source_ban_until[source] = time.time() + duration_minutes * 60
    
    async def collect_comments(self, stock_code: str = None,
                                source_ids: List[str] = None,
                                time_window_hours: int = 24) -> List[SentimentComment]:
        """采集所有启用数据源的散户评论
        - 跳过处于封禁状态的数据源（使用缓存数据）
        - 并发采集各数据源
        - 清洗 + 去重
        - 持久化到数据库
        """
    
    def get_source_status(self) -> Dict[str, Dict]:
        """获取各数据源的采集状态
        返回：{source_id: {last_collected, success_rate, status: normal/throttled/banned}}
        """
```

#### 10A. 混合情绪数据源服务（`app/services/mixed_sentiment_data_service.py`）

采集 AKShare 聚合指标、百度投票、新闻情绪指数、融资融券等非爬虫数据源，与评论爬虫数据共同构成综合情绪指数：

```python
# 默认加权配置
DEFAULT_SENTIMENT_WEIGHTS = {
    "comment_sentiment": 0.40,   # 评论情绪分（LLM 分析散户评论）
    "baidu_vote": 0.20,          # 百度投票分（百度股市通看涨/看跌）
    "akshare_aggregate": 0.15,   # AKShare 聚合分（千股千评 + 人气榜）
    "news_sentiment": 0.15,      # 新闻情绪分（数库新闻情绪指数）
    "margin_trading": 0.10,      # 融资融券分（融资净买入变化率）
}

class MixedSentimentDataService:
    """混合情绪数据源采集服务，通过 AKShare 直接调用获取聚合指标
    所有 AKShare 调用使用 asyncio.to_thread() 包装，避免阻塞事件循环"""
    
    def __init__(self):
        self.weights = DEFAULT_SENTIMENT_WEIGHTS.copy()
    
    async def fetch_akshare_comment_metrics(self, stock_code: str = None) -> Dict:
        """采集 AKShare 千股千评和人气数据
        - stock_comment_em()：千股千评综合评分、关注度排名
        - stock_comment_detail_scrd_focus_em()：用户关注指数变化趋势
        - stock_hot_rank_em()：个股人气榜排名和人气值
        - stock_hot_keyword_em()：热门关键词（市场讨论焦点）
        返回归一化到 0-100 的聚合得分
        """
    
    async def fetch_baidu_vote(self, stock_code: str) -> Dict:
        """采集百度股市通散户投票数据
        - stock_zh_vote_baidu(stock_code)：看涨/看跌投票比例
        返回：{bullish_ratio, bearish_ratio, score}（score = bullish_ratio × 100）
        """
    
    async def fetch_news_sentiment_index(self) -> Dict:
        """采集数库 A 股新闻情绪指数
        - index_news_sentiment_scope()：基于新闻文本的市场情绪量化
        返回归一化到 0-100 的新闻情绪得分
        """
    
    async def fetch_margin_trading_data(self, stock_code: str = None) -> Dict:
        """采集融资融券数据
        - stock_margin_detail_szse() / stock_margin_detail_sse()：融资融券余额变化
        - 融资净买入增加 → 看多信号（得分偏高）
        - 融券净卖出增加 → 看空信号（得分偏低）
        返回归一化到 0-100 的融资融券情绪得分
        """
    
    async def fetch_xueqiu_heat_data(self, stock_code: str = None) -> Dict:
        """采集雪球平台热度数据（通过 AKShare，无需爬虫）
        - stock_hot_follow_xq()：雪球关注排行
        - stock_hot_tweet_xq()：雪球讨论排行
        返回热度数据（作为 AKShare 聚合分的补充输入）
        """
    
    async def collect_all_metrics(self, stock_code: str = None) -> Dict:
        """并发采集所有聚合指标数据源
        返回：{
            'baidu_vote_score': float | None,
            'akshare_aggregate_score': float | None,
            'news_sentiment_score': float | None,
            'margin_trading_score': float | None,
            'xueqiu_heat': dict | None,
            'source_availability': {source_id: bool}
        }
        每个数据源独立 try/except，失败返回 None 不影响其他源
        """
    
    def calculate_weighted_index(self, comment_score: float,
                                  metrics: Dict,
                                  custom_weights: Dict = None) -> Dict:
        """基于加权模型计算综合情绪指数
        - comment_score: 评论情绪分（来自 LLM 分析）
        - metrics: collect_all_metrics() 的返回值
        - custom_weights: 用户自定义权重（可选，覆盖默认权重）
        
        计算逻辑：
        1. 收集所有可用数据源的得分
        2. 不可用的数据源权重按比例分配给其他可用源
        3. 加权求和得到综合指数（0-100）
        
        返回：{
            'index_value': float,  # 综合指数
            'comment_sentiment_score': float | None,
            'baidu_vote_score': float | None,
            'akshare_aggregate_score': float | None,
            'news_sentiment_score': float | None,
            'margin_trading_score': float | None,
            'effective_weights': dict,  # 实际使用的权重（重分配后）
            'source_availability': dict
        }
        """
        weights = custom_weights or self.weights
        available_scores = {}
        total_weight = 0.0
        
        # 收集可用数据源
        score_map = {
            'comment_sentiment': comment_score,
            'baidu_vote': metrics.get('baidu_vote_score'),
            'akshare_aggregate': metrics.get('akshare_aggregate_score'),
            'news_sentiment': metrics.get('news_sentiment_score'),
            'margin_trading': metrics.get('margin_trading_score'),
        }
        
        for key, score in score_map.items():
            if score is not None:
                available_scores[key] = score
                total_weight += weights.get(key, 0)
        
        # 权重重分配：不可用源的权重按比例分配给可用源
        if total_weight > 0 and total_weight < 1.0:
            scale = 1.0 / total_weight
            effective_weights = {k: weights[k] * scale for k in available_scores}
        else:
            effective_weights = {k: weights.get(k, 0) for k in available_scores}
        
        # 加权求和
        index_value = sum(
            available_scores[k] * effective_weights[k]
            for k in available_scores
        )
        
        return {
            'index_value': max(0, min(100, index_value)),
            'comment_sentiment_score': comment_score,
            'baidu_vote_score': metrics.get('baidu_vote_score'),
            'akshare_aggregate_score': metrics.get('akshare_aggregate_score'),
            'news_sentiment_score': metrics.get('news_sentiment_score'),
            'margin_trading_score': metrics.get('margin_trading_score'),
            'effective_weights': effective_weights,
            'source_availability': metrics.get('source_availability', {}),
        }
    
    def update_weights(self, new_weights: Dict):
        """更新加权配置（从设置页面调用）"""
        self.weights.update(new_weights)
```

#### 11. 散户情绪分析服务（`app/services/sentiment_analyzer.py`）

基于 LLM 对散户评论进行情绪分析，结合混合数据源计算综合恐慌/贪婪指数：

```python
class SentimentAnalyzer:
    """散户情绪分析与综合指数计算服务"""
    
    def __init__(self):
        self.crawler = SentimentCrawler()
        self.mixed_data_service = MixedSentimentDataService()
        self.batch_size = 50  # 每批 LLM 分析的评论数
    
    async def analyze_batch(self, comments: List[SentimentComment]) -> List[SentimentComment]:
        """批量调用 LLM 对评论进行情绪分类
        - 将多条评论合并为一次 LLM 调用（每批最多 50 条）
        - 每条评论标记为 fear/greed/neutral
        - 给出 0-100 的情绪强度分数
        - 返回更新了 sentiment_label 和 sentiment_score 的评论列表
        
        LLM Prompt 模板：
        ```
        你是一个专业的股票市场情绪分析师。请对以下散户评论进行情绪分类。
        对每条评论，判断其情绪倾向并给出分数：
        - fear（恐慌）：表达担忧、恐惧、看空、割肉等负面情绪，分数 0-33
        - neutral（中性）：客观讨论、提问、无明显情绪倾向，分数 34-66
        - greed（贪婪）：表达乐观、看多、追涨、暴富等正面情绪，分数 67-100
        
        请以 JSON 数组格式返回结果：
        [{"index": 0, "label": "fear|neutral|greed", "score": 0-100}, ...]
        ```
        """
    
    def calculate_index(self, comments: List[SentimentComment],
                        mixed_metrics: Dict = None,
                        custom_weights: Dict = None) -> SentimentSnapshot:
        """基于混合数据源计算综合情绪指数
        - 先计算评论情绪分：greed_count / total_count * 100
        - 再调用 mixed_data_service.calculate_weighted_index() 加权合并所有数据源
        - 生成包含综合指数和各分项得分的 SentimentSnapshot
        """
    
    async def get_latest_index(self, stock_code: str = None) -> Optional[SentimentSnapshot]:
        """获取最新的情绪指数快照
        - stock_code 为 None 时返回大盘整体指数
        - 从数据库查询最新的 snapshot
        """
    
    async def get_index_history(self, stock_code: str = None,
                                 days: int = 30) -> List[SentimentSnapshot]:
        """获取情绪指数历史数据（用于时序图表）
        - 返回指定天数内的所有快照
        - 按 snapshot_time 升序排列
        """
    
    async def run_analysis_cycle(self, stock_code: str = None,
                                  time_window_hours: int = 24):
        """执行一轮完整的情绪采集和分析（混合数据源）
        1. 调用 crawler.collect_comments() 采集评论
        2. 调用 analyze_batch() 批量情绪分析
        3. 调用 mixed_data_service.collect_all_metrics() 采集聚合指标
        4. 调用 calculate_index(comments, mixed_metrics) 计算综合指数
        5. 持久化 snapshot 到数据库（含各分项得分和数据源可用性）
        6. 持久化评论到数据库
        """
    
    async def get_sentiment_context(self, stock_code: str = None) -> Dict:
        """获取情绪上下文数据，供行情推演引用
        返回：{index_value, sub_scores: {comment, baidu_vote, akshare, news, margin},
               trend_direction(up/down/stable), sample_count, label, source_availability}
        - trend_direction 基于最近 3 个快照的趋势判断
        """
    
    async def cleanup_old_comments(self, retention_days: int = 90):
        """清理超过 retention_days 的原始评论数据
        - 仅删除 sentiment_comments 表中的旧数据
        - sentiment_snapshots 表的聚合数据永久保留
        """
```

#### 12. 情绪分析 API 端点（`app/api/sentiment_endpoints.py`）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/sentiment/index` | GET | 获取大盘整体情绪指数（含综合指数和各分项得分） |
| `/api/sentiment/index/{stock_code}` | GET | 获取指定股票的情绪指数（含综合指数和各分项得分） |
| `/api/sentiment/history` | GET | 获取情绪指数历史数据，支持 stock_code/days 参数 |
| `/api/sentiment/comments` | GET | 获取最近的评论样本，支持 stock_code/limit 参数 |
| `/api/sentiment/status` | GET | 获取各情绪数据源的采集状态（分评论爬虫源和聚合指标源两组） |
| `/api/sentiment/trigger` | POST | 手动触发一轮情绪采集和分析 |
| `/api/sentiment/weights` | PUT | 更新各分项权重配置 |

#### 13. 情绪采集定时任务集成

在现有 SchedulerService 中新增情绪采集定时任务：

```python
# 在 SchedulerService.start() 中新增
self.scheduler.add_job(
    self.run_sentiment_analysis,
    'interval', hours=2,  # 默认每 2 小时
    id='sentiment_analysis',
    replace_existing=True
)

async def run_sentiment_analysis(self):
    """定时执行情绪采集和分析
    - 采集大盘综合讨论区评论 → 分析 → 生成大盘情绪快照
    - 采集热门个股讨论区评论 → 分析 → 生成个股情绪快照
    """

def update_sentiment_schedule(self, interval_hours: int = 2):
    """更新情绪采集频率（从设置页面调用）"""
    self.scheduler.reschedule_job(
        'sentiment_analysis',
        trigger='interval', hours=interval_hours
    )
```

#### 14. 行情推演服务集成情绪数据

更新 StockAnalysisService，在推演流程中引用情绪数据：

```python
# 在 StockAnalysisService.analyze() 中
# Step 0（新增）: 获取情绪上下文
sentiment_context = await self.sentiment_analyzer.get_sentiment_context(stock_code)

# Step 2: 影响分析 Agent 的 prompt 中注入情绪数据
impact_prompt = f"""
...现有 prompt...
当前散户情绪参考数据（混合数据源综合分析）：
- 综合情绪指数：{sentiment_context['index_value']}（{sentiment_context['label']}）
- 评论情绪分：{sentiment_context['sub_scores']['comment']}
- 百度投票看涨比例：{sentiment_context['sub_scores']['baidu_vote']}
- 新闻情绪分：{sentiment_context['sub_scores']['news']}
- 融资融券信号：{sentiment_context['sub_scores']['margin']}
- 趋势方向：{sentiment_context['trend_direction']}
- 样本量：{sentiment_context['sample_count']}
请在分析中综合引用散户情绪状态和各分项数据。
"""

# 推演结果新增 sentiment_context 字段
result.sentiment_context = sentiment_context
```

#### 15. 前端情绪指数组件

**SentimentGauge 仪表盘组件（`src/components/SentimentGauge.vue`）：**
- 使用 ECharts gauge 图表展示情绪指数（0-100）
- 颜色渐变：红色（0-20 极度恐慌）→ 橙色（20-40 恐慌）→ 黄色（40-60 中性）→ 浅绿（60-80 贪婪）→ 深绿（80-100 极度贪婪）
- 支持 mini 模式（用于推演页面旁的迷你仪表盘）和 full 模式（用于热榜页面顶部）
- Props: `indexValue`, `label`, `size`（mini/full）

**SentimentChart 时序图表组件（`src/components/SentimentChart.vue`）：**
- 使用 ECharts K 线风格折线图展示情绪指数历史趋势
- X 轴：时间，Y 轴：指数值（0-100）
- 背景色分区：红色区域（0-20）、黄色区域（40-60）、绿色区域（80-100）
- 支持缩放（dataZoom）和时间范围选择（7天/14天/30天）
- 支持切换显示综合指数或各分项指数（评论情绪/百度投票/AKShare 聚合/新闻情绪/融资融券），多线叠加对比
- 关键事件节点标注（指数突破 80 或跌破 20 时）
- 鼠标悬停 tooltip 显示该时间点的综合指数、各分项得分和代表性评论摘要
- Props: `historyData`, `stockCode`, `showSubScores`

**前端 API 层新增（`src/api/index.js`）：**
```javascript
// 情绪分析
async getSentimentIndex(stockCode = null) { ... }
async getSentimentHistory(stockCode = null, days = 30) { ... }
async getSentimentStatus() { ... }
async triggerSentimentAnalysis() { ... }
async updateSentimentWeights(weights) { ... }
```

**前端状态管理新增（`src/stores/sentiment.js`）：**
```javascript
export const useSentimentStore = defineStore('sentiment', {
  state: () => ({
    marketIndex: null,        // 大盘情绪指数 SentimentSnapshot（含 sub_scores）
    stockIndices: {},         // {stock_code: SentimentSnapshot}
    marketHistory: [],        // 大盘情绪历史 SentimentSnapshot[]
    stockHistory: {},         // {stock_code: SentimentSnapshot[]}
    sourceStatus: {},         // 各数据源采集状态（分 crawler 和 aggregate 两组）
    sentimentWeights: {},     // 各分项权重配置
    loading: false,
    error: null,
  }),
  actions: {
    async fetchMarketIndex() { ... },
    async fetchStockIndex(stockCode) { ... },
    async fetchHistory(stockCode, days) { ... },
    async fetchSourceStatus() { ... },
    async triggerAnalysis() { ... },
    async updateWeights(weights) { ... },
  },
})
```

**StockHotView 集成：**
- 页面顶部新增大盘情绪仪表盘（SentimentGauge full 模式）
- 个股详情面板中新增个股情绪指数和趋势图

**StockAnalysisView 集成：**
- 输入区域旁新增迷你情绪仪表盘（SentimentGauge mini 模式）
- 推演结果中展示 sentiment_context 数据

**SettingsView 集成：**
- 新增情绪采集配置区域：采集频率设置、代理池配置、数据源启用/禁用（分"评论采集源"和"聚合指标源"两组）
- 新增各分项权重配置（滑块或数字输入，总和自动归一化为 100%）
- 新增采集状态监控面板（评论爬虫状态 + 聚合指标 AKShare 调用状态）
