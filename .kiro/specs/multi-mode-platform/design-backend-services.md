# 设计文档：后端服务

> 本文件是 design.md 拆分后的子文件。完整设计文档包含：
> - [design-overview.md](design-overview.md)  概述、依赖、策略、架构、数据库
> - [design-frontend.md](design-frontend.md)  前端组件、路由、状态管理
> - [design-backend-services.md](design-backend-services.md)  后端服务（爬虫、推演、内容生成、合规脱敏）
> - [design-sentiment.md](design-sentiment.md) — 散户情绪分析全链路
> - [design-data-models.md](design-data-models.md)  数据模型、正确性属性、错误处理、测试策略

### 后端接口

#### 1. 股票资讯路由（`app/api/stock_endpoints.py`）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/stock/news` | GET | 获取股票热点资讯列表，支持 limit/source/category/force_refresh 参数；category 支持 domestic/international/research_report |
| `/api/stock/sources` | GET | 获取支持的数据源列表及状态（含国内、国际、研报三类） |
| `/api/stock/analyze` | POST | 触发行情推演，SSE 流式返回各步骤输出 |
| `/api/stock/analyze/history` | GET | 获取历史推演记录列表 |
| `/api/stock/analyze/{analysis_id}` | GET | 获取单条推演结果详情 |
| `/api/stock/research/consensus/{symbol}` | GET | 获取指定股票的共识评级（汇总所有投行分析师评级） |
| `/api/stock/research/ratings/{symbol}` | GET | 获取指定股票的分析师评级列表，支持 source 参数筛选 |

#### 2. 社交内容路由（`app/api/content_endpoints.py`）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/content/generate` | POST | 根据推演结果生成指定平台格式的社交内容 |
| `/api/content/daily-report` | POST | 生成每日股市速报内容 |
| `/api/content/daily-report/latest` | GET | 获取当日最新速报内容 |
| `/api/content/daily-report/history` | GET | 获取历史速报列表，支持 limit/offset 参数 |
| `/api/content/daily-report/publish-all` | POST | 一键发布速报到全平台（当前 = 小红书） |
| `/api/content/publish/xhs` | POST | 一键发布到小红书（调用 XHS MCP） |
| `/api/content/history` | GET | 获取历史生成/发布记录 |
| `/api/content/{content_id}` | GET | 获取单条内容详情 |
| `/api/content/{content_id}` | PUT | 更新/编辑已生成的内容 |

#### 3. 数据源管理路由（`app/api/stock_endpoints.py` 扩展）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/stock/datasource/config` | GET | 获取所有数据源的配置状态（启用/禁用、API Key 是否已配置） |
| `/api/stock/datasource/config` | PUT | 保存数据源配置（API Key、启用/禁用状态） |
| `/api/stock/datasource/test/{source_id}` | POST | 测试指定数据源的 API Key 连通性，返回成功/失败和延迟信息 |

#### 4. 股票爬虫服务（`app/services/stock_news_collector.py`）

遵循现有 `TopHubCollector` 的设计模式：

```python
class SourceRateLimitConfig(BaseModel):
    """每个数据源的独立限速配置"""
    max_concurrent: int = 3          # 该源最大并发数
    cooldown_seconds: float = 1.0    # 请求间隔冷却时间（秒）
    is_high_risk: bool = False       # 是否为高风险源（Tier 4 / 反爬风险高）

class RateLimiter:
    """全局请求速率限制器，基于 asyncio.Semaphore + 每源独立 cooldown"""
    
    def __init__(self, global_max_concurrent: int = 10):
        self.global_semaphore = asyncio.Semaphore(global_max_concurrent)
        self.source_configs: Dict[str, SourceRateLimitConfig] = {}
        self.source_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.source_last_request: Dict[str, float] = {}
        self.source_fail_count: Dict[str, int] = {}
    
    def configure_source(self, source_id: str, config: SourceRateLimitConfig):
        """为指定数据源配置限速参数"""
        self.source_configs[source_id] = config
        self.source_semaphores[source_id] = asyncio.Semaphore(config.max_concurrent)
        self.source_fail_count[source_id] = 0
    
    async def acquire(self, source_id: str):
        """获取请求许可：全局信号量 + 源级信号量 + cooldown 等待"""
        await self.global_semaphore.acquire()
        if source_id in self.source_semaphores:
            await self.source_semaphores[source_id].acquire()
        # 执行 cooldown 等待
        config = self.source_configs.get(source_id)
        if config:
            last = self.source_last_request.get(source_id, 0)
            elapsed = time.time() - last
            if elapsed < config.cooldown_seconds:
                await asyncio.sleep(config.cooldown_seconds - elapsed)
        self.source_last_request[source_id] = time.time()
    
    def release(self, source_id: str):
        """释放请求许可"""
        self.global_semaphore.release()
        if source_id in self.source_semaphores:
            self.source_semaphores[source_id].release()
    
    async def handle_failure(self, source_id: str) -> bool:
        """高风险源失败时执行指数退避策略
        - 第一次失败：等待 5 秒后重试
        - 第二次失败：等待 15 秒后重试
        - 第三次失败：跳过该源，返回 False
        返回 True 表示可以重试，False 表示应跳过
        """
        config = self.source_configs.get(source_id)
        if not config or not config.is_high_risk:
            return False  # 非高风险源不做指数退避
        
        self.source_fail_count[source_id] = self.source_fail_count.get(source_id, 0) + 1
        fail_count = self.source_fail_count[source_id]
        
        if fail_count == 1:
            await asyncio.sleep(5)
            return True
        elif fail_count == 2:
            await asyncio.sleep(15)
            return True
        else:
            # 第三次失败，跳过该源
            return False
    
    def reset_fail_count(self, source_id: str):
        """请求成功后重置失败计数"""
        self.source_fail_count[source_id] = 0

# 默认限速配置
DEFAULT_RATE_LIMIT_CONFIGS = {
    "akshare": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=0.5, is_high_risk=False),
    "sina": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=1.0, is_high_risk=False),
    "10jqka": SourceRateLimitConfig(max_concurrent=2, cooldown_seconds=2.0, is_high_risk=False),
    "xueqiu": SourceRateLimitConfig(max_concurrent=2, cooldown_seconds=3.0, is_high_risk=True),
    "tushare": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=1.0, is_high_risk=False),
    "finnhub": SourceRateLimitConfig(max_concurrent=3, cooldown_seconds=1.0, is_high_risk=False),
    "newsapi": SourceRateLimitConfig(max_concurrent=2, cooldown_seconds=2.0, is_high_risk=False),
    "tipranks": SourceRateLimitConfig(max_concurrent=1, cooldown_seconds=5.0, is_high_risk=True),
    "marketbeat": SourceRateLimitConfig(max_concurrent=1, cooldown_seconds=5.0, is_high_risk=True),
    "simplywallst": SourceRateLimitConfig(max_concurrent=1, cooldown_seconds=5.0, is_high_risk=True),
    "last10k": SourceRateLimitConfig(max_concurrent=1, cooldown_seconds=5.0, is_high_risk=True),
    "wisesheets": SourceRateLimitConfig(max_concurrent=1, cooldown_seconds=5.0, is_high_risk=True),
}

class StockNewsCollector:
    def __init__(self, use_cache=True):
        self.sources = STOCK_SOURCES  # 数据源配置
        self.cache_service = hot_news_cache
        self.intl_news_service = InternationalNewsService(use_cache=use_cache)
        self.research_service = ResearchReportService(use_cache=use_cache)
        self.rate_limiter = RateLimiter(global_max_concurrent=10)
        # 初始化各数据源限速配置
        for source_id, config in DEFAULT_RATE_LIMIT_CONFIGS.items():
            self.rate_limiter.configure_source(source_id, config)
    
    async def fetch_akshare_news(self) -> List[StockNewsItem]:
        """通过 AKShare 库采集东方财富股票资讯（主要数据源）
        所有 AKShare 调用使用 asyncio.to_thread() 包装，避免阻塞事件循环"""
        # df = await asyncio.to_thread(ak.stock_news_em)
        # hot_rank = await asyncio.to_thread(ak.stock_hot_rank_em)
    
    async def fetch_sina_news(self) -> List[StockNewsItem]:
        """通过 HTTP API 采集新浪财经资讯"""
        # httpx.AsyncClient 请求新浪财经 API
    
    async def fetch_10jqka_news(self) -> List[StockNewsItem]:
        """采集同花顺热股排行数据"""
        # httpx.AsyncClient + 解析
    
    async def fetch_xueqiu_news(self) -> List[StockNewsItem]:
        """采集雪球热帖数据（需处理反爬）"""
        # httpx.AsyncClient + cookie/header 处理
    
    async def collect_news(self, source_ids=None, force_refresh=False, 
                           include_international=True, include_research=True) -> Dict:
        """采集所有数据源的股票资讯（含国内、国际、投行研报）
        - 缓存检查 → 并发采集国内源 + 国际源 + 投行研报 → 结果合并 → 缓存保存
        - include_international: 是否包含国际财经新闻
        - include_research: 是否包含投行研报数据
        - 返回结果中以 category 字段区分：domestic/international/research_report
        """
```

支持的数据源（初始版本）：
- **AKShare（akshare）**：主要数据源，通过 Python 库直接调用（所有调用使用 `asyncio.to_thread()` 包装）。使用 `stock_news_em()` 获取东方财富财经要闻，`stock_hot_rank_em()` 获取热股排行，`stock_board_concept_name_em()` 获取概念板块数据。重点采集 A 股和港股相关资讯
- **新浪财经（sina）**：通过 HTTP API 获取实时财经新闻和股票行情数据
- **同花顺（10jqka）**：热股排行、概念板块热度数据
- **雪球（xueqiu）**：热帖排行、今日话题（需处理反爬机制）
- **Tushare（tushare）**：免费层 API，获取新闻快讯和公告数据（需注册获取 token）

#### 5. 国际财经新闻服务（`app/services/international_news_service.py`）

采集国际主流财经媒体新闻，为行情推演提供全球视角：

```python
class InternationalNewsService:
    """国际财经新闻采集服务，聚合多个免费/免费层 API"""
    
    def __init__(self, use_cache=True):
        self.cache_service = hot_news_cache
        self.llm = None  # 延迟初始化，用于英文摘要翻译
    
    async def fetch_finnhub_news(self, category: str = "general") -> List[StockNewsItem]:
        """通过 Finnhub API 采集国际财经新闻
        - 免费层：60 calls/min
        - 端点：/api/v1/news?category=general（通用财经新闻）
        - 端点：/api/v1/company-news?symbol=AAPL（个股新闻）
        - 聚合来源：Reuters, CNBC, MarketWatch, Bloomberg-adjacent
        - 需要 API Key（免费注册获取）
        """
    
    async def fetch_newsapi_news(self, query: str = "stock market") -> List[StockNewsItem]:
        """通过 NewsAPI 采集国际财经新闻
        - 免费开发者层：100 requests/day
        - 覆盖：Bloomberg, Reuters, CNBC, Financial Times, WSJ, The Economist
        - 支持按关键词、来源、语言筛选
        - 需要 API Key（免费注册获取）
        """
    
    async def fetch_alpha_vantage_news(self, tickers: str = None) -> List[StockNewsItem]:
        """通过 Alpha Vantage NEWS_SENTIMENT 端点采集新闻
        - 免费层：25 requests/day
        - 提供新闻 + 情绪分析评分（bullish/bearish/neutral）
        - 支持按 ticker 和主题筛选
        - 需要 API Key（免费注册获取）
        """
    
    async def fetch_gdelt_news(self, theme: str = "ECON_STOCKMARKET") -> List[StockNewsItem]:
        """通过 GDELT Project API 采集全球金融新闻
        - 完全免费，无需 API Key
        - GKG API：按主题（ECON_STOCKMARKET, ECON_BANKRUPTCY 等）获取新闻
        - DOC API：全文搜索全球新闻
        - 数据量大，需做去重和相关性过滤
        """
    
    async def fetch_google_news_rss(self, query: str = "stock market finance") -> List[StockNewsItem]:
        """通过 Google News RSS feed 采集财经新闻
        - 完全免费，无需 API Key
        - 使用 feedparser 解析 RSS
        - URL: https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en
        - 支持按关键词和地区过滤
        """
    
    async def fetch_marketaux_news(self, symbols: str = None) -> List[StockNewsItem]:
        """通过 Marketaux API 采集金融新闻
        - 免费层：100 requests/day
        - 提供新闻 + 情绪分析标签
        - 支持按 symbol 和行业筛选
        - 需要 API Key（免费注册获取）
        """
    
    async def batch_translate_to_chinese(self, news_items: List[StockNewsItem], max_items: int = 20) -> List[StockNewsItem]:
        """批量调用 LLM 将多条英文新闻翻译为中文摘要
        - 将多条新闻合并为一次 LLM 调用，减少 API 调用次数
        - 每批最多 max_items 条（默认 20），超出时分批处理
        - LLM prompt 中强调"严格基于原文翻译，不添加任何原文没有的信息"
        - 保留关键数据和数字
        - 生成简洁的中文摘要（每条 100-200字）
        - 标注原始语言为英文
        - 在返回的 StockNewsItem 中标记 is_ai_translated=True，供前端展示"AI 翻译摘要"标签
        - 返回更新了 summary 字段的 news_items 列表
        
        LLM Prompt 模板：
        ```
        你是一个专业的财经新闻翻译助手。请严格基于以下英文新闻原文进行翻译，
        不添加任何原文没有的信息，不做任何推测或补充。
        保留所有数字、公司名称、股票代码等关键数据。
        每条新闻生成 100-200 字的中文摘要。
        ```
        """
    
    async def collect_international_news(self, source_ids: List[str] = None, 
                                          force_refresh: bool = False) -> List[StockNewsItem]:
        """采集所有国际财经新闻源
        - 缓存检查（cache_key 前缀：intl_news_）
        - 并发采集所有启用的数据源
        - 英文内容通过 batch_translate_to_chinese() 批量翻译为中文摘要
        - 结果合并、去重、按时间排序
        """
```

支持的国际财经数据源：
- **Finnhub（finnhub）**：主要国际新闻源，聚合 Reuters/CNBC/MarketWatch 等，免费层 60 calls/min，需 API Key
- **NewsAPI（newsapi）**：覆盖面最广，Bloomberg/Reuters/CNBC/FT/WSJ，免费层 100 requests/day，需 API Key
- **Alpha Vantage（alpha_vantage）**：新闻 + 情绪分析，免费层 25 requests/day，需 API Key
- **GDELT Project（gdelt）**：完全免费，全球新闻监控，数据量大需过滤
- **Google News RSS（google_rss）**：完全免费，通过 RSS feed 获取，使用 feedparser 解析
- **Marketaux（marketaux）**：金融新闻 + 情绪标签，免费层 100 requests/day，需 API Key

API Key 配置：所有需要 API Key 的服务通过 `.env` 文件配置（`FINNHUB_API_KEY`、`NEWSAPI_API_KEY`、`ALPHA_VANTAGE_API_KEY`、`MARKETAUX_API_KEY`），未配置的数据源自动跳过。

#### 6. 投行研报与分析师评级服务（`app/services/research_report_service.py`）

采集主流投行分析师评级、目标价和研报摘要，为行情推演提供机构视角。采用分层优先级和降级策略：

```python
class AnalystRating(BaseModel):
    """分析师评级数据模型"""
    analyst_name: str              # 分析师姓名
    firm: str                      # 所属机构（如 "JP Morgan", "Goldman Sachs"）
    rating: str                    # 评级（Buy/Hold/Sell/Overweight/Underweight 等）
    rating_normalized: str         # 标准化评级（buy/hold/sell）
    target_price: Optional[float]  # 目标价
    previous_target: Optional[float]  # 前次目标价
    currency: str = "USD"          # 货币
    date: str                      # 评级日期
    stock_symbol: str              # 股票代码
    stock_name: str                # 股票名称
    action: Optional[str]          # 动作（upgrade/downgrade/maintain/initiate）
    summary: Optional[str]         # 研报摘要

# 数据源分层优先级配置
RESEARCH_SOURCE_TIERS = {
    1: ["finnhub_research", "yahoo"],       # Tier 1: 核心免费源，始终启用
    2: ["finviz", "zacks"],                  # Tier 2: 免费层可用，良好补充
    3: ["benzinga", "seekingalpha"],          # Tier 3: 需付费 API Key，可选
    4: ["tipranks", "marketbeat", "simplywallst", "last10k", "wisesheets"],  # Tier 4: 高反爬风险，尽力而为
}

class ResearchReportService:
    """投行研报与分析师评级采集服务，支持分层优先级和降级策略"""
    
    def __init__(self, use_cache=True):
        self.cache_service = hot_news_cache
        self.llm = None
    
    async def fetch_finnhub_recommendations(self, symbol: str) -> List[AnalystRating]:
        """【Tier 1 主要源】通过 Finnhub API 采集分析师推荐趋势
        - 端点：/stock/recommendation?symbol={symbol}
        - 返回结构化数据：buy/hold/sell/strongBuy/strongSell 计数（按月）
        - 端点：/stock/earnings?symbol={symbol} 获取盈利惊喜数据
        - 免费层 60 calls/min，需 API Key（免费注册）
        - 作为分析师评级的首选数据源
        """
    
    async def fetch_yahoo_finance_ratings(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 1】通过 yfinance 库采集 Yahoo Finance 分析师数据
        - 完全免费，使用 yfinance Python 库，无需 API Key
        - ticker.recommendations：分析师推荐历史
        - ticker.analyst_price_targets：目标价数据
        - ticker.recommendations_summary：评级汇总
        """
    
    async def fetch_finviz_ratings(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 2】从 Finviz 采集分析师目标价和评级
        - 免费 HTML 抓取
        - 提供分析师目标价、评级概览
        """
    
    async def fetch_zacks_ratings(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 2】从 Zacks 采集分析师评级排名
        - 免费层可获取基本评级信息（Zacks Rank 1-5）
        - 提供盈利预测
        """
    
    async def fetch_benzinga_ratings(self) -> List[AnalystRating]:
        """【Tier 3】从 Benzinga 采集分析师评级动态
        - 提供实时升降级动态（upgrades/downgrades）
        - 需付费 API Key 获取完整访问
        """
    
    async def fetch_seeking_alpha_ratings(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 3】从 Seeking Alpha 采集分析师文章和评级
        - 部分免费，提供分析师文章摘要
        """
    
    async def fetch_tipranks_ratings(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 4 尽力而为】从 TipRanks 采集分析师评级
        - 聚合 JP Morgan, Goldman Sachs, Morgan Stanley 等主流投行
        - 通过 HTTP 请求 + JSON 解析（非官方 API）
        - 高反爬风险，失败时静默跳过
        """
    
    async def fetch_marketbeat_ratings(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 4 尽力而为】从 MarketBeat 采集分析师评级
        - 分析师评级和目标价聚合器
        - 通过 HTTP 请求 + HTML 解析
        - 高反爬风险，失败时静默跳过
        """
    
    async def fetch_simply_wall_st(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 4 尽力而为】从 Simply Wall St 采集分析师预测
        - 免费层可获取基本估值分析和分析师预测
        - 高反爬风险，失败时静默跳过
        """
    
    async def fetch_last10k_summaries(self, symbol: str = None) -> List[Dict]:
        """【Tier 4 尽力而为】从 Last10K 采集 SEC 财报 AI 摘要
        - 免费层可用
        - 高反爬风险，失败时静默跳过
        """
    
    async def fetch_wisesheets_reports(self, symbol: str = None) -> List[AnalystRating]:
        """【Tier 4 尽力而为】从 Wisesheets 采集投行研报摘要
        - 高反爬风险，失败时静默跳过
        """
    
    async def normalize_rating(self, raw_rating: str) -> str:
        """将各平台的评级标准化为 buy/hold/sell
        - Buy/Overweight/Outperform/Strong Buy → buy
        - Hold/Neutral/Equal-Weight/Market Perform → hold
        - Sell/Underweight/Underperform/Strong Sell → sell
        """
    
    async def collect_research_reports(self, symbols: List[str] = None,
                                        source_ids: List[str] = None,
                                        force_refresh: bool = False) -> Dict:
        """按分层优先级采集所有投行研报数据源，支持降级策略
        - 缓存检查（cache_key 前缀：research_）
        - 按 Tier 1 → Tier 2 → Tier 3 → Tier 4 顺序采集
        - Tier 1（Finnhub + Yahoo Finance）作为核心源始终尝试
        - 每层内并发采集，层间按优先级顺序执行
        - 高优先级层成功后仍尝试低优先级层以补充数据
        - Tier 4 源失败时静默跳过（记录 debug 日志）
        - 所有层均失败时返回空结果并附带 tier_status 信息
        - 评级标准化（buy/hold/sell）
        - 结果合并、去重、按日期排序
        - 生成共识评级汇总
        - 返回结果包含 tier_status: Dict[int, str] 记录每层采集状态
        """
    
    async def get_consensus_rating(self, symbol: str) -> Dict:
        """计算某只股票的共识评级
        - 汇总所有来源的分析师评级
        - 计算 buy/hold/sell 占比
        - 计算平均目标价和目标价区间
        """
    
    def convert_to_news_items(self, ratings: List[AnalystRating]) -> List[StockNewsItem]:
        """将分析师评级转换为 StockNewsItem 格式，以便在热榜中统一展示
        - title: "{firm} {action} {stock_name}: {rating}, 目标价 ${target_price}"
        - summary: 包含评级详情和目标价变动
        - source_platform: "research_{source}"
        - category: "research_report"
        """
```

支持的投行研报数据源（按优先级分层）：
- **Tier 1 核心免费源（始终启用）：**
  - **Finnhub Research（finnhub_research）**：`/stock/recommendation` 端点返回结构化 buy/hold/sell/strongBuy/strongSell 计数，`/stock/earnings` 提供盈利惊喜数据，免费层 60 calls/min，需 API Key（免费注册），**分析师评级首选数据源**
  - **Yahoo Finance（yahoo）**：完全免费，通过 yfinance 库获取 `ticker.recommendations`、`ticker.analyst_price_targets`、`ticker.recommendations_summary`，无需 API Key
- **Tier 2 免费层可用（良好补充）：**
  - **Finviz（finviz）**：免费 HTML 抓取，分析师目标价和评级概览
  - **Zacks（zacks）**：免费层基本评级信息（Zacks Rank 1-5），盈利预测
- **Tier 3 需付费 API Key（可选）：**
  - **Benzinga（benzinga）**：实时升降级动态，需付费 API Key（通过 `.env` 配置 `BENZINGA_API_KEY`）
  - **Seeking Alpha（seekingalpha）**：分析师文章和评级，部分免费（通过 `.env` 配置 `SEEKING_ALPHA_API_KEY`）
- **Tier 4 高反爬风险（尽力而为）：**
  - **TipRanks（tipranks）**、**MarketBeat（marketbeat）**、**Simply Wall St（simplywallst）**、**Last10K（last10k）**、**Wisesheets（wisesheets）**：均需 HTML 抓取，反爬风险高，失败时静默跳过不影响系统运行

#### 7. 行情推演服务（`app/services/stock_analysis_service.py`）

参考现有 `app/services/workflow.py` 的 LangGraph 工作流模式：

```python
class StockAnalysisService:
    async def analyze(self, request: StockAnalysisRequest):
        """执行行情推演，yield SSE 事件
        - request.topic: 用户输入的推演主题
        - request.debate_rounds: 辩论轮数
        - request.news_items: 可选的关联资讯（从热榜带入时使用）
        """
        # Step 0: 情绪数据获取（核心引擎输入）→ yield step event
        # Step 1: 资讯汇总 → yield step event
        # Step 2: 影响分析（融入情绪数据）→ yield step event
        # Step 3: 多头激辩（Bull Agent，引用情绪数据佐证）→ yield step event
        # Step 4: 空头激辩（Bear Agent，引用情绪数据佐证）→ yield step event
        # Step 5: 多空交锋（Debate Agent，轮数由 debate_rounds 控制）→ yield step event
        # Step 6: 争议性结论生成 → yield step event
        # Step 7: 文案生成（Writer Agent）→ yield step event
        # Step 8: 配图生成（Image Generator）→ yield step event
        # 缓存结果 + 持久化到 SQLite 数据库
```

推演流程九步（情绪数据作为第一步获取，贯穿后续所有分析环节）：
0. **情绪数据获取（核心引擎输入）**：调用 SentimentAnalyzer.get_sentiment_context() 获取相关股票或大盘的最新情绪数据（综合指数、各分项得分、趋势方向、样本量、数据源可用性），作为后续所有 Agent 的共享上下文
1. **资讯汇总 Agent**：将输入主题和关联资讯汇总为结构化摘要，提取关键事件和涉及标的
2. **影响分析 Agent**：分析对相关股票/板块的影响，综合引用情绪数据（如"当前综合情绪指数 75，处于贪婪区间，其中散户评论情绪偏贪婪 82、百度投票看涨比例 68%、融资净买入持续增加"），给出初步利好/利空判断
3. **多头激辩 Agent（Bull）**：以坚定看多的立场，用激进、有说服力的语言论证为什么应该买入。要求：引用具体数据、历史类比、情绪数据佐证（如"当前情绪指数仅 25，处于恐慌区间，正是别人恐惧我贪婪的时候"），语气自信甚至略带挑衅
4. **空头激辩 Agent（Bear）**：以坚定看空的立场，用犀利、有冲击力的语言论证为什么应该远离。要求：揭示风险、反驳多头论点、引用情绪数据佐证（如"情绪指数已达 85，散户极度贪婪，历史上每次到这个位置都是见顶信号"）
5. **多空交锋 Agent（Debate）**：模拟多空双方的直接对话交锋，以对话体呈现（多头："..."，空头："..."），轮数由用户设置的 debate_rounds 控制（默认 2 轮），逐步升级争议强度
6. **争议性结论 Agent**：不给出"客观中立"的结论，而是选择一个更有争议性的立场（偏多或偏空），用标题党风格输出一个能引发讨论的核心观点，附带风险提示
7. **文案生成 Agent（Writer）**：根据推演结果和当前选择的平台格式，生成适合社交平台发布的文案（标题 + 正文），融入情绪数据亮点增强内容传播力，输出格式为 `TITLE: ...\nCONTENT: ...`
8. **配图生成 Agent（Image Generator）**：调用火山引擎文生图 API 生成金融/商务风格配图

复用 `app/llm.py` 的 `get_agent_llm()` 获取 LLM 实例。推演结果缓存 60 分钟，以资讯 ID 组合哈希为 key。历史记录持久化到 SQLite 数据库（`stock_analysis_results` 表），历史查询支持分页（limit/offset）。

#### 8. 社交内容生成服务（`app/services/social_content_generator.py`）

将行情推演结果转化为适合社交平台发布的内容：

```python
class SocialContentGenerator:
    def __init__(self):
        self.image_service = image_generator_service  # 复用现有图片生成
        self.xhs_publisher = xiaohongshu_publisher    # 复用现有小红书发布
        self.sentiment_analyzer = None                # 延迟初始化，用于获取情绪数据
    
    async def generate_xhs_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成小红书风格图文：争议性标题 + 多空对决正文 + 情绪数据亮点 + 话题标签 + AI配图
        默认使用中度脱敏（行业描述），可被用户设置覆盖
        融入情绪数据：在正文中插入情绪指数亮点（如"散户恐慌指数已飙到 85"）增强传播力"""
        # 从 controversial_conclusion 提取核心争议点
        # 用 bull_argument 和 bear_argument 构建"你站哪边？"式互动内容
        # 从 sentiment_context 提取情绪数据亮点融入正文
        # 调用 image_generator_service 生成金融风格配图
    
    async def generate_weibo_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成微博短文：一句争议性观点 + 情绪数据点缀 + 反问引导互动
        默认使用轻度脱敏（拼音缩写），可被用户设置覆盖
        融入情绪数据：用情绪指数数据增强观点冲击力（如"恐慌指数跌破 20，散户都在割肉"）"""
        # 从 controversial_conclusion 提取最尖锐的一句话
        # 结合 sentiment_context 中的关键数据点
        # 结尾用反问句引发评论区讨论
    
    async def generate_xueqiu_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成雪球长文：完整多空辩论 + 情绪数据论证 + 争议性标题
        默认使用轻度脱敏（拼音缩写），可被用户设置覆盖
        融入情绪数据：引用各分项得分（评论情绪、百度投票、融资融券等）作为量化论据"""
        # 完整呈现 debate_dialogue 对话交锋
        # 用 bull_argument 和 bear_argument 作为正反论述
        # 引用 sentiment_context 各分项得分数据增强专业性
        # 以 controversial_conclusion 作为文章标题和开头
    
    async def generate_zhihu_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成知乎风格长文：以争议性问题为标题，'回答'体裁呈现多空论证 + 情绪数据引用 + 逻辑推理。
        默认使用轻度脱敏（拼音缩写），可被用户设置覆盖
        融入情绪数据：以情绪指数各分项数据作为量化论据，增强逻辑说服力"""
        # 将 controversial_conclusion 转化为争议性问题标题（如"XX行业真的到了拐点吗？"）
        # 以知乎"回答"体裁展开，先摆数据和事实
        # 引用 sentiment_context 数据（如"从数据看，综合情绪指数 72，其中散户评论贪婪度 82、融资净买入持续增加"）
        # 用 bull_argument 和 bear_argument 呈现多空双方深度论证
        # 用逻辑推理而非情绪渲染
        # 结尾带免责声明和互动引导（"欢迎在评论区讨论你的看法"）
    
    async def generate_daily_report(self, news_items: List[StockNewsItem]) -> Dict[str, SocialContent]:
        """生成每日股市速报：为每个平台生成独立的内容副本
        返回 Dict[platform_id, SocialContent]，包含 xhs/weibo/xueqiu/zhihu 四个平台的内容
        每个平台的内容根据平台特性独立生成（标题风格、正文长度、格式要求各不同）
        情绪概况作为速报首要板块，展示综合恐慌/贪婪指数、各分项得分变化和情绪趋势方向"""
    
    async def publish_to_xhs(self, content: SocialContent) -> Dict:
        """通过 XHS MCP 发布到小红书（初始版本唯一的全自动发布渠道）"""
        return await self.xhs_publisher.publish_content(
            title=content.title,
            content=content.body,
            images=content.image_urls,
            tags=content.tags
        )
    
    async def publish_all_platforms(self, content: SocialContent) -> Dict[str, Dict]:
        """一键发布到全平台（当前全平台 = 小红书）
        依次向所有已启用平台发布内容，返回各平台发布结果。
        当前已启用平台：小红书（全自动，通过 XHS MCP）。
        后续新增平台时，在 ENABLED_PLATFORMS 中添加即可自动纳入发布流程。
        """
        ENABLED_PLATFORMS = {
            "xhs": self.publish_to_xhs,
        }
        results = {}
        for platform_id, publish_fn in ENABLED_PLATFORMS.items():
            try:
                result = await publish_fn(content)
                results[platform_id] = {"status": "published", "result": result}
            except Exception as e:
                results[platform_id] = {"status": "failed", "error": str(e)}
        return results
    
    def copy_to_clipboard(self, content: SocialContent) -> str:
        """将内容格式化为可复制的文本，供用户手动粘贴到微博/雪球/知乎等平台
        初始版本中，非小红书平台采用"一键复制到剪贴板"的半自动方案。
        后续可通过 Playwright 浏览器自动化逐个平台补齐全自动发布能力，
        但全自动发布维护成本较高（平台 UI 改版需跟进适配），不建议初期铺开过多平台。
        """
        # 返回格式化后的纯文本（标题 + 正文 + 标签）
```

**分阶段发布策略说明：**
- **初始版本**：仅小红书支持全自动发布（通过 XHS MCP），其他平台（微博/雪球/知乎）提供"一键复制到剪贴板"的半自动方案
- **后续迭代**：逐个平台通过 Playwright 浏览器自动化补齐发布能力
- **维护成本考量**：全自动发布依赖平台 UI 结构，平台改版时需跟进适配，维护成本不低，不建议初期铺开过多平台

各平台内容生成的 LLM Prompt 策略（以争议性观点为核心驱动，情绪数据为量化支撑）：
- **小红书**：标题用争议性立场句式（如"为什么我敢说XX股票被严重低估了"、"XX板块要崩？3个你不知道的真相"），正文呈现多空双方核心论点并融入情绪数据亮点（如"散户恐慌指数已飙到 85，但聪明钱在悄悄进场"），结尾用"你怎么看？评论区见"引导互动
- **微博**：直接抛出最尖锐的争议性结论，结合情绪指数数据增强冲击力（如"恐慌指数跌破 20，散户都在割肉，但融资净买入创新高——还在追高XX的人，你们想过这个风险吗？#XX股票# #A股#"），控制在 140 字
- **雪球**：以争议性标题开头，完整呈现多空交锋对话，引用具体数据、资讯来源和情绪指数各分项得分（评论情绪、百度投票、融资融券等），结尾带"以上仅为多空双方观点碰撞，不构成投资建议"免责声明
- **知乎**：以争议性问题为标题（如"XX行业真的到了拐点吗？"），以知乎"回答"体裁展开，先摆数据和事实（包括情绪指数各分项数据作为量化论据），再呈现多空双方的深度论证，用逻辑推理而非情绪渲染，结尾带"以上分析仅为个人观点讨论，不构成投资建议"免责声明
- **每日速报**：固定模板（情绪概况→大盘回顾→板块异动→今日最具争议话题→明日看点），"情绪概况"板块展示综合恐慌/贪婪指数、各分项得分变化和趋势方向，"最具争议话题"板块呈现当日最有分歧的资讯和多空观点

#### 9. 合规脱敏服务（`app/services/compliance_service.py`）

社交内容输出前的合规脱敏处理。系统采用四级脱敏策略：轻度（拼音缩写）、中度（行业描述）、重度（纯行业）、不脱敏。内部页面（行情推演）保留完整个股信息，社交内容输出时根据脱敏级别自动处理。每个社交平台有推荐的默认脱敏级别，用户可在设置中覆盖。

```python
class DesensitizationLevel(str, Enum):
    LIGHT = "light"      # 轻度脱敏：拼音缩写（如"贵州茅台"→"GZMT"）
    MEDIUM = "medium"    # 中度脱敏：行业描述（如"贵州茅台"→"某白酒龙头"）
    HEAVY = "heavy"      # 重度脱敏：纯行业（如"贵州茅台"→"白酒板块"）
    NONE = "none"        # 不脱敏：保留原始内容（用户自行承担风险）

# 各平台推荐的默认脱敏级别
PLATFORM_DEFAULT_LEVELS = {
    "xhs": DesensitizationLevel.MEDIUM,     # 小红书审核较严，推荐中度脱敏
    "weibo": DesensitizationLevel.LIGHT,    # 微博财经圈常用缩写，推荐轻度脱敏
    "xueqiu": DesensitizationLevel.LIGHT,   # 雪球用户都是投资者，拼音缩写一看就懂
    "zhihu": DesensitizationLevel.LIGHT,    # 知乎用户偏专业，拼音缩写一看就懂
}


class StockDesensitizer:
    """个股信息脱敏处理器，支持多级脱敏策略"""
    
    def __init__(self, mapping: Dict[str, StockSectorMapping]):
        self.mapping = mapping  # stock_code -> StockSectorMapping
    
    def generate_pinyin_abbreviation(self, stock_name: str) -> str:
        """将股票名称转换为拼音首字母大写缩写（如"贵州茅台"→"GZMT"）
        使用 pypinyin 库提取每个汉字的拼音首字母并大写拼接"""
    
    def replace_stock_names_light(self, text: str) -> str:
        """轻度脱敏：将个股名称替换为拼音缩写（如"贵州茅台"→"GZMT"）"""
    
    def replace_stock_names_medium(self, text: str) -> str:
        """中度脱敏：将个股名称替换为行业描述（如"贵州茅台"→"某白酒龙头"）"""
    
    def replace_stock_names_heavy(self, text: str) -> str:
        """重度脱敏：将个股名称替换为纯行业板块（如"贵州茅台"→"白酒板块"）"""
    
    def replace_stock_codes(self, text: str) -> str:
        """将股票代码（6位数字）替换为行业描述或移除"""
    
    def apply_custom_rules(self, text: str, rules: List[CustomDesensitizeRule]) -> str:
        """应用用户自定义脱敏规则"""


class ComplianceService:
    def __init__(self):
        self.desensitizer = StockDesensitizer(mapping={})
        self.cache_path = "outputs/compliance/stock_sector_mapping.json"
    
    async def build_stock_sector_mapping(self) -> Dict[str, StockSectorMapping]:
        """通过 AKShare 获取板块数据，构建个股到板块/行业的映射表
        
        所有 AKShare 调用使用 asyncio.to_thread() 包装，避免阻塞事件循环。
        冷启动策略详见"个股板块映射表冷启动策略"章节。
        
        详细生成逻辑：
        1. 使用 await asyncio.to_thread(ak.stock_board_industry_name_em) 获取行业板块列表
        2. 通过 await asyncio.to_thread(ak.stock_board_industry_cons_em, symbol=板块名) 获取各板块成分股
        3. 使用 await asyncio.to_thread(ak.stock_zh_a_spot_em) 获取全部 A 股实时行情（含总市值字段），用于行业内排名
        4. 对每个行业板块内的成分股按总市值降序排列，确定行业内排名
        5. 根据排名生成 desensitized_label：
           - 排名第 1 → "某{industry}龙头"（如"某白酒龙头"）
           - 排名第 2 → "某{industry}龙二"（如"某白酒龙二"）
           - 排名第 3-5 → "某{industry}头部企业"（如"某白酒头部企业"）
           - 排名第 6+ → "某{industry}企业"（如"某白酒企业"）
           - 数据不可用时回退 → "某上市公司"
        6. 使用 pypinyin 生成 pinyin_abbr 字段（拼音首字母大写缩写）
        
        构建 stock_code -> (sector_name, industry_name, desensitized_label, pinyin_abbr) 映射。
        结果缓存到本地（JSON 文件或 SQLite），定期更新。
        """
    
    def get_desensitization_level(self, platform: str, user_settings: ComplianceSettings) -> DesensitizationLevel:
        """获取指定平台的脱敏级别：优先使用用户设置的平台级别覆盖，否则使用平台推荐默认值"""
    
    def desensitize_content(self, text: str, mapping: Dict[str, StockSectorMapping],
                            level: DesensitizationLevel = DesensitizationLevel.MEDIUM,
                            custom_rules: List[CustomDesensitizeRule] = None) -> str:
        """对文本执行脱敏处理，根据 level 选择不同策略：
        - LIGHT: 拼音缩写替换 → 替换股票代码 → 应用自定义规则
        - MEDIUM: 行业描述替换 → 替换股票代码 → 应用自定义规则
        - HEAVY: 纯行业板块替换 → 替换股票代码 → 应用自定义规则
        - NONE: 不做任何脱敏处理
        """
    
    def add_disclaimer(self, content: str) -> str:
        """强制附带免责声明：'以上内容仅为市场观点讨论，不构成任何投资建议'"""
    
    def check_compliance(self, content: str) -> ComplianceCheckResult:
        """检查内容是否包含未脱敏的个股信息，返回检查结果。
        注意：合规检查仅生成警告信息供用户参考，不拦截发布操作，用户自行承担风险。"""
    
    def log_publish_audit(self, content: SocialContent, user_acknowledged_risk: bool):
        """记录发布操作审计日志，特别是"不脱敏"模式下的发布行为。
        审计日志记录到应用日志（INFO 级别），包含：
        - content_id: 内容 ID
        - platform: 目标平台
        - desensitization_level: 实际脱敏级别
        - user_acknowledged_risk: 用户是否确认了风险
        - published_at: 发布时间
        - contains_stock_names: 是否包含未脱敏的个股名称（仅 none 级别时检查）
        
        当 desensitization_level 为 "none" 时，日志级别提升为 WARNING。
        """
        level = logging.WARNING if content.desensitization_level == "none" else logging.INFO
        logger.log(level, f"发布审计: content_id={content.id}, platform={content.platform}, "
                   f"level={content.desensitization_level}, risk_ack={user_acknowledged_risk}")
```

SocialContentGenerator 的所有 generate 方法在返回前调用 ComplianceService：
1. 保存原始内容到 `original_content` 字段
2. 通过 `get_desensitization_level(platform, user_settings)` 获取当前平台的脱敏级别
3. 调用 `desensitize_content(text, mapping, level)` 进行脱敏
4. 调用 `add_disclaimer()` 附加免责声明
5. 调用 `check_compliance()` 做最终合规检查
6. 将实际应用的脱敏级别记录到 `SocialContent.desensitization_level` 字段

映射表构建策略：
- 首次启动时通过 AKShare 拉取全量板块数据
- 缓存到 `outputs/compliance/stock_sector_mapping.json`
- 每日自动更新一次（或手动触发）
- AKShare 不可用时回退到本地缓存
