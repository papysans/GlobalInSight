from pydantic import BaseModel
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

class GenerateSentimentRequest(BaseModel):
    topic: str
    insight: str

class EmotionItem(BaseModel):
    name: str
    value: int

class GenerateSentimentResponse(BaseModel):
    emotions: List[EmotionItem]

class GenerateKeywordsRequest(BaseModel):
    topic: str
    crawler_data: Optional[List[Dict[str, Any]]] = None

class KeywordItem(BaseModel):
    word: str
    frequency: int

class GenerateKeywordsResponse(BaseModel):
    keywords: List[KeywordItem]
