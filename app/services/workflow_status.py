"""
工作流状态管理器
用于跟踪当前运行的工作流状态
"""
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

class WorkflowStatusManager:
    """管理工作流状态"""
    
    def __init__(self):
        self._status: Dict[str, Any] = {
            "running": False,
            "current_step": None,
            "progress": 0,
            "started_at": None,
            "topic": None,
            "current_platform": None,  # 当前正在爬取的平台
        }
        self._lock = asyncio.Lock()
    
    async def start_workflow(self, topic: str):
        """开始工作流"""
        async with self._lock:
            self._status = {
                "running": True,
                "current_step": "crawler_agent",
                "progress": 0,
                "started_at": datetime.now().isoformat(),
                "topic": topic,
                "current_platform": None,
            }
    
    async def update_step(self, step: str, progress: int = None, current_platform: Any = "UNCHANGED"):
        """更新当前步骤"""
        async with self._lock:
            # 如果步骤切换了，且没有明确指定平台，则自动清空平台信息
            if step != self._status["current_step"] and current_platform == "UNCHANGED":
                self._status["current_platform"] = None

            self._status["current_step"] = step
            if progress is not None:
                self._status["progress"] = progress
            else:
                # 根据步骤自动计算进度
                step_progress = {
                    "crawler_agent": 10,
                    "reporter": 30,
                    "analyst": 50,
                    "debater": 70,
                    "writer": 90,
                }
                self._status["progress"] = step_progress.get(step, self._status["progress"])
            
            # 更新当前平台（如果明确提供，包括 None）
            if current_platform != "UNCHANGED":
                self._status["current_platform"] = current_platform
    
    async def finish_workflow(self):
        """完成工作流"""
        async with self._lock:
            self._status = {
                "running": False,
                "current_step": None,
                "progress": 100,
                "started_at": self._status.get("started_at"),
                "topic": self._status.get("topic"),
                "current_platform": None,
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        async with self._lock:
            return self._status.copy()
    
    async def reset(self):
        """重置状态"""
        async with self._lock:
            self._status = {
                "running": False,
                "current_step": None,
                "progress": 0,
                "started_at": None,
                "topic": None,
                "current_platform": None,
            }


# 全局实例
workflow_status = WorkflowStatusManager()
