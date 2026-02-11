# 设计文档：数据模型与测试

> 本文件是 design.md 拆分后的子文件。完整设计文档包含：
> - [design-overview.md](design-overview.md)  概述、依赖、策略、架构、数据库
> - [design-frontend.md](design-frontend.md)  前端组件、路由、状态管理
> - [design-backend-services.md](design-backend-services.md)  后端服务（爬虫、推演、内容生成、合规脱敏）
> - [design-sentiment.md](design-sentiment.md) — 散户情绪分析全链路
> - [design-data-models.md](design-data-models.md)  数据模型、正确性属性、错误处理、测试策略

## 数据模型

### 股票资讯条目

```python
class StockNewsItem(BaseModel):
    id: str                    # 唯一标识（source_platform_rank）
    title: str                 # 标题
    summary: str               # 摘要内容
    source_platform: str       # 来源平台标识（akshare / sina / 10jqka / xueqiu / tushare / finnhub / newsapi / alpha_vantage / gdelt / google_rss / marketaux / tipranks / marketbeat / benzinga / seekingalpha / finviz / zacks / yahoo / simplywallst / last10k / wisesheets）
    source_name: str           # 来源平台显示名
    url: str                   # 原文链接
    published_time: str        # 发布时间（ISO 8601）
    hot_value: str             # 热度值
    rank: Optional[int]        # 排名
    category: Optional[str]    # 分类（domestic/international/research_report）
    original_language: Optional[str] = "zh"  # 原始语言（zh/en）
    sentiment: Optional[str] = None          # 情绪标签（bullish/bearish/neutral，来自 Alpha Vantage/Marketaux）
    analyst_rating: Optional[AnalystRating] = None  # 关联的分析师评级（仅 research_report 类别）
    is_ai_translated: bool = False           # 是否为 AI 翻译的摘要（用于前端展示"AI 翻译摘要"标签）
```

### 分析师评级

```python
class AnalystRating(BaseModel):
    analyst_name: str              # 分析师姓名
    firm: str                      # 所属机构（如 "JP Morgan", "Goldman Sachs"）
    rating: str                    # 原始评级（Buy/Hold/Sell/Overweight/Underweight 等）
    rating_normalized: str         # 标准化评级（buy/hold/sell）
    target_price: Optional[float]  # 目标价
    previous_target: Optional[float]  # 前次目标价
    currency: str = "USD"          # 货币
    date: str                      # 评级日期（ISO 8601）
    stock_symbol: str              # 股票代码
    stock_name: str                # 股票名称
    action: Optional[str]          # 动作（upgrade/downgrade/maintain/initiate）
    summary: Optional[str]         # 研报摘要

class ConsensusRating(BaseModel):
    stock_symbol: str              # 股票代码
    stock_name: str                # 股票名称
    buy_count: int                 # 买入评级数量
    hold_count: int                # 持有评级数量
    sell_count: int                # 卖出评级数量
    consensus: str                 # 共识评级（buy/hold/sell）
    avg_target_price: Optional[float]  # 平均目标价
    high_target: Optional[float]   # 最高目标价
    low_target: Optional[float]    # 最低目标价
    total_analysts: int            # 分析师总数
    last_updated: str              # 最后更新时间
```

### 股票资讯采集结果

```python
class StockNewsCollectResponse(BaseModel):
    success: bool
    items: List[StockNewsItem]
    total: int
    source_stats: Dict[str, int]     # 各平台采集数量
    category_stats: Dict[str, int]   # 各类别数量（domestic/international/research_report）
    collection_time: str
    from_cache: bool
```

### 行情推演请求

```python
class StockAnalysisRequest(BaseModel):
    topic: str                       # 推演主题（用户输入的文本，可以是股票名称、事件描述或资讯标题）
    debate_rounds: int = 2           # 辩论轮数（1-5，默认2）
    news_items: Optional[List[StockNewsItem]] = None  # 可选：关联的资讯条目（从热榜带入时使用）
```

### 行情推演步骤输出（SSE 流式）

```python
class StockAnalysisStep(BaseModel):
    agent_name: str       # Agent 名称
    step_content: str     # 步骤输出内容
    status: str           # 'thinking' | 'finished' | 'error'
```

### 行情推演结果

```python
class StockAnalysisResult(BaseModel):
    id: str                          # 推演结果唯一 ID
    news_titles: List[str]           # 输入资讯标题列表
    summary: str                     # 资讯摘要
    impact_analysis: str             # 影响分析
    bull_argument: str               # 多头激辩观点（激进看多论述）
    bear_argument: str               # 空头激辩观点（犀利看空论述）
    debate_dialogue: str             # 多空交锋对话（对话体，轮数由 debate_rounds 控制，默认 2 轮）
    controversial_conclusion: str    # 争议性结论（有立场的标题党观点）
    stance: str                      # 最终立场倾向（"bull" | "bear"）
    risk_warning: str                # 风险提示/免责声明
    sentiment_context: Optional[SentimentContext] = None  # 推演时引用的情绪指数数据
    created_at: str                  # 创建时间
    cache_hit: bool = False
```

### 社交内容生成请求

```python
class SocialContentRequest(BaseModel):
    analysis_id: str                 # 关联的推演结果 ID
    platform: str                    # 目标平台（xhs / weibo / xueqiu / zhihu）
```

### 多平台内容集合（前端状态用）

```python
class PlatformContent(BaseModel):
    """单个平台的内容副本，用于前端多平台预览和独立编辑"""
    title: str = ''                  # 标题
    body: str = ''                   # 正文内容
    images: List[str] = []           # 配图 URL 列表
    tags: List[str] = []             # 话题标签
    titleEmoji: Optional[str] = None # 标题卡 emoji（仅小红书）
    titleTheme: Optional[str] = None # 标题卡主题色（仅小红书）

class PlatformContents(BaseModel):
    """所有平台的内容副本集合"""
    xhs: PlatformContent = PlatformContent()
    weibo: PlatformContent = PlatformContent()
    xueqiu: PlatformContent = PlatformContent()
    zhihu: PlatformContent = PlatformContent()
```

### 每日速报请求

```python
class DailyReportRequest(BaseModel):
    platform: str = "xhs"            # 目标平台格式
    include_analysis: bool = True    # 是否包含 LLM 分析
```

### 社交内容

```python
class SocialContent(BaseModel):
    id: str                          # 内容唯一 ID
    platform: str                    # 目标平台
    title: str                       # 标题（小红书/雪球用）
    body: str                        # 正文内容
    tags: List[str]                  # 话题标签
    image_urls: List[str]            # 配图 URL 列表
    source_analysis_id: Optional[str]  # 关联的推演结果 ID
    content_type: str                # "analysis" | "daily_report"
    status: str                      # "draft" | "published"
    published_at: Optional[str]      # 发布时间
    created_at: str                  # 创建时间
    desensitization_level: str = "medium"  # 实际应用的脱敏级别（light/medium/heavy/none）
    original_content: Optional[str] = None  # 脱敏前的原始内容备份
    user_acknowledged_risk: bool = False    # 用户是否确认了"不脱敏"风险（选择 none 级别时为 True）
```

### 个股板块映射

```python
class StockSectorMapping(BaseModel):
    stock_code: str              # 股票代码（如 "600519"）
    stock_name: str              # 股票名称（如 "贵州茅台"）
    sector_name: str             # 板块名称（如 "白酒"）
    industry_name: str           # 行业名称（如 "食品饮料"）
    desensitized_label: str      # 中度脱敏描述（如 "某白酒龙头"）
    pinyin_abbr: str             # 拼音缩写（如 "GZMT"），用于轻度脱敏
```

### 合规设置

```python
class DesensitizationLevel(str, Enum):
    LIGHT = "light"      # 轻度脱敏：拼音缩写
    MEDIUM = "medium"    # 中度脱敏：行业描述
    HEAVY = "heavy"      # 重度脱敏：纯行业
    NONE = "none"        # 不脱敏

class ComplianceSettings(BaseModel):
    default_level: DesensitizationLevel = DesensitizationLevel.MEDIUM  # 全局默认脱敏级别
    platform_levels: Dict[str, DesensitizationLevel] = {}             # 各平台脱敏级别覆盖
    custom_rules: List[CustomDesensitizeRule] = []                    # 自定义脱敏规则
    show_risk_warning: bool = True                                    # 是否显示风险警告

class CustomDesensitizeRule(BaseModel):
    pattern: str          # 匹配模式（如敏感词）
    replacement: str      # 替换文本

class ComplianceCheckResult(BaseModel):
    is_compliant: bool                    # 是否合规
    violations: List[str] = []            # 违规项列表（如未脱敏的股票名称）
    warnings: List[str] = []             # 警告项列表
```

### 散户评论条目

```python
class SentimentComment(BaseModel):
    id: str                          # 唯一标识
    content: str                     # 评论内容
    source_platform: str             # 来源平台（eastmoney/xueqiu/10jqka）
    stock_code: Optional[str]        # 关联股票代码，None 表示综合讨论
    author_nickname: Optional[str]   # 作者昵称
    published_time: str              # 发布时间（ISO 8601）
    content_hash: str                # 内容 MD5 哈希
    sentiment_label: Optional[str]   # 情绪标签（fear/greed/neutral）
    sentiment_score: Optional[float] # 情绪强度分数（0-100）
```

### 情绪指数快照

```python
class SentimentSnapshot(BaseModel):
    id: str                          # 快照唯一 ID
    stock_code: Optional[str]        # 股票代码，None 表示大盘整体
    index_value: float               # 综合情绪指数值（0-100，加权计算）
    comment_sentiment_score: Optional[float]  # 评论情绪分项得分（0-100）
    baidu_vote_score: Optional[float]         # 百度投票分项得分（0-100）
    akshare_aggregate_score: Optional[float]  # AKShare 聚合分项得分（0-100）
    news_sentiment_score: Optional[float]     # 新闻情绪分项得分（0-100）
    margin_trading_score: Optional[float]     # 融资融券分项得分（0-100）
    fear_ratio: float                # 恐慌评论占比
    greed_ratio: float               # 贪婪评论占比
    neutral_ratio: float             # 中性评论占比
    sample_count: int                # 评论样本数
    data_source_availability: Optional[Dict[str, bool]]  # 各数据源可用性状态
    label: str                       # 情绪标签（extreme_fear/fear/neutral/greed/extreme_greed）
    snapshot_time: str               # 快照时间（ISO 8601）

class SentimentContext(BaseModel):
    """行情推演引用的情绪上下文"""
    index_value: float               # 综合情绪指数
    label: str                       # 情绪标签
    trend_direction: str             # 趋势方向（up/down/stable）
    sample_count: int                # 样本量
    sub_scores: Dict[str, Optional[float]]  # 各分项得分 {comment, baidu_vote, akshare, news, margin}
    source_availability: Dict[str, bool]    # 各数据源可用性
```

### 情绪采集配置

```python
class SentimentCrawlConfig(BaseModel):
    interval_hours: int = 2                    # 采集频率（小时）
    time_window_hours: int = 24                # 增量采集时间窗口
    proxies: List[str] = []                    # 代理池列表
    source_enabled: Dict[str, bool] = {        # 评论采集源启用状态
        "eastmoney": True,
        "xueqiu": True,
        "10jqka": True,
    }
    aggregate_source_enabled: Dict[str, bool] = {  # 聚合指标源启用状态
        "akshare_comment": True,
        "baidu_vote": True,
        "news_sentiment": True,
        "margin_trading": True,
        "xueqiu_heat": True,
    }
    sentiment_weights: Dict[str, float] = {    # 各分项权重配置
        "comment_sentiment": 0.40,
        "baidu_vote": 0.20,
        "akshare_aggregate": 0.15,
        "news_sentiment": 0.15,
        "margin_trading": 0.10,
    }
    spam_keywords: List[str] = []              # 垃圾内容关键词黑名单

class SentimentSourceStatus(BaseModel):
    source_id: str                             # 数据源标识
    source_type: str                           # crawler（评论爬虫）/ aggregate（聚合指标）
    last_collected: Optional[str]              # 最近采集时间
    success_rate: float                        # 成功率（0-1）
    status: str                                # normal/throttled/banned（爬虫）或 normal/failed（聚合）
    comment_count: int = 0                     # 最近一次采集的评论数（仅爬虫源）
    latest_value: Optional[float] = None       # 最近一次采集的指标值（仅聚合源）
```

### 数据源配置

```python
class DataSourceStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"  # API Key 未配置
    CONFIGURED = "configured"          # 已配置但未测试
    CONNECTED = "connected"            # 连通性测试通过
    FAILED = "failed"                  # 连通性测试失败
    FREE = "free"                      # 免费数据源，无需 API Key

class DataSourceConfig(BaseModel):
    source_id: str                     # 数据源标识（如 "finnhub"、"newsapi"）
    display_name: str                  # 显示名称
    category: str                      # 分类（international / research_report / domestic）
    requires_api_key: bool             # 是否需要 API Key
    enabled: bool = True               # 是否启用
    api_key: Optional[str] = None      # API Key（存储在 .env 文件中）
    status: DataSourceStatus = DataSourceStatus.NOT_CONFIGURED
    last_tested: Optional[str] = None  # 最后测试时间

class DataSourceConfigResponse(BaseModel):
    sources: List[DataSourceConfig]    # 所有数据源配置列表
```

## 正确性属性

*正确性属性是指在系统所有有效执行中都应成立的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性是连接人类可读规范与机器可验证正确性保证的桥梁。*


### Property 1: 股票资讯条目数据完整性

*For any* Stock_Crawler 返回的 StockNewsItem，该条目的 title、source_platform、url 和 published_time 字段必须为非空字符串。

**Validates: Requirements 1.2**

### Property 2: 股票资讯缓存往返一致性

*For any* 成功的股票资讯采集结果，保存到缓存后在 30 分钟内读取，返回的条目列表应与原始数据等价。

**Validates: Requirements 1.3**

### Property 3: 数据源失败时回退缓存

*For any* 已缓存的股票资讯数据，当对应的 Stock_Source 请求失败时，Stock_Crawler 应返回非空的缓存数据。

**Validates: Requirements 1.4**

### Property 4: 强制刷新绕过缓存

*For any* 带有 `force_refresh=true` 的采集请求，返回结果中 `from_cache` 应为 `false`。

**Validates: Requirements 1.5**

### Property 5: 股票资讯按排名排序

*For any* 股票热榜返回的资讯列表，列表中每个条目的 rank 值应小于或等于其后续条目的 rank 值。

**Validates: Requirements 2.1**

### Property 6: 平台筛选结果一致性

*For any* 平台筛选参数 P 和股票资讯列表，筛选后返回的每条 StockNewsItem 的 `source_platform` 字段应等于 P。

**Validates: Requirements 2.4**

### Property 7: 行情推演对有效输入产生结果

*For any* 包含至少一条 StockNewsItem 的推演请求，Stock_Analysis_Agent 应返回一个非空的 StockAnalysisResult。

**Validates: Requirements 3.1**

### Property 8: 行情推演结果完整性

*For any* 成功的行情推演结果，其 summary、impact_analysis、bull_argument、bear_argument、debate_dialogue、controversial_conclusion 和 risk_warning 字段必须为非空字符串，且 stance 字段必须为 "bull" 或 "bear"。

**Validates: Requirements 3.2**

### Property 9: 行情推演缓存幂等性

*For any* 相同的资讯组合，在 60 分钟内重复请求行情推演，第二次请求应返回 `cache_hit=true` 且结果内容与首次一致。

**Validates: Requirements 3.8**

### Property 16: 多空交锋对话轮次

*For any* 成功的行情推演结果，其 debate_dialogue 字段应包含至少 debate_rounds 轮多空交锋（即至少 debate_rounds×2 段对话，多头和空头各至少 debate_rounds 段）。当 debate_rounds 使用默认值 2 时，至少包含 4 段对话。

**Validates: Requirements 3.5**

### Property 17: 争议性结论立场一致性

*For any* 成功的行情推演结果，其 stance 字段值（"bull" 或 "bear"）应与 controversial_conclusion 文本中表达的立场方向一致。

**Validates: Requirements 3.6**

### Property 10: 历史推演记录按时间倒序

*For any* 历史推演记录列表，列表中每条记录的 created_at 时间应大于或等于其后续记录的 created_at 时间。

**Validates: Requirements 3.6**

### Property 11: 无效参数返回 400 错误

*For any* 包含无效参数的 API 请求（如负数 limit、不存在的 source、空的 news_items），API 应返回 HTTP 400 状态码和包含错误描述的响应体。

**Validates: Requirements 7.4**

### Property 12: 社交内容平台格式一致性

*For any* 社交内容生成请求，生成的 SocialContent 的 `platform` 字段应与请求中指定的平台一致。

**Validates: Requirements 5.1**

### Property 13: 小红书内容包含必要元素

*For any* 平台为 "xhs" 的 SocialContent，其 title、body 和 tags 字段必须为非空，且 tags 列表长度至少为 1。

**Validates: Requirements 5.2**

### Property 14: 微博内容长度限制

*For any* 平台为 "weibo" 的 SocialContent，其 body 字段长度不超过 140 个字符。

**Validates: Requirements 5.3**

### Property 15: 每日速报内容结构完整性

*For any* content_type 为 "daily_report" 的 SocialContent，其 body 必须包含大盘概况、板块异动和热点事件解读三个部分的内容（非空）。

**Validates: Requirements 5.8, 5.9**

### Property 18: 脱敏内容不含股票代码

*For any* desensitization_level 为 "light"、"medium" 或 "heavy" 的 SocialContent，其 body 和 title 中不应包含任何匹配 `\d{6}` 模式的6位股票代码。

**Validates: Requirements 5A.3**

### Property 19: 脱敏内容不含个股名称

*For any* desensitization_level 为 "medium" 或 "heavy" 的 SocialContent 以及给定的 StockSectorMapping 映射表，其 body 和 title 中不应包含映射表中任何 stock_name。（轻度脱敏使用拼音缩写替换，个股名称同样不会出现。）

**Validates: Requirements 5A.2**

### Property 20: 社交内容包含免责声明

*For any* SocialContent（无论是否脱敏），其 body 必须包含免责声明文本"以上内容仅为市场观点讨论，不构成任何投资建议"。

**Validates: Requirements 5A.5**

### Property 21: 脱敏可逆性

*For any* desensitization_level 不为 "none" 的 SocialContent，其 original_content 字段必须为非空字符串，保留脱敏前的完整内容。

**Validates: Requirements 5A.6**

### Property 22: 拼音缩写格式正确性

*For any* desensitization_level 为 "light" 的 SocialContent，其 body 和 title 中的个股名称应被替换为大写拼音首字母缩写，匹配 `[A-Z]{2,6}` 模式。

**Validates: Requirements 5A.2**

### Property 23: 平台默认脱敏级别一致性

*For any* SocialContent，若用户未设置该平台的脱敏级别覆盖，则实际应用的 desensitization_level 应与该平台的推荐默认值一致（小红书：medium，微博：light，雪球：light，知乎：light）。

**Validates: Requirements 5A.9**

### Property 24: 国际财经新闻中文摘要完整性

*For any* category 为 "international" 且 original_language 为 "en" 的 StockNewsItem，其 summary 字段必须为非空的中文文本（包含至少一个中文字符）。

**Validates: Requirements 1.9**

### Property 25: 投行研报结构化数据完整性

*For any* category 为 "research_report" 的 StockNewsItem，其关联的 AnalystRating 的 firm、rating_normalized、stock_symbol 和 date 字段必须为非空字符串，且 rating_normalized 必须为 "buy"、"hold" 或 "sell" 之一。

**Validates: Requirements 1.10**

### Property 26: 资讯类别筛选一致性

*For any* 类别筛选参数 C（domestic/international/research_report）和股票资讯列表，筛选后返回的每条 StockNewsItem 的 category 字段应等于 C。

**Validates: Requirements 1.11**

### Property 27: 共识评级计算一致性

*For any* ConsensusRating，其 buy_count + hold_count + sell_count 应等于 total_analysts，且 consensus 字段应等于 buy_count/hold_count/sell_count 中最大值对应的评级。

**Validates: Requirements 1.10**

### Property 28: 国际新闻源失败不影响国内数据

*For any* 国际财经数据源全部请求失败的情况，Stock_Crawler 仍应返回非空的国内数据源采集结果（若国内源可用）。

**Validates: Requirements 1.5**

### Property 29: 高风险源指数退避行为

*For any* 标记为高风险的 Stock_Source，连续失败时 RateLimiter 应执行指数退避：第一次失败后等待 5 秒可重试，第二次失败后等待 15 秒可重试，第三次失败后跳过该源。

**Validates: Requirements 1.13**

### Property 30: RateLimiter 每源 cooldown 隔离性

*For any* 两个不同的 Stock_Source，对其中一个源的 cooldown 等待不应影响另一个源的请求时机。

**Validates: Requirements 1.12**

### Property 31: AI 翻译摘要标记一致性

*For any* category 为 "international" 且 original_language 为 "en" 且经过 LLM 翻译的 StockNewsItem，其 is_ai_translated 字段必须为 True。

**Validates: Requirements 1.14**

### Property 32: 散户评论数据完整性与情绪标签有效性

*For any* 经过情绪分析的 SentimentComment，其 content、source_platform、published_time 和 content_hash 字段必须为非空字符串，且 sentiment_label 必须为 "fear"、"greed" 或 "neutral" 之一，sentiment_score 必须在 0-100 范围内。

**Validates: Requirements 9.2, 9.10**

### Property 33: 增量采集时间窗口过滤

*For any* 指定的 time_window_hours 参数和采集结果列表，返回的每条 SentimentComment 的 published_time 必须在当前时间减去 time_window_hours 的范围内。

**Validates: Requirements 9.3**

### Property 34: 个股评论筛选一致性

*For any* 指定的 stock_code 参数和采集结果列表，返回的每条 SentimentComment 的 stock_code 字段必须等于请求中指定的 stock_code。

**Validates: Requirements 9.4**

### Property 35: 代理池轮换与排除

*For any* ProxyPoolManager 实例，当某个代理被标记为失败后，后续调用 get_random_proxy() 不应返回该失败代理；当所有代理均失败时，get_random_proxy() 应返回 None。

**Validates: Requirements 9.5**

### Property 36: 请求频率自适应控制状态机

*For any* AdaptiveRateController 实例和数据源，检测到反爬信号后 cooldown 应翻倍（不超过 60 秒上限）；连续 3 次成功后 cooldown 应恢复为 base_cooldown。

**Validates: Requirements 9.6**

### Property 37: Cookie 池轮换与失效排除

*For any* CookiePoolManager 实例，当某组 Cookie 被标记为失效后，后续调用 get_cookie() 不应返回该失效 Cookie。

**Validates: Requirements 9.7**

### Property 38: 数据源封禁降级

*For any* SentimentCrawler 实例和数据源，连续 3 次请求失败后该数据源应被标记为 banned 状态，is_source_banned() 应返回 True。

**Validates: Requirements 9.8**

### Property 39: 评论清洗去除垃圾和重复

*For any* 包含纯表情评论、垃圾关键词评论和重复评论的输入列表，经过 clean_comments() 处理后，结果列表中不应包含任何纯表情/纯符号评论、不应包含垃圾关键词、不应包含重复的 content_hash。

**Validates: Requirements 9.9**

### Property 40: 情绪指数计算正确性（加权模型）

*For any* 一组已分类的 SentimentComment 和混合数据源指标，calculate_weighted_index() 返回的 index_value 应等于各可用数据源得分的加权求和（权重经重分配后总和为 1.0），且结果在 0-100 范围内。

**Validates: Requirements 9.17**

### Property 45: 混合数据源权重重分配正确性

*For any* 部分数据源不可用的情况，calculate_weighted_index() 中实际使用的 effective_weights 总和应等于 1.0（允许浮点误差 ±0.01），且不可用数据源的权重应为 0。

**Validates: Requirements 9.17**

### Property 46: AKShare 聚合指标归一化范围

*For any* MixedSentimentDataService 返回的各分项得分（baidu_vote_score、akshare_aggregate_score、news_sentiment_score、margin_trading_score），非 None 值必须在 0-100 范围内。

**Validates: Requirements 9.10, 9.11, 9.12, 9.13**

### Property 41: 情绪快照持久化往返一致性

*For any* 成功计算的 SentimentSnapshot，保存到数据库后读取，返回的 index_value、comment_sentiment_score、baidu_vote_score、akshare_aggregate_score、news_sentiment_score、margin_trading_score、fear_ratio、greed_ratio、neutral_ratio 和 sample_count 应与原始数据等价。

**Validates: Requirements 9.19**

### Property 42: 关键事件节点分类

*For any* SentimentSnapshot，当 index_value 大于 80 或小于 20 时，该快照应被标记为关键事件节点。

**Validates: Requirements 9.19**

### Property 43: 推演结果包含情绪上下文

*For any* 成功的行情推演结果，当情绪数据可用时，其 sentiment_context 字段应为非空，且包含有效的 index_value（0-100）、trend_direction（up/down/stable）、sample_count（正整数）和 sub_scores 字典（至少一个分项得分非 None）。

**Validates: Requirements 9.26**

### Property 44: 旧评论清理保留快照

*For any* 执行 cleanup_old_comments(retention_days=90) 后，sentiment_comments 表中不应存在 published_time 早于 90 天前的记录，但 sentiment_snapshots 表中的所有历史快照应保持不变。

**Validates: Requirements 9.26**

## 错误处理

### 前端错误处理

| 场景 | 处理方式 |
|------|----------|
| 股票资讯 API 请求失败 | 显示错误提示，保留上次成功加载的数据 |
| 行情推演 SSE 连接断开 | 显示连接中断提示，允许重试 |
| 行情推演返回 error 事件 | 显示 LLM 调用失败提示，建议稍后重试 |
| 社交内容生成失败 | 显示生成失败提示，允许重试或手动编辑 |
| 小红书发布失败 | 显示具体错误信息（MCP 未启动/未登录/网络错误），引导用户排查 |
| 配图生成失败 | 显示提示，允许跳过配图或手动上传替代 |
| 用户关闭脱敏时 | 显示合规风险警告弹窗，需二次确认 |

### 后端错误处理

| 场景 | 处理方式 |
|------|----------|
| 股票数据源请求超时 | 记录日志，返回缓存数据（若有），标记 `from_cache: true` |
| 股票数据源返回非 200 状态 | 记录日志，跳过该数据源，继续采集其他数据源 |
| HTML 解析失败 | 记录日志，返回空列表，不影响其他数据源 |
| 缓存读写失败 | 记录日志，继续正常流程 |
| 无效请求参数 | 返回 HTTP 400，包含具体的参数错误描述 |
| 行情推演 LLM 调用失败 | 返回 SSE error 事件，提示用户稍后重试 |
| 行情推演输入主题为空 | 返回 HTTP 400，提示需要输入推演主题（topic 不能为空） |
| 社交内容生成 LLM 调用失败 | 返回错误信息，保留推演原始结果供手动编辑 |
| 小红书 MCP 服务不可用 | 返回服务不可用状态，提示用户启动 MCP 服务 |
| 小红书未登录 | 返回未登录状态，引导用户完成登录 |
| 配图生成失败（火山引擎） | 记录日志，返回无配图的内容，提示用户手动上传 |
| 不支持的平台参数 | 返回 HTTP 400，列出支持的平台列表 |
| 映射表缺失条目 | 使用通用描述（如"某上市公司"）替代，记录日志 |
| AKShare 板块数据获取失败 | 使用本地缓存的映射表，若无缓存则使用通用描述 |
| 拼音转换失败 | 回退到中度脱敏（行业描述），记录日志 |
| 国际新闻 API Key 未配置 | 自动跳过该数据源，记录 info 日志，不影响其他源 |
| Finnhub/NewsAPI 请求频率超限 | 记录日志，返回缓存数据（若有），下次采集时自动恢复 |
| 国际新闻英文翻译 LLM 失败 | 保留英文原文作为 summary，标记 original_language="en" |
| 投行研报网站反爬/封禁 | 记录日志，跳过该源，继续采集其他研报源 |
| 分析师评级标准化失败 | 保留原始评级文本，rating_normalized 设为 "unknown" |
| Yahoo Finance yfinance 请求失败 | 记录日志，跳过 Yahoo 源，不影响其他研报源 |
| 所有国际源均失败 | 返回国内数据源结果，在 source_stats 中标记国际源状态 |
| 所有研报源均失败 | 返回国内+国际数据，在 source_stats 中标记研报源状态 |
| 高风险源连续失败三次 | 执行指数退避（5s→15s→跳过），记录日志，不影响其他数据源 |
| RateLimiter 全局并发达到上限 | 请求排队等待，不丢弃请求 |
| 情绪数据源触发反爬封禁 | 暂停该源 30 分钟，使用缓存数据，30 分钟后自动恢复 |
| 情绪评论 LLM 分析失败 | 记录日志，跳过该批次评论，不影响已有快照数据 |
| 代理池所有代理均不可用 | 回退到直连模式，降低采集频率，记录警告日志 |
| Cookie 池所有 Cookie 失效 | 暂停该数据源采集，记录日志，等待手动刷新或自动恢复 |
| 情绪指数计算样本量不足（少于 10 条） | 标记该快照为低置信度，前端展示时附带"样本量不足"提示 |
| 评论清洗后无有效评论 | 跳过本轮分析，保留上一次快照数据 |
| AKShare 聚合指标接口调用失败 | 该分项得分设为 None，权重自动重分配给其他可用源，记录日志 |
| 百度股市通投票数据获取失败 | 该分项得分设为 None，权重自动重分配，记录日志 |
| 数库新闻情绪指数获取失败 | 该分项得分设为 None，权重自动重分配，记录日志 |
| 融资融券数据获取失败 | 该分项得分设为 None，权重自动重分配，记录日志 |
| 所有混合数据源均不可用 | 仅使用评论情绪分（权重 100%）计算指数，标记为低置信度 |
| 用户自定义权重总和不为 1.0 | 自动归一化权重，记录日志 |

## 测试策略

### 单元测试

- StockNewsCollector 的 HTML 解析逻辑（使用固定 HTML 片段）
- StockNewsItem 的数据校验（必填字段验证）
- 缓存服务的读写和过期逻辑
- API 端点的参数校验和错误响应
- StockAnalysisResult 的结构校验
- 行情推演缓存的命中与过期逻辑
- 历史记录的排序逻辑
- InternationalNewsService 各数据源的响应解析（使用固定 JSON/HTML 片段）
- InternationalNewsService 英文翻译中文摘要逻辑
- InternationalNewsService API Key 缺失时的跳过逻辑
- ResearchReportService 各数据源的响应解析（使用固定 JSON/HTML 片段）
- ResearchReportService 评级标准化逻辑（Buy/Overweight→buy, Hold/Neutral→hold, Sell/Underweight→sell）
- ResearchReportService 共识评级计算逻辑
- AnalystRating 到 StockNewsItem 的转换逻辑
- 国际新闻和研报的缓存读写逻辑
- SocialContentGenerator 各平台内容格式校验
- 微博内容长度限制校验
- 小红书内容必要元素校验（标题、正文、标签、配图）
- 知乎内容格式校验（争议性问题标题、"回答"体裁、数据引用、逻辑推理、免责声明）
- 每日速报结构完整性校验
- ComplianceService 脱敏替换逻辑（使用固定的个股名称和代码）
- StockDesensitizer 个股名称替换（已知映射表 + 已知输入文本）
- StockDesensitizer 股票代码替换（6位数字模式匹配）
- StockDesensitizer 拼音缩写生成（已知股票名称 → 预期拼音缩写）
- 各脱敏级别的替换策略正确性（轻度/中度/重度/不脱敏）
- 平台默认脱敏级别配置和用户覆盖逻辑
- 拼音转换失败时回退到中度脱敏
- 免责声明附加逻辑
- 自定义脱敏规则应用
- 映射表缺失条目时的回退逻辑（通用描述替代）
- ComplianceCheckResult 合规检查结果校验
- RateLimiter 全局并发控制（asyncio.Semaphore 行为）
- RateLimiter 每源独立 cooldown 配置
- RateLimiter 高风险源指数退避策略（5s → 15s → 跳过）
- batch_translate_to_chinese 翻译 prompt 严格性（不添加原文没有的信息）
- StockNewsItem.is_ai_translated 标记逻辑
- 非小红书平台的"一键复制到剪贴板"文本格式化
- SentimentCrawler 评论清洗逻辑（纯表情去除、关键词黑名单、内容哈希去重）
- ProxyPoolManager 代理轮换和失败排除逻辑
- CookiePoolManager Cookie 轮换和失效标记逻辑
- AdaptiveRateController 反爬信号检测（403/429/验证码/空响应）
- AdaptiveRateController cooldown 翻倍和恢复逻辑
- SentimentCrawler 数据源封禁和自动恢复逻辑
- SentimentAnalyzer 情绪指数计算（贪婪占比 × 100）
- SentimentAnalyzer 情绪标签分类有效性（fear/greed/neutral）
- SentimentSnapshot 持久化和读取逻辑
- 关键事件节点分类（指数 > 80 或 < 20）
- 旧评论数据清理（90 天）保留快照逻辑
- SentimentContext 趋势方向计算（基于最近 3 个快照）
- MixedSentimentDataService 各 AKShare 接口调用和归一化逻辑
- MixedSentimentDataService 百度投票数据采集和得分计算
- MixedSentimentDataService 新闻情绪指数归一化
- MixedSentimentDataService 融资融券数据归一化
- MixedSentimentDataService 加权指数计算（含权重重分配）
- MixedSentimentDataService 部分数据源不可用时的权重重分配
- MixedSentimentDataService 自定义权重覆盖

### 属性测试

使用 **Hypothesis**（Python 后端）进行属性测试。每个属性测试至少运行 100 次迭代。

标注格式：**Feature: multi-mode-platform, Property {number}: {property_text}**

属性测试重点覆盖：
- 数据完整性校验（Property 1, 8, 13, 15, 24, 25, 32）
- 缓存往返一致性（Property 2, 9, 41）
- 筛选逻辑正确性（Property 6, 26, 33, 34）
- 排序正确性（Property 5, 10）
- 错误参数校验（Property 11）
- 社交内容格式校验（Property 12, 13, 14, 15）
- 多空辩论结构校验（Property 16, 17）
- 合规脱敏校验（Property 18, 19, 20, 21, 22, 23）
- 国际新闻与投行研报校验（Property 24, 25, 26, 27, 28）
- 速率限制与退避策略校验（Property 29, 30）
- AI 翻译标记校验（Property 31）
- 散户情绪采集与反爬校验（Property 32, 33, 34, 35, 36, 37, 38, 39）
- 情绪指数计算与持久化校验（Property 40, 41, 42, 45, 46）
- 情绪与推演集成校验（Property 43）
- 数据生命周期管理校验（Property 44）

### 前端测试策略

使用 Vitest + Vue Test Utils 进行前端单元测试和组件测试：

**Pinia Store 单元测试（优先级高）：**
- `stockNews` store：fetchNews 数据加载、filteredNews 筛选逻辑、selectTopic 状态更新
- `stockAnalysis` store：startAnalysis SSE 流式状态管理、platformContents 多平台内容切换、switchPlatform 逻辑
- `dailyReport` store：generateReport 状态流转、publishAllPlatforms 各平台状态追踪、initPlatformContents 内容初始化
- `sentiment` store：fetchMarketIndex 数据加载、updateWeights 权重更新

**组件测试（优先级中）：**
- PlatformPreview：平台 Tab 切换渲染正确的预览组件、Props 传递正确性
- SentimentGauge：mini/full 模式渲染差异、颜色渐变区间正确性
- XiaohongshuPreview / WeiboCard / XueqiuCard / ZhihuCard：Props 渲染、内容截断/格式化逻辑

**E2E 测试（可选，后续迭代）：**
- 使用 Playwright 覆盖核心用户流程：热榜浏览 → 一键推演 → 内容生成 → 发布
- 初始版本不强制要求 E2E 测试，优先保证 store 和关键组件的单元测试覆盖

### 集成测试

- 股票爬虫端到端：从采集到缓存到 API 返回的完整流程（含国内、国际、研报三类数据）
- 国际财经新闻端到端：从 API 采集到英文翻译到中文摘要生成到缓存
- 投行研报端到端：从多源采集到评级标准化到共识评级计算到热榜展示
- 行情推演端到端：从资讯选择（含国际新闻和研报）到 SSE 流式输出到结果持久化
- 社交内容端到端：从推演结果到内容生成到预览编辑
- 小红书发布端到端：从内容生成到配图到 MCP 发布（需 MCP 服务可用）
- 每日速报端到端：从资讯采集到速报生成到内容输出
- 设置页面回归测试：确保 LLM 配置、API Key 配置等功能正常
- 数据源降级测试：模拟国际源全部失败，验证国内数据正常返回
- 散户情绪采集端到端：从评论采集到清洗到 LLM 情绪分析到混合数据源聚合指标采集到加权指数计算到快照持久化
- 情绪反爬对抗端到端：模拟反爬信号触发自适应降速和数据源封禁降级
- 情绪与推演集成端到端：触发推演时自动获取情绪上下文并注入分析报告
- 情绪数据生命周期：验证 90 天旧评论清理后快照数据保留完整