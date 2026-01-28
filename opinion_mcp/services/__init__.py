"""
Opinion MCP Services

包含后端客户端、任务管理器、Webhook 管理器等服务。
"""

from opinion_mcp.services.backend_client import BackendClient, backend_client
from opinion_mcp.services.job_manager import JobManager, job_manager
from opinion_mcp.services.webhook_manager import WebhookManager, webhook_manager

__all__ = [
    "BackendClient",
    "backend_client",
    "JobManager",
    "job_manager",
    "WebhookManager",
    "webhook_manager",
]
