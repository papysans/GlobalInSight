from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing import List, Optional, Dict, Any

class NewsRequest(BaseModel):
    urls: List[str] = []
    topic: str
    platforms: Optional[List[str]] = None  # Optional: specify platforms to crawl
    debate_rounds: Optional[int] = 2  # Optional: debate rounds (1-5), default 2

class AgentState(BaseModel):
    agent_name: str
    step_content: str
    status: str  # 'thinking' | 'finished' | 'error'
    model: Optional[str] = None  # Optional: model name used
    image_urls: Optional[List[str]] = None  # Optional: generated image URLs

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


class UserSettingsResponse(BaseModel):
    llm_apis: List[UserLLMApi] = []
    volcengine: Optional[VolcengineConfig] = None
    agent_llm_overrides: Dict[str, str] = {}


class UserSettingsUpdateRequest(BaseModel):
    llm_apis: Optional[List[UserLLMApi]] = None
    volcengine: Optional[VolcengineConfig] = None
    agent_llm_overrides: Optional[Dict[str, str]] = None

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
