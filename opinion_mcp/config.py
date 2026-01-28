"""
Opinion MCP Server 配置

包含服务器配置、后端连接配置、超时设置等。
"""

import os
from typing import List, Dict


class Config:
    """MCP 服务器配置"""
    
    # 后端服务配置
    BACKEND_URL: str = os.getenv("OPINION_BACKEND_URL", "http://localhost:8000")
    
    # MCP 服务器配置
    MCP_PORT: int = int(os.getenv("OPINION_MCP_PORT", "18061"))
    MCP_HOST: str = os.getenv("OPINION_MCP_HOST", "localhost")
    
    # 请求超时配置 (秒)
    REQUEST_TIMEOUT: int = int(os.getenv("OPINION_REQUEST_TIMEOUT", "300"))
    HOTNEWS_TIMEOUT: int = int(os.getenv("OPINION_HOTNEWS_TIMEOUT", "30"))
    
    # Webhook 配置
    WEBHOOK_RETRY_COUNT: int = int(os.getenv("OPINION_WEBHOOK_RETRY_COUNT", "3"))
    WEBHOOK_RETRY_DELAY: float = float(os.getenv("OPINION_WEBHOOK_RETRY_DELAY", "1.0"))
    
    # 分析默认配置
    DEFAULT_DEBATE_ROUNDS: int = 2
    DEFAULT_IMAGE_COUNT: int = 2
    MAX_IMAGE_COUNT: int = 9
    MAX_DEBATE_ROUNDS: int = 5
    
    # 热榜配置
    HOTNEWS_DEFAULT_LIMIT: int = 20
    HOTNEWS_MAX_LIMIT: int = 100
    
    # 可用平台配置
    AVAILABLE_PLATFORMS: List[Dict[str, str]] = [
        {"code": "wb", "name": "微博", "emoji": "📱"},
        {"code": "dy", "name": "抖音", "emoji": "🎵"},
        {"code": "ks", "name": "快手", "emoji": "🎬"},
        {"code": "bili", "name": "B站", "emoji": "📺"},
        {"code": "tieba", "name": "贴吧", "emoji": "💬"},
        {"code": "zhihu", "name": "知乎", "emoji": "🔍"},
        {"code": "xhs", "name": "小红书", "emoji": "📕"},
        {"code": "hn", "name": "Hacker News", "emoji": "💻"},
        {"code": "reddit", "name": "Reddit", "emoji": "🔴"},
    ]
    
    # 默认爬取平台
    DEFAULT_PLATFORMS: List[str] = ["wb", "dy", "ks", "bili"]
    
    # 进度步骤映射
    STEP_PROGRESS_MAP: Dict[str, Dict] = {
        "crawler_agent": {"name": "多平台数据爬取", "progress": 10},
        "reporter": {"name": "事实提炼汇总", "progress": 25},
        "analyst": {"name": "舆论态势分析", "progress": 40},
        "debater": {"name": "多角度辩论", "progress": 60},
        "writer": {"name": "文案生成", "progress": 80},
        "image_generator": {"name": "图片生成", "progress": 95},
        "finished": {"name": "完成", "progress": 100},
    }
    
    @classmethod
    def get_platform_name(cls, code: str) -> str:
        """根据平台代码获取平台名称"""
        for platform in cls.AVAILABLE_PLATFORMS:
            if platform["code"] == code:
                return platform["name"]
        return code
    
    @classmethod
    def get_platform_emoji(cls, code: str) -> str:
        """根据平台代码获取平台 emoji"""
        for platform in cls.AVAILABLE_PLATFORMS:
            if platform["code"] == code:
                return platform["emoji"]
        return "📌"
    
    @classmethod
    def validate_platforms(cls, platforms: List[str]) -> List[str]:
        """验证平台代码列表，返回有效的平台代码"""
        valid_codes = {p["code"] for p in cls.AVAILABLE_PLATFORMS}
        return [p for p in platforms if p in valid_codes]
    
    @classmethod
    def get_step_info(cls, step: str) -> Dict:
        """获取步骤信息"""
        return cls.STEP_PROGRESS_MAP.get(step, {"name": step, "progress": 0})


# 导出配置实例
config = Config()
