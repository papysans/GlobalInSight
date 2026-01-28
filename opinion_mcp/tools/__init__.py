"""
MCP Tools - 舆论分析工具集

包含以下工具:
- analyze_topic: 启动舆论分析任务
- get_analysis_status: 查询分析进度
- get_analysis_result: 获取分析结果
- update_copywriting: 修改文案
- get_hot_news: 获取热榜数据
- publish_to_xhs: 发布到小红书
- get_settings: 获取配置
- register_webhook: 注册进度推送
"""

# 分析相关工具
from opinion_mcp.tools.analyze import (
    analyze_topic,
    get_analysis_status,
    get_analysis_result,
    update_copywriting,
)

# 热榜工具
from opinion_mcp.tools.hotnews import (
    get_hot_news,
)

# 发布工具
from opinion_mcp.tools.publish import (
    publish_to_xhs,
)

# 设置和 Webhook 工具
from opinion_mcp.tools.settings import (
    get_settings,
    register_webhook,
)

__all__ = [
    # 分析相关
    "analyze_topic",
    "get_analysis_status",
    "get_analysis_result",
    "update_copywriting",
    # 热榜
    "get_hot_news",
    # 发布
    "publish_to_xhs",
    # 设置和 Webhook
    "get_settings",
    "register_webhook",
]
