"""
Opinion MCP Server Pydantic 模型定义

包含所有数据结构的类型定义，用于数据验证和序列化。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================
# 枚举类型
# ============================================================


class JobStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    """Webhook 事件类型枚举"""

    STARTED = "started"
    PROGRESS = "progress"
    PLATFORM_DONE = "platform_done"
    STEP_CHANGE = "step_change"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# 通用响应模型
# ============================================================


class ToolResponse(BaseModel):
    """MCP 工具标准响应格式"""

    success: bool = Field(..., description="操作是否成功")
    data: Optional[Any] = Field(default=None, description="成功时的返回数据")
    error: Optional[str] = Field(default=None, description="失败时的错误信息")

    @classmethod
    def ok(cls, data: Any = None) -> "ToolResponse":
        """创建成功响应"""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ToolResponse":
        """创建失败响应"""
        return cls(success=False, error=error)


# ============================================================
# 文案相关模型
# ============================================================


class Copywriting(BaseModel):
    """小红书文案内容"""

    title: str = Field(..., description="主标题")
    subtitle: str = Field(default="", description="副标题")
    content: str = Field(default="", description="正文内容")
    tags: List[str] = Field(default_factory=list, description="话题标签")


class CopywritingUpdate(BaseModel):
    """文案更新请求"""

    title: Optional[str] = Field(default=None, description="新标题")
    subtitle: Optional[str] = Field(default=None, description="新副标题")
    content: Optional[str] = Field(default=None, description="新正文")
    tags: Optional[List[str]] = Field(default=None, description="新标签")


# ============================================================
# 分析结果模型
# ============================================================


class AnalysisCards(BaseModel):
    """数据卡片 URL"""

    title_card: Optional[str] = Field(
        default=None, description="标题卡片本地路径（内部使用）"
    )
    debate_timeline: Optional[str] = Field(
        default=None, description="辩论时间线本地路径（内部使用）"
    )
    trend_analysis: Optional[str] = Field(
        default=None, description="趋势分析本地路径（内部使用）"
    )
    platform_radar: Optional[str] = Field(
        default=None, description="平台雷达图本地路径（内部使用）"
    )


class CardAssetMeta(BaseModel):
    """面向 OpenClaw 的卡片元数据"""

    type: str = Field(..., description="卡片类型")
    label: str = Field(..., description="卡片显示名称")
    ready: bool = Field(default=False, description="卡片是否已就绪")


class AnalysisCardsMeta(BaseModel):
    """面向 OpenClaw 的卡片元数据集合"""

    total_ready: int = Field(default=0, description="已就绪卡片数量")
    items: List[CardAssetMeta] = Field(
        default_factory=list, description="卡片元数据列表"
    )


class AnalysisResult(BaseModel):
    """舆论分析完整结果"""

    summary: str = Field(default="", description="核心观点摘要")
    insight: str = Field(default="", description="深度洞察分析")
    title: str = Field(default="", description="主标题")
    subtitle: str = Field(default="", description="副标题")
    platforms_analyzed: List[str] = Field(
        default_factory=list, description="已分析平台列表"
    )
    copywriting: Optional[Copywriting] = Field(default=None, description="小红书文案")
    cards: Optional[AnalysisCards] = Field(default=None, description="数据卡片")
    ai_images: List[str] = Field(
        default_factory=list, description="AI 生成图片 URL 列表"
    )
    platform_stats: Dict[str, int] = Field(
        default_factory=dict, description="各平台数据量统计"
    )
    output_file: Optional[str] = Field(default=None, description="输出文件路径")


# ============================================================
# 任务信息模型
# ============================================================


class JobInfo(BaseModel):
    """分析任务信息"""

    job_id: str = Field(..., description="任务唯一标识")
    topic: str = Field(..., description="分析话题")
    platforms: List[str] = Field(default_factory=list, description="爬取平台列表")
    status: JobStatus = Field(default=JobStatus.PENDING, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    current_step_name: Optional[str] = Field(default=None, description="当前步骤名称")
    current_platform: Optional[str] = Field(default=None, description="当前爬取平台")
    progress: int = Field(default=0, description="进度百分比 (0-100)")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    result: Optional[AnalysisResult] = Field(default=None, description="分析结果")
    debate_rounds: int = Field(default=2, description="辩论轮数")
    image_count: int = Field(default=2, description="图片数量")
    webhook_url: Optional[str] = Field(default=None, description="Webhook 回调 URL")
    published: bool = Field(default=False, description="是否已发布")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")

    @property
    def elapsed_minutes(self) -> Optional[float]:
        """计算已用时间（分钟）"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return (end_time - self.started_at).total_seconds() / 60
        return None

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == JobStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == JobStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == JobStatus.FAILED


# ============================================================
# 热榜数据模型
# ============================================================


class HotNewsItem(BaseModel):
    """热榜条目"""

    id: str = Field(..., description="条目唯一标识")
    title: str = Field(..., description="标题")
    hot_score: int = Field(default=0, description="热度分数")
    platforms: List[str] = Field(default_factory=list, description="来源平台")
    growth: Optional[float] = Field(default=None, description="增长率")
    is_new: bool = Field(default=False, description="是否新上榜")
    url: Optional[str] = Field(default=None, description="链接")


class HotNewsResponse(BaseModel):
    """热榜响应"""

    items: List[HotNewsItem] = Field(default_factory=list, description="热榜条目列表")
    total: int = Field(default=0, description="总条数")
    collection_time: Optional[datetime] = Field(default=None, description="采集时间")
    from_cache: bool = Field(default=False, description="是否来自缓存")


# ============================================================
# Webhook 相关模型
# ============================================================


class WebhookData(BaseModel):
    """Webhook 推送数据"""

    step: Optional[str] = Field(default=None, description="当前步骤")
    step_name: Optional[str] = Field(default=None, description="步骤名称")
    progress: Optional[int] = Field(default=None, description="进度百分比")
    message: Optional[str] = Field(default=None, description="消息内容")
    platform: Optional[str] = Field(default=None, description="平台代码")
    platform_name: Optional[str] = Field(default=None, description="平台名称")
    platform_count: Optional[int] = Field(default=None, description="平台数据量")
    error: Optional[str] = Field(default=None, description="错误信息")
    result: Optional[AnalysisResult] = Field(default=None, description="分析结果")


class WebhookPayload(BaseModel):
    """Webhook 推送载荷"""

    job_id: str = Field(..., description="任务 ID")
    event_type: EventType = Field(..., description="事件类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    data: WebhookData = Field(default_factory=WebhookData, description="事件数据")


# ============================================================
# 设置相关模型
# ============================================================


class PlatformInfo(BaseModel):
    """平台信息"""

    code: str = Field(..., description="平台代码")
    name: str = Field(..., description="平台名称")
    emoji: str = Field(default="📌", description="平台 emoji")


class SettingsResponse(BaseModel):
    """设置响应"""

    default_platforms: List[str] = Field(default_factory=list, description="默认平台")
    image_count: int = Field(default=2, description="默认图片数量")
    debate_rounds: int = Field(default=2, description="默认辩论轮数")
    available_platforms: List[PlatformInfo] = Field(
        default_factory=list, description="可用平台列表"
    )


# ============================================================
# 分析任务请求/响应模型
# ============================================================


class AnalyzeTopicRequest(BaseModel):
    """分析话题请求"""

    topic: str = Field(..., description="要分析的话题")
    platforms: Optional[List[str]] = Field(default=None, description="平台列表")
    debate_rounds: int = Field(default=2, ge=1, le=5, description="辩论轮数")
    image_count: int = Field(default=2, ge=0, le=9, description="图片数量")


class AnalyzeTopicResponse(BaseModel):
    """分析话题响应"""

    success: bool = Field(..., description="是否成功")
    job_id: str = Field(..., description="任务 ID")
    message: str = Field(default="分析任务已启动", description="消息")
    estimated_time_minutes: int = Field(default=15, description="预估时间（分钟）")
    platforms: List[str] = Field(default_factory=list, description="爬取平台")
    hint: str = Field(default="请使用 get_analysis_status 查询进度", description="提示")


class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""

    success: bool = Field(default=True, description="是否成功")
    job_id: Optional[str] = Field(default=None, description="任务 ID")
    running: bool = Field(default=False, description="是否运行中")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    current_step_name: Optional[str] = Field(default=None, description="步骤名称")
    progress: int = Field(default=0, description="进度百分比")
    topic: Optional[str] = Field(default=None, description="分析话题")
    current_platform: Optional[str] = Field(default=None, description="当前平台")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    elapsed_minutes: Optional[float] = Field(default=None, description="已用时间")
    estimated_remaining_minutes: Optional[float] = Field(
        default=None, description="预估剩余时间"
    )


class AnalysisResultResponse(BaseModel):
    """分析结果响应"""

    success: bool = Field(default=True, description="是否成功")
    job_id: str = Field(..., description="任务 ID")
    topic: str = Field(..., description="分析话题")
    copywriting: Optional[Copywriting] = Field(default=None, description="文案")
    cards: Optional[AnalysisCardsMeta] = Field(
        default=None, description="数据卡片元数据"
    )
    cards_meta: Optional[AnalysisCardsMeta] = Field(
        default=None, description="数据卡片元数据"
    )
    ai_images: List[str] = Field(default_factory=list, description="AI 图片")
    summary: str = Field(default="", description="核心观点")
    insight: str = Field(default="", description="深度洞察")
    platforms_analyzed: List[str] = Field(
        default_factory=list, description="已分析平台"
    )
    platform_stats: Dict[str, int] = Field(default_factory=dict, description="平台统计")
    output_file: Optional[str] = Field(default=None, description="输出文件")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    duration_minutes: Optional[float] = Field(default=None, description="耗时")


# ============================================================
# 发布相关模型
# ============================================================


class PublishRequest(BaseModel):
    """发布请求"""

    job_id: str = Field(..., description="任务 ID")
    title: Optional[str] = Field(default=None, description="自定义标题")
    tags: Optional[List[str]] = Field(default=None, description="话题标签")


class PublishResponse(BaseModel):
    """发布响应"""

    success: bool = Field(..., description="是否成功")
    job_id: str = Field(..., description="任务 ID")
    note_url: Optional[str] = Field(default=None, description="笔记链接")
    message: str = Field(default="", description="消息")


# ============================================================
# Webhook 注册模型
# ============================================================


class RegisterWebhookRequest(BaseModel):
    """注册 Webhook 请求"""

    callback_url: str = Field(..., description="回调 URL")
    job_id: str = Field(..., description="任务 ID")


class RegisterWebhookResponse(BaseModel):
    """注册 Webhook 响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(default="Webhook 注册成功", description="消息")
