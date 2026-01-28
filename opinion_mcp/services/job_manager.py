"""
Opinion MCP 任务管理器

管理舆论分析任务的生命周期，包括创建、状态更新、结果存储等。
采用内存存储（简化版），生产环境可替换为 Redis。
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
from loguru import logger

from opinion_mcp.schemas import (
    JobInfo,
    JobStatus,
    AnalysisResult,
    AnalysisCards,
    Copywriting,
    CopywritingUpdate,
)


class JobManager:
    """
    任务管理器
    
    负责管理所有分析任务的状态和结果。
    使用内存字典存储任务信息，支持：
    - 创建新任务
    - 更新任务状态和进度
    - 存储分析结果
    - 修改文案内容
    """
    
    def __init__(self):
        """初始化任务管理器"""
        self._jobs: Dict[str, JobInfo] = {}
        self._current_job_id: Optional[str] = None
        logger.info("JobManager 初始化完成")
    
    def create_job(
        self,
        topic: str,
        platforms: List[str],
        debate_rounds: int = 2,
        image_count: int = 2,
    ) -> str:
        """
        创建新的分析任务
        
        Args:
            topic: 分析话题
            platforms: 爬取平台列表
            debate_rounds: 辩论轮数 (1-5)
            image_count: 图片数量 (0-9)
            
        Returns:
            str: 任务 ID
            
        Raises:
            ValueError: 如果已有任务在运行
        """
        # 检查是否有任务在运行
        if self._current_job_id:
            current_job = self._jobs.get(self._current_job_id)
            if current_job and current_job.is_running:
                raise ValueError(
                    f"已有任务在运行中: {self._current_job_id}，请等待完成后再创建新任务"
                )
        
        # 生成唯一任务 ID: job_YYYYMMDD_HHMMSS_xxxxxx
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        
        # 创建任务信息
        job_info = JobInfo(
            job_id=job_id,
            topic=topic,
            platforms=platforms,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            debate_rounds=debate_rounds,
            image_count=image_count,
            progress=0,
        )
        
        # 存储任务
        self._jobs[job_id] = job_info
        self._current_job_id = job_id
        
        logger.info(f"创建任务: {job_id}, 话题: {topic}, 平台: {platforms}")
        return job_id
    
    def update_status(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        current_step: Optional[str] = None,
        current_step_name: Optional[str] = None,
        current_platform: Optional[str] = None,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[JobInfo]:
        """
        更新任务状态
        
        Args:
            job_id: 任务 ID
            status: 新状态
            current_step: 当前步骤代码
            current_step_name: 当前步骤名称（中文）
            current_platform: 当前爬取平台
            progress: 进度百分比 (0-100)
            error_message: 错误信息
            
        Returns:
            Optional[JobInfo]: 更新后的任务信息，如果任务不存在则返回 None
        """
        job = self._jobs.get(job_id)
        if not job:
            logger.warning(f"任务不存在: {job_id}")
            return None
        
        # 更新状态
        if status is not None:
            old_status = job.status
            job.status = status
            logger.info(f"任务 {job_id} 状态更新: {old_status} -> {status}")
            
            # 记录时间戳
            if status == JobStatus.RUNNING and job.started_at is None:
                job.started_at = datetime.now()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.now()
        
        # 更新步骤信息
        if current_step is not None:
            job.current_step = current_step
        if current_step_name is not None:
            job.current_step_name = current_step_name
        if current_platform is not None:
            job.current_platform = current_platform
        
        # 更新进度
        if progress is not None:
            # 确保进度只增不减
            if progress >= job.progress:
                job.progress = min(progress, 100)
        
        # 更新错误信息
        if error_message is not None:
            job.error_message = error_message
        
        return job
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """
        获取任务信息
        
        Args:
            job_id: 任务 ID
            
        Returns:
            Optional[JobInfo]: 任务信息，如果不存在则返回 None
        """
        return self._jobs.get(job_id)
    
    def get_current_job(self) -> Optional[JobInfo]:
        """
        获取当前任务
        
        Returns:
            Optional[JobInfo]: 当前任务信息，如果没有则返回 None
        """
        if self._current_job_id:
            return self._jobs.get(self._current_job_id)
        return None
    
    def store_result(
        self,
        job_id: str,
        summary: Optional[str] = None,
        insight: Optional[str] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        cards: Optional[Dict[str, str]] = None,
        ai_images: Optional[List[str]] = None,
        platforms_analyzed: Optional[List[str]] = None,
        platform_stats: Optional[Dict[str, int]] = None,
        output_file: Optional[str] = None,
    ) -> Optional[JobInfo]:
        """
        存储分析结果
        
        Args:
            job_id: 任务 ID
            summary: 核心观点摘要
            insight: 深度洞察分析
            title: 主标题
            subtitle: 副标题
            content: 正文内容
            tags: 话题标签
            cards: 数据卡片 URL 字典
            ai_images: AI 生成图片 URL 列表
            platforms_analyzed: 已分析平台列表
            platform_stats: 各平台数据量统计
            output_file: 输出文件路径
            
        Returns:
            Optional[JobInfo]: 更新后的任务信息
        """
        job = self._jobs.get(job_id)
        if not job:
            logger.warning(f"任务不存在: {job_id}")
            return None
        
        # 初始化结果对象
        if job.result is None:
            job.result = AnalysisResult()
        
        # 更新摘要和洞察
        if summary is not None:
            job.result.summary = summary
        if insight is not None:
            job.result.insight = insight
        
        # 更新标题
        if title is not None:
            job.result.title = title
        if subtitle is not None:
            job.result.subtitle = subtitle
        
        # 更新文案
        if title is not None or subtitle is not None or content is not None or tags is not None:
            if job.result.copywriting is None:
                job.result.copywriting = Copywriting(
                    title=title or "",
                    subtitle=subtitle or "",
                    content=content or "",
                    tags=tags or [],
                )
            else:
                if title is not None:
                    job.result.copywriting.title = title
                if subtitle is not None:
                    job.result.copywriting.subtitle = subtitle
                if content is not None:
                    job.result.copywriting.content = content
                if tags is not None:
                    job.result.copywriting.tags = tags
        
        # 更新数据卡片
        if cards is not None:
            job.result.cards = AnalysisCards(
                title_card=cards.get("title_card"),
                debate_timeline=cards.get("debate_timeline"),
                trend_analysis=cards.get("trend_analysis"),
                platform_radar=cards.get("platform_radar"),
            )
        
        # 更新 AI 图片
        if ai_images is not None:
            job.result.ai_images = ai_images
        
        # 更新平台信息
        if platforms_analyzed is not None:
            job.result.platforms_analyzed = platforms_analyzed
        if platform_stats is not None:
            job.result.platform_stats = platform_stats
        
        # 更新输出文件
        if output_file is not None:
            job.result.output_file = output_file
        
        logger.info(f"任务 {job_id} 结果已更新")
        return job
    
    def update_copywriting(
        self,
        job_id: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> tuple[Optional[JobInfo], List[str]]:
        """
        修改文案内容
        
        Args:
            job_id: 任务 ID
            title: 新标题（None 表示不修改）
            subtitle: 新副标题（None 表示不修改）
            content: 新正文（None 表示不修改）
            tags: 新标签（None 表示不修改）
            
        Returns:
            tuple: (更新后的任务信息, 已更新的字段列表)
        """
        job = self._jobs.get(job_id)
        if not job:
            logger.warning(f"任务不存在: {job_id}")
            return None, []
        
        # 确保结果和文案对象存在
        if job.result is None:
            job.result = AnalysisResult()
        if job.result.copywriting is None:
            job.result.copywriting = Copywriting(
                title="",
                subtitle="",
                content="",
                tags=[],
            )
        
        # 记录更新的字段
        updated_fields: List[str] = []
        
        # 更新各字段
        if title is not None:
            job.result.copywriting.title = title
            job.result.title = title  # 同步更新 result.title
            updated_fields.append("title")
            logger.info(f"任务 {job_id} 标题已更新: {title}")
        
        if subtitle is not None:
            job.result.copywriting.subtitle = subtitle
            job.result.subtitle = subtitle  # 同步更新 result.subtitle
            updated_fields.append("subtitle")
            logger.info(f"任务 {job_id} 副标题已更新: {subtitle}")
        
        if content is not None:
            job.result.copywriting.content = content
            updated_fields.append("content")
            logger.info(f"任务 {job_id} 正文已更新")
        
        if tags is not None:
            job.result.copywriting.tags = tags
            updated_fields.append("tags")
            logger.info(f"任务 {job_id} 标签已更新: {tags}")
        
        return job, updated_fields
    
    def set_webhook_url(self, job_id: str, webhook_url: str) -> Optional[JobInfo]:
        """
        设置任务的 Webhook URL
        
        Args:
            job_id: 任务 ID
            webhook_url: Webhook 回调 URL
            
        Returns:
            Optional[JobInfo]: 更新后的任务信息
        """
        job = self._jobs.get(job_id)
        if not job:
            logger.warning(f"任务不存在: {job_id}")
            return None
        
        job.webhook_url = webhook_url
        logger.info(f"任务 {job_id} Webhook URL 已设置: {webhook_url}")
        return job
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 10,
    ) -> List[JobInfo]:
        """
        列出任务
        
        Args:
            status: 筛选状态（None 表示全部）
            limit: 返回数量限制
            
        Returns:
            List[JobInfo]: 任务列表（按创建时间倒序）
        """
        jobs = list(self._jobs.values())
        
        # 按状态筛选
        if status is not None:
            jobs = [j for j in jobs if j.status == status]
        
        # 按创建时间倒序排序
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # 限制数量
        return jobs[:limit]
    
    def clear_completed_jobs(self, keep_count: int = 10) -> int:
        """
        清理已完成的任务（保留最近的 N 个）
        
        Args:
            keep_count: 保留的任务数量
            
        Returns:
            int: 清理的任务数量
        """
        # 获取已完成的任务
        completed_jobs = [
            j for j in self._jobs.values()
            if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]
        
        # 按完成时间排序
        completed_jobs.sort(
            key=lambda j: j.completed_at or j.created_at,
            reverse=True,
        )
        
        # 删除超出保留数量的任务
        jobs_to_remove = completed_jobs[keep_count:]
        for job in jobs_to_remove:
            del self._jobs[job.job_id]
        
        removed_count = len(jobs_to_remove)
        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 个已完成的任务")
        
        return removed_count


# 全局单例实例
job_manager = JobManager()
