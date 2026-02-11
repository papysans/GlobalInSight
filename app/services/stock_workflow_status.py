"""
股票行情推演工作流状态管理器
复用 WorkflowStatusManager 模式，用于跟踪推演流程的步骤、进度和 SSE 流式状态
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class StockWorkflowStatusManager:
    """管理股票行情推演工作流状态"""

    # 推演九步流程及其对应进度
    STEP_PROGRESS = {
        "sentiment_fetch": 5,
        "news_summary": 15,
        "impact_analysis": 25,
        "bull_argument": 35,
        "bear_argument": 50,
        "debate": 65,
        "conclusion": 75,
        "writer": 85,
        "image_generator": 95,
    }

    def __init__(self):
        self._status: Dict[str, Any] = {
            "running": False,
            "current_step": None,
            "progress": 0,
            "started_at": None,
            "topic": None,
            "current_agent": None,
        }
        self._lock = asyncio.Lock()

    async def start_workflow(self, topic: str):
        """开始推演工作流"""
        async with self._lock:
            self._status = {
                "running": True,
                "current_step": "sentiment_fetch",
                "progress": 0,
                "started_at": datetime.now().isoformat(),
                "topic": topic,
                "current_agent": None,
            }

    async def update_step(
        self,
        step: str,
        progress: Optional[int] = None,
        current_agent: Any = "UNCHANGED",
    ):
        """更新当前步骤"""
        async with self._lock:
            if step != self._status["current_step"] and current_agent == "UNCHANGED":
                self._status["current_agent"] = None

            self._status["current_step"] = step
            if progress is not None:
                self._status["progress"] = progress
            else:
                self._status["progress"] = self.STEP_PROGRESS.get(
                    step, self._status["progress"]
                )

            if current_agent != "UNCHANGED":
                self._status["current_agent"] = current_agent

    async def finish_workflow(self):
        """完成工作流"""
        async with self._lock:
            self._status = {
                "running": False,
                "current_step": None,
                "progress": 100,
                "started_at": self._status.get("started_at"),
                "topic": self._status.get("topic"),
                "current_agent": None,
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
                "current_agent": None,
            }


# 全局实例
stock_workflow_status = StockWorkflowStatusManager()
