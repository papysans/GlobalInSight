"""
Webhook 推送服务

负责管理 Webhook 回调 URL 注册和进度推送。
支持重试逻辑（3次，指数退避）。
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
import httpx
from loguru import logger

from opinion_mcp.schemas import (
    EventType,
    WebhookPayload,
    WebhookData,
    AnalysisResult,
)


class WebhookManager:
    """
    Webhook 管理器
    
    负责:
    - 注册 Webhook 回调 URL
    - 推送进度事件到回调 URL
    - 实现重试逻辑（3次，指数退避: 1s, 2s, 4s）
    """
    
    # 重试配置
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # 基础延迟（秒）
    
    def __init__(self):
        """初始化 Webhook 管理器"""
        # job_id -> callback_url 映射
        self._webhooks: Dict[str, str] = {}
        # HTTP 客户端配置
        self._timeout = httpx.Timeout(10.0, connect=5.0)
    
    def register(self, job_id: str, callback_url: str) -> bool:
        """
        注册 Webhook 回调 URL
        
        Args:
            job_id: 任务 ID
            callback_url: 回调 URL
            
        Returns:
            是否注册成功
        """
        if not job_id or not callback_url:
            logger.warning(f"Invalid webhook registration: job_id={job_id}, url={callback_url}")
            return False
        
        self._webhooks[job_id] = callback_url
        logger.info(f"Webhook registered: job_id={job_id}, url={callback_url}")
        return True
    
    def unregister(self, job_id: str) -> bool:
        """
        取消注册 Webhook
        
        Args:
            job_id: 任务 ID
            
        Returns:
            是否取消成功
        """
        if job_id in self._webhooks:
            del self._webhooks[job_id]
            logger.info(f"Webhook unregistered: job_id={job_id}")
            return True
        return False
    
    def get_callback_url(self, job_id: str) -> Optional[str]:
        """
        获取任务的回调 URL
        
        Args:
            job_id: 任务 ID
            
        Returns:
            回调 URL，如果未注册则返回 None
        """
        return self._webhooks.get(job_id)
    
    def has_webhook(self, job_id: str) -> bool:
        """
        检查任务是否注册了 Webhook
        
        Args:
            job_id: 任务 ID
            
        Returns:
            是否已注册
        """
        return job_id in self._webhooks
    
    async def push(
        self,
        job_id: str,
        event_type: EventType,
        data: Optional[WebhookData] = None,
    ) -> bool:
        """
        推送进度事件到 Webhook
        
        Args:
            job_id: 任务 ID
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            是否推送成功
        """
        callback_url = self._webhooks.get(job_id)
        if not callback_url:
            logger.debug(f"No webhook registered for job_id={job_id}, skipping push")
            return False
        
        # 构建 Webhook 载荷
        payload = WebhookPayload(
            job_id=job_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or WebhookData(),
        )
        
        # 执行推送（带重试）
        return await self._push_with_retry(callback_url, payload)
    
    async def _push_with_retry(
        self,
        callback_url: str,
        payload: WebhookPayload,
    ) -> bool:
        """
        带重试逻辑的推送
        
        重试策略: 最多 3 次，指数退避 (1s, 2s, 4s)
        
        Args:
            callback_url: 回调 URL
            payload: Webhook 载荷
            
        Returns:
            是否推送成功
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        callback_url,
                        json=payload.model_dump(mode="json"),
                        headers={"Content-Type": "application/json"},
                    )
                    
                    if response.status_code >= 200 and response.status_code < 300:
                        logger.debug(
                            f"Webhook push success: job_id={payload.job_id}, "
                            f"event={payload.event_type.value}, "
                            f"url={callback_url}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Webhook push failed with status {response.status_code}: "
                            f"job_id={payload.job_id}, attempt={attempt + 1}/{self.MAX_RETRIES}"
                        )
                        last_error = Exception(f"HTTP {response.status_code}: {response.text}")
                        
            except httpx.TimeoutException as e:
                logger.warning(
                    f"Webhook push timeout: job_id={payload.job_id}, "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES}, error={e}"
                )
                last_error = e
                
            except httpx.RequestError as e:
                logger.warning(
                    f"Webhook push request error: job_id={payload.job_id}, "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES}, error={e}"
                )
                last_error = e
                
            except Exception as e:
                logger.error(
                    f"Webhook push unexpected error: job_id={payload.job_id}, "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES}, error={e}"
                )
                last_error = e
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.MAX_RETRIES - 1:
                delay = self.BASE_DELAY * (2 ** attempt)  # 指数退避: 1s, 2s, 4s
                logger.debug(f"Retrying webhook push in {delay}s...")
                await asyncio.sleep(delay)
        
        # 所有重试都失败
        logger.error(
            f"Webhook push failed after {self.MAX_RETRIES} attempts: "
            f"job_id={payload.job_id}, event={payload.event_type.value}, "
            f"url={callback_url}, last_error={last_error}"
        )
        return False
    
    # ============================================================
    # 便捷推送方法
    # ============================================================
    
    async def push_started(
        self,
        job_id: str,
        topic: str,
        platforms: list[str],
    ) -> bool:
        """
        推送任务开始事件
        
        Args:
            job_id: 任务 ID
            topic: 分析话题
            platforms: 平台列表
        """
        data = WebhookData(
            step="started",
            step_name="任务开始",
            progress=0,
            message=f"🚀 开始分析话题: {topic}",
        )
        return await self.push(job_id, EventType.STARTED, data)
    
    async def push_progress(
        self,
        job_id: str,
        step: str,
        step_name: str,
        progress: int,
        message: str,
    ) -> bool:
        """
        推送进度更新事件
        
        Args:
            job_id: 任务 ID
            step: 当前步骤代码
            step_name: 步骤名称
            progress: 进度百分比
            message: 进度消息
        """
        data = WebhookData(
            step=step,
            step_name=step_name,
            progress=progress,
            message=message,
        )
        return await self.push(job_id, EventType.PROGRESS, data)
    
    async def push_platform_done(
        self,
        job_id: str,
        platform: str,
        platform_name: str,
        count: int,
        progress: int,
    ) -> bool:
        """
        推送平台爬取完成事件
        
        Args:
            job_id: 任务 ID
            platform: 平台代码
            platform_name: 平台名称
            count: 爬取数据量
            progress: 当前进度
        """
        data = WebhookData(
            step="crawler_agent",
            step_name="多平台数据爬取",
            progress=progress,
            message=f"✅ {platform_name}爬取完成 ({count}条)",
            platform=platform,
            platform_name=platform_name,
            platform_count=count,
        )
        return await self.push(job_id, EventType.PLATFORM_DONE, data)
    
    async def push_step_change(
        self,
        job_id: str,
        step: str,
        step_name: str,
        progress: int,
        message: Optional[str] = None,
    ) -> bool:
        """
        推送步骤变更事件
        
        Args:
            job_id: 任务 ID
            step: 新步骤代码
            step_name: 步骤名称
            progress: 当前进度
            message: 可选消息
        """
        data = WebhookData(
            step=step,
            step_name=step_name,
            progress=progress,
            message=message or f"🔄 {step_name}...",
        )
        return await self.push(job_id, EventType.STEP_CHANGE, data)
    
    async def push_completed(
        self,
        job_id: str,
        result: Optional[AnalysisResult] = None,
        duration_minutes: Optional[float] = None,
    ) -> bool:
        """
        推送任务完成事件
        
        Args:
            job_id: 任务 ID
            result: 分析结果
            duration_minutes: 耗时（分钟）
        """
        message = "🎉 分析完成！"
        if duration_minutes:
            minutes = int(duration_minutes)
            seconds = int((duration_minutes - minutes) * 60)
            message = f"🎉 分析完成！耗时{minutes}分{seconds}秒"
        
        data = WebhookData(
            step="finished",
            step_name="完成",
            progress=100,
            message=message,
            result=result,
        )
        return await self.push(job_id, EventType.COMPLETED, data)
    
    async def push_failed(
        self,
        job_id: str,
        error: str,
        step: Optional[str] = None,
    ) -> bool:
        """
        推送任务失败事件
        
        Args:
            job_id: 任务 ID
            error: 错误信息
            step: 失败时的步骤
        """
        data = WebhookData(
            step=step or "unknown",
            step_name="失败",
            progress=0,
            message=f"❌ 分析失败: {error}",
            error=error,
        )
        return await self.push(job_id, EventType.FAILED, data)


# 全局单例
webhook_manager = WebhookManager()
