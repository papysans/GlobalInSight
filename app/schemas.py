from enum import Enum

from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing import List, Optional, Dict, Any, Union

# ==========================================
# 合规脱敏 - 数据模型
# ==========================================

class DesensitizationLevel(str, Enum):
    """脱敏级别枚举"""
    LIGHT = "light"      # 轻度脱敏：拼音缩写（如"贵州茅台"→"GZMT"）
    MEDIUM = "medium"    # 中度脱敏：行业描述（如"贵州茅台"→"某白酒龙头"）
    HEAVY = "heavy"      # 重度脱敏：纯行业（如"贵州茅台"→"白酒板块"）
    NONE = "none"        # 不脱敏


class StockSectorMapping(BaseModel):
    """个股板块映射"""
    stock_code: str              # 股票代码（如 "600519"）
    stock_name: str              # 股票名称（如 "贵州茅台"）
    sector_name: str             # 板块名称（如 "白酒"）
    industry_name: str           # 行业名称（如 "食品饮料"）
    desensitized_label: str      # 中度脱敏描述（如 "某白酒龙头"）
    pinyin_abbr: str             # 拼音缩写（如 "GZMT"）


class CustomDesensitizeRule(BaseModel):
    """自定义脱敏规则"""
    pattern: str          # 匹配模式（敏感词）
    replacement: str      # 替换文本


class ComplianceSettings(BaseModel):
    """合规设置"""
    default_level: DesensitizationLevel = DesensitizationLevel.MEDIUM
    platform_levels: Dict[str, DesensitizationLevel] = {}
    custom_rules: List[CustomDesensitizeRule] = []
    show_risk_warning: bool = True


class ComplianceCheckResult(BaseModel):
    """合规检查结果"""
    is_compliant: bool                    # 是否合规
    violations: List[str] = []            # 违规项列表
    warnings: List[str] = []             # 警告项列表


class NewsRequest(BaseModel):
    urls: List[str] = []
    topic: str
    platforms: Optional[List[str]] = None  # Optional: specify platforms to crawl
    debate_rounds: Optional[int] = 2  # Optional: debate rounds (1-5), default 2
    image_count: Optional[int] = 2  # Optional: AI image count (0-9), default 2

class AgentState(BaseModel):
    agent_name: str
    step_content: str
    status: str  # 'thinking' | 'finished' | 'error'
    model: Optional[str] = None  # Optional: model name used
    image_urls: Optional[List[str]] = None  # Optional: generated image URLs
    dataview_images: Optional[List[str]] = None  # Optional: DataView card image URLs
    platform_stats: Optional[Dict[str, int]] = None  # Optional: platform data counts {platform_code: count}
    final_copy: Optional[str] = None  # Optional: Writer 完整输出（包含 TITLE/CONTENT/EMOJI/THEME）

class CrawlerDataItem(BaseModel):
    """Standardized crawler data item"""
    platform: str
    content_id: str
    title: str
    content: str
    author: Dict[str, Any]
    interactions: Dict[str, Any]
    timestamp: str
    url: str
    raw_data: Dict[str, Any]

# --- 配置相关 Schema ---
class LLMProviderConfig(BaseModel):
    provider: str
    model: str

class AgentConfig(BaseModel):
    reporter: List[LLMProviderConfig]
    analyst: List[LLMProviderConfig]
    debater: List[LLMProviderConfig]
    writer: List[LLMProviderConfig]

class CrawlerLimit(BaseModel):
    max_items: int
    max_comments: int

class HotNewsConfig(BaseModel):
    """热榜配置"""
    enabled: bool = True
    platform_sources: List[str] = []  # 空数组表示收集所有平台
    fetch_interval_hours: int = 4
    cache_ttl_minutes: int = 30
    max_items_per_platform: int = 100

class HotNewsCollectRequest(BaseModel):
    """热榜收集请求"""
    platforms: Optional[List[str]] = None  # 指定平台列表，None表示所有平台
    force_refresh: bool = False  # 是否强制刷新


class HotNewsInterpretRequest(BaseModel):
    """单条热点的“演化解读”请求（只在用户点开时调用）"""
    id: str
    title: str
    collection_time: Optional[str] = None
    hot_value: Optional[str] = None
    hot_score: Optional[float] = None
    growth: Optional[int] = None
    hot_score_delta: Optional[float] = None
    is_new: Optional[bool] = None
    platforms_data: Optional[List[Dict[str, Any]]] = None
    evidence: Optional[List[Dict[str, Any]]] = None


class HotNewsInterpretResponse(BaseModel):
    """演化解读结果"""
    success: bool = True
    id: str
    title: str
    agent_name: str = "hotnews_interpretation_agent"
    cache_hit: bool = False
    trace_steps: List[str] = []
    lifecycle_stage: str
    diffusion_summary: str
    divergence_points: List[str] = []
    watch_points: List[str] = []
    confidence: float = 0.6
    used_llm: bool = False

class ConfigResponse(BaseModel):
    llm_providers: Dict[str, List[LLMProviderConfig]]
    crawler_limits: Dict[str, CrawlerLimit]
    debate_max_rounds: int
    default_platforms: List[str]
    hot_news_config: Optional[HotNewsConfig] = None

class ConfigUpdateRequest(BaseModel):
    debate_max_rounds: Optional[int] = None
    crawler_limits: Optional[Dict[str, CrawlerLimit]] = None
    default_platforms: Optional[List[str]] = None
    hot_news_config: Optional[HotNewsConfig] = None


# --- 前端可写入的用户设置（落盘到 cache/，不影响 .env） ---
class UserLLMApi(BaseModel):
    """
    Frontend-provided LLM API config.
    Note: backend currently uses it mainly to merge/override provider keys.
    """
    id: Optional[int] = None
    provider: str
    providerKey: str
    url: Optional[str] = None
    key: str
    model: Optional[str] = None
    active: Optional[bool] = True


class VolcengineConfig(BaseModel):
    """Volcengine Visual / 即梦（文生图）配置"""
    model_config = ConfigDict(extra="ignore")
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    image_count: Optional[int] = 2  # AI生图张数，默认2张


class UserSettingsResponse(BaseModel):
    llm_apis: List[UserLLMApi] = []
    volcengine: Optional[VolcengineConfig] = None
    agent_llm_overrides: Dict[str, Union[str, Dict[str, Any]]] = {}


class UserSettingsUpdateRequest(BaseModel):
    llm_apis: Optional[List[UserLLMApi]] = None
    volcengine: Optional[VolcengineConfig] = None
    agent_llm_overrides: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None

# --- 输出文件相关 Schema ---
class OutputFileInfo(BaseModel):
    filename: str
    topic: str
    created_at: str
    size: int

class OutputFileListResponse(BaseModel):
    files: List[OutputFileInfo]
    total: int

class OutputFileContentResponse(BaseModel):
    filename: str
    content: str
    created_at: str

# --- 工作流状态相关 Schema ---
class WorkflowStatusResponse(BaseModel):
    running: bool
    current_step: Optional[str] = None
    progress: int = 0
    started_at: Optional[str] = None
    topic: Optional[str] = None
    current_platform: Optional[str] = None  # 当前正在爬取的平台

# --- 数据生成相关 Schema ---
class GenerateContrastRequest(BaseModel):
    topic: str
    insight: str

class GenerateContrastResponse(BaseModel):
    domestic: List[int]  # [支持%, 中立%, 反对%]
    intl: List[int]  # [支持%, 中立%, 反对%]
    agent_name: str = "analyst"  # 生成数据的Agent名称
    used_llm: bool = True  # 是否使用了LLM
    cache_hit: bool = False  # 是否命中缓存
    llm_reasoning: Optional[str] = None  # LLM生成时的推理过程/说明（前300字符）

class GenerateSentimentRequest(BaseModel):
    topic: str
    insight: str

class EmotionItem(BaseModel):
    name: str
    value: int

class GenerateSentimentResponse(BaseModel):
    emotions: List[EmotionItem]
    agent_name: str = "analyst"  # 生成数据的Agent名称
    used_llm: bool = True  # 是否使用了LLM
    cache_hit: bool = False  # 是否命中缓存
    llm_reasoning: Optional[str] = None  # LLM生成时的推理过程/说明（前300字符）

class GenerateKeywordsRequest(BaseModel):
    topic: str
    crawler_data: Optional[List[Dict[str, Any]]] = None

class KeywordItem(BaseModel):
    word: str
    frequency: int

class GenerateKeywordsResponse(BaseModel):
    keywords: List[KeywordItem]
    agent_name: str = "analyst"  # 生成数据的Agent名称
    used_llm: bool = True  # 是否使用了LLM
    cache_hit: bool = False  # 是否命中缓存
    llm_reasoning: Optional[str] = None  # LLM生成时的推理过程/说明（前300字符）


# --- 小红书发布相关 Schema ---
class XhsPublishRequest(BaseModel):
    """小红书发布请求"""
    title: str
    content: str
    images: List[str] = []  # 图片列表（本地路径或 HTTP URL）
    tags: Optional[List[str]] = None  # 话题标签（不含#前缀）


class XhsPublishResponse(BaseModel):
    """小红书发布响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class XhsStatusResponse(BaseModel):
    """小红书 MCP 状态响应"""
    mcp_available: bool
    login_status: bool
    message: str


# ==========================================
# 股票资讯与行情推演平台 - 数据模型
# ==========================================

class AnalystRating(BaseModel):
    """分析师评级数据模型"""
    analyst_name: str = ""
    firm: str = ""
    rating: str = ""                           # 原始评级（Buy/Hold/Sell/Overweight/Underweight 等）
    rating_normalized: str = ""                # 标准化评级（buy/hold/sell）
    target_price: Optional[float] = None       # 目标价
    previous_target: Optional[float] = None    # 前次目标价
    currency: str = "USD"                      # 货币
    date: str = ""                             # 评级日期（ISO 8601）
    stock_symbol: str = ""                     # 股票代码
    stock_name: str = ""                       # 股票名称
    action: Optional[str] = None               # 动作（upgrade/downgrade/maintain/initiate）
    summary: Optional[str] = None              # 研报摘要


class ConsensusRating(BaseModel):
    """共识评级数据模型"""
    stock_symbol: str                          # 股票代码
    stock_name: str                            # 股票名称
    buy_count: int                             # 买入评级数量
    hold_count: int                            # 持有评级数量
    sell_count: int                            # 卖出评级数量
    consensus: str                             # 共识评级（buy/hold/sell）
    avg_target_price: Optional[float] = None   # 平均目标价
    high_target: Optional[float] = None        # 最高目标价
    low_target: Optional[float] = None         # 最低目标价
    total_analysts: int                        # 分析师总数
    last_updated: str                          # 最后更新时间（ISO 8601）


class StockNewsItem(BaseModel):
    """股票资讯条目"""
    id: str                                    # 唯一标识（source_platform_rank）
    title: str                                 # 标题
    summary: str                               # 摘要内容
    source_platform: str                       # 来源平台标识
    source_name: str                           # 来源平台显示名
    url: str                                   # 原文链接
    published_time: str                        # 发布时间（ISO 8601）
    hot_value: str                             # 热度值（原始字符串）
    heat_score: Optional[float] = None         # 统一热度评分（0-100，跨源归一化）
    rank: Optional[int] = None                 # 排名
    category: Optional[str] = None             # 分类（domestic/international/research_report）
    original_language: Optional[str] = "zh"    # 原始语言（zh/en）
    sentiment: Optional[str] = None            # 情绪标签（bullish/bearish/neutral）
    analyst_rating: Optional[AnalystRating] = None  # 关联的分析师评级
    is_ai_translated: bool = False             # 是否为 AI 翻译的摘要


class StockNewsCollectResponse(BaseModel):
    """股票资讯采集结果"""
    success: bool
    items: List[StockNewsItem] = []
    total: int = 0
    source_stats: Dict[str, int] = {}         # 各平台采集数量
    category_stats: Dict[str, int] = {}       # 各类别数量
    collection_time: str = ""
    from_cache: bool = False


class StockAnalysisRequest(BaseModel):
    """行情推演请求"""
    topic: str                                 # 推演主题
    debate_rounds: int = 2                     # 辩论轮数（1-5，默认2）
    news_items: Optional[List[StockNewsItem]] = None  # 可选关联资讯


class StockAnalysisStep(BaseModel):
    """行情推演步骤输出（SSE 流式）"""
    agent_name: str                            # Agent 名称
    step_content: str                          # 步骤输出内容
    status: str                                # 'thinking' | 'finished' | 'error'


class StockAnalysisResult(BaseModel):
    """行情推演结果"""
    id: str                                    # 推演结果唯一 ID
    news_titles: List[str] = []                # 输入资讯标题列表
    summary: str = ""                          # 资讯摘要
    impact_analysis: str = ""                  # 影响分析
    bull_argument: str = ""                    # 多头激辩观点
    bear_argument: str = ""                    # 空头激辩观点
    debate_dialogue: str = ""                  # 多空交锋对话
    controversial_conclusion: str = ""         # 争议性结论
    stance: str = ""                           # 最终立场（"bull" | "bear"）
    risk_warning: str = ""                     # 风险提示
    sentiment_context: Optional[Dict[str, Any]] = None  # 推演时引用的情绪数据快照
    created_at: str = ""                       # 创建时间
    cache_hit: bool = False


# ==========================================
# 数据源配置管理
# ==========================================

class DataSourceStatus(str, Enum):
    """数据源状态枚举"""
    NOT_CONFIGURED = "not_configured"  # API Key 未配置
    CONFIGURED = "configured"          # 已配置但未测试
    CONNECTED = "connected"            # 连通性测试通过
    FAILED = "failed"                  # 连通性测试失败
    FREE = "free"                      # 免费数据源，无需 API Key


class DataSourceConfig(BaseModel):
    """单个数据源的配置信息"""
    source_id: str                     # 数据源标识（如 "finnhub"、"newsapi"）
    display_name: str                  # 显示名称
    category: str                      # 分类（international / research_report / domestic）
    requires_api_key: bool             # 是否需要 API Key
    enabled: bool = True               # 是否启用
    api_key: Optional[str] = None      # API Key
    status: DataSourceStatus = DataSourceStatus.NOT_CONFIGURED
    last_tested: Optional[str] = None  # 最后测试时间（ISO 8601）


class DataSourceConfigResponse(BaseModel):
    """数据源配置列表响应"""
    sources: List[DataSourceConfig]    # 所有数据源配置列表


# ==========================================
# 社交内容生成与发布 - 数据模型
# ==========================================

class SocialContentRequest(BaseModel):
    """社交内容生成请求"""
    analysis_id: str                             # 关联的推演结果 ID
    platform: str                                # 目标平台（xhs / weibo / xueqiu / zhihu）


class DailyReportRequest(BaseModel):
    """每日速报请求"""
    platform: str = "xhs"                        # 目标平台格式
    include_analysis: bool = True                # 是否包含 LLM 分析


class PlatformContent(BaseModel):
    """单个平台的内容副本，用于前端多平台预览和独立编辑"""
    title: str = ""                              # 标题
    body: str = ""                               # 正文内容
    images: List[str] = []                       # 配图 URL 列表
    tags: List[str] = []                         # 话题标签
    titleEmoji: Optional[str] = None             # 标题卡 emoji（仅小红书）
    titleTheme: Optional[str] = None             # 标题卡主题色（仅小红书）


class PlatformContents(BaseModel):
    """所有平台的内容副本集合"""
    xhs: PlatformContent = PlatformContent()
    weibo: PlatformContent = PlatformContent()
    xueqiu: PlatformContent = PlatformContent()
    zhihu: PlatformContent = PlatformContent()


class SocialContent(BaseModel):
    """社交内容"""
    id: str                                      # 内容唯一 ID
    platform: str                                # 目标平台（xhs / weibo / xueqiu / zhihu）
    title: str                                   # 标题
    body: str                                    # 正文内容
    tags: List[str]                              # 话题标签
    image_urls: List[str]                        # 配图 URL 列表
    source_analysis_id: Optional[str] = None     # 关联的推演结果 ID
    content_type: str                            # "analysis" | "daily_report"
    status: str = "draft"                        # "draft" | "published"
    published_at: Optional[str] = None           # 发布时间（ISO 8601）
    created_at: str = ""                         # 创建时间（ISO 8601）
    desensitization_level: str = "medium"        # 实际应用的脱敏级别（light/medium/heavy/none）
    original_content: Optional[str] = None       # 脱敏前的原始内容备份
    user_acknowledged_risk: bool = False          # 用户是否确认了"不脱敏"风险


# ==========================================
# 散户情绪分析 - 数据模型
# ==========================================

class SentimentComment(BaseModel):
    """散户评论条目"""
    id: str                                    # 唯一标识
    content: str                               # 评论内容
    source_platform: str                       # 来源平台（eastmoney/xueqiu/10jqka）
    stock_code: Optional[str] = None           # 关联股票代码，None 表示综合讨论
    author_nickname: Optional[str] = None      # 作者昵称
    published_time: str                        # 发布时间（ISO 8601）
    content_hash: str                          # 内容 MD5 哈希
    sentiment_label: Optional[str] = None      # 情绪标签（fear/greed/neutral）
    sentiment_score: Optional[float] = None    # 情绪强度分数（0-100）


class SentimentSnapshot(BaseModel):
    """情绪指数快照"""
    id: str                                    # 快照唯一 ID
    stock_code: Optional[str] = None           # 股票代码，None 表示大盘整体
    index_value: float                         # 综合情绪指数值（0-100，加权计算）
    comment_sentiment_score: Optional[float] = None   # 评论情绪分项得分（0-100）
    baidu_vote_score: Optional[float] = None          # 百度投票分项得分（0-100）
    akshare_aggregate_score: Optional[float] = None   # AKShare 聚合分项得分（0-100）
    news_sentiment_score: Optional[float] = None      # 新闻情绪分项得分（0-100）
    margin_trading_score: Optional[float] = None      # 融资融券分项得分（0-100）
    fear_ratio: float = 0.0                    # 恐慌评论占比
    greed_ratio: float = 0.0                   # 贪婪评论占比
    neutral_ratio: float = 0.0                 # 中性评论占比
    sample_count: int = 0                      # 评论样本数
    data_source_availability: Optional[Dict[str, bool]] = None  # 各数据源可用性状态
    label: str = "neutral"                     # 情绪标签（extreme_fear/fear/neutral/greed/extreme_greed）
    snapshot_time: str = ""                    # 快照时间（ISO 8601）


class SentimentContext(BaseModel):
    """行情推演引用的情绪上下文"""
    index_value: float                         # 综合情绪指数
    label: str                                 # 情绪标签
    trend_direction: str                       # 趋势方向（up/down/stable）
    sample_count: int                          # 样本量
    sub_scores: Dict[str, Optional[float]]     # 各分项得分 {comment, baidu_vote, akshare, news, margin}
    source_availability: Dict[str, bool]       # 各数据源可用性


class MixedSentimentMetrics(BaseModel):
    """混合数据源聚合指标"""
    baidu_vote_score: Optional[float] = None           # 百度投票得分（0-100）
    akshare_aggregate_score: Optional[float] = None    # AKShare 聚合得分（0-100）
    news_sentiment_score: Optional[float] = None       # 新闻情绪得分（0-100）
    margin_trading_score: Optional[float] = None       # 融资融券得分（0-100）
    xueqiu_heat: Optional[float] = None                # 雪球热度数据
    source_availability: Dict[str, bool] = {}          # 各数据源可用性


class SentimentCrawlConfig(BaseModel):
    """情绪采集配置"""
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
    """情绪数据源采集状态"""
    source_id: str                             # 数据源标识
    source_type: str                           # crawler（评论爬虫）/ aggregate（聚合指标）
    last_collected: Optional[str] = None       # 最近采集时间
    success_rate: float = 0.0                  # 成功率（0-1）
    status: str = "normal"                     # normal/throttled/banned（爬虫）或 normal/failed（聚合）
    comment_count: int = 0                     # 最近一次采集的评论数（仅爬虫源）
    latest_value: Optional[float] = None       # 最近一次采集的指标值（仅聚合源）
