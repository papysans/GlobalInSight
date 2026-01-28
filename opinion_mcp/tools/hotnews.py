"""
MCP 热榜工具

包含热榜数据获取相关的 MCP 工具:
- get_hot_news: 获取多平台热榜数据
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger

from opinion_mcp.config import config
from opinion_mcp.services.backend_client import backend_client


# ============================================================
# 6.2 get_hot_news 工具 - 获取热榜数据
# ============================================================

async def get_hot_news(
    limit: int = 20,
    platforms: Optional[List[str]] = None,
    include_hn: bool = True,
) -> Dict[str, Any]:
    """
    获取多平台热榜数据，可用于发现热门话题
    
    Args:
        limit: 返回条数 (1-100)，默认 20
        platforms: 筛选平台列表，留空返回所有平台
        include_hn: 是否包含 Hacker News，默认 True
        
    Returns:
        Dict 包含:
        - success: bool - 是否成功
        - items: List[Dict] - 热榜条目列表，每个条目包含:
            - id: str - 条目唯一标识
            - title: str - 标题
            - hot_score: int - 热度分数
            - platforms: List[str] - 来源平台
            - growth: float - 增长率
            - is_new: bool - 是否新上榜
        - total: int - 总条数
        - collection_time: str - 采集时间
        - from_cache: bool - 是否来自缓存
    """
    logger.info(f"[get_hot_news] 获取热榜: limit={limit}, platforms={platforms}, include_hn={include_hn}")
    
    # 参数验证
    limit = max(1, min(limit, config.HOTNEWS_MAX_LIMIT))
    
    # 验证平台参数
    if platforms:
        platforms = config.validate_platforms(platforms)
    
    try:
        # 调用后端 API
        result = await backend_client.get_hot_news(
            limit=limit,
            source="hot",
            force_refresh=False,
            include_hn=include_hn,
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "获取热榜失败"),
                "items": [],
                "total": 0,
            }
        
        # 获取原始数据
        items = result.get("items", [])
        
        # 如果指定了平台，进行过滤
        if platforms:
            filtered_items = []
            for item in items:
                item_platforms = item.get("platforms", [])
                item_platform = item.get("platform", "")
                
                # 检查是否匹配指定平台
                if item_platform and item_platform in platforms:
                    filtered_items.append(item)
                elif item_platforms:
                    # 检查 platforms 列表中是否有匹配
                    for p in item_platforms:
                        if p in platforms or _platform_name_to_code(p) in platforms:
                            filtered_items.append(item)
                            break
            items = filtered_items
        
        # 格式化返回数据
        formatted_items = []
        for idx, item in enumerate(items[:limit]):
            formatted_item = {
                "id": item.get("id") or f"item_{idx}",
                "title": item.get("title", ""),
                "hot_score": item.get("hot_score") or item.get("hot_value") or item.get("score") or 0,
                "platforms": _get_item_platforms(item),
                "growth": item.get("growth"),
                "is_new": item.get("is_new", False),
            }
            formatted_items.append(formatted_item)
        
        # 获取采集时间
        collection_time = result.get("collection_time")
        if collection_time and isinstance(collection_time, str):
            pass  # 已经是字符串
        elif collection_time:
            collection_time = collection_time.isoformat() if hasattr(collection_time, 'isoformat') else str(collection_time)
        else:
            collection_time = datetime.now().isoformat()
        
        logger.info(f"[get_hot_news] 获取成功: {len(formatted_items)} 条")
        
        return {
            "success": True,
            "items": formatted_items,
            "total": len(formatted_items),
            "collection_time": collection_time,
            "from_cache": result.get("from_cache", False),
        }
        
    except Exception as e:
        logger.exception(f"[get_hot_news] 获取热榜异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "items": [],
            "total": 0,
        }


def _get_item_platforms(item: Dict[str, Any]) -> List[str]:
    """
    从热榜条目中提取平台列表
    
    Args:
        item: 热榜条目
        
    Returns:
        平台名称列表
    """
    platforms = []
    
    # 尝试从 platforms 字段获取
    if item.get("platforms"):
        platforms = item["platforms"]
    # 尝试从 platform 字段获取
    elif item.get("platform"):
        platform_code = item["platform"]
        platform_name = config.get_platform_name(platform_code)
        platforms = [platform_name]
    # 尝试从 source 字段获取
    elif item.get("source"):
        platforms = [item["source"]]
    
    return platforms


def _platform_name_to_code(name: str) -> str:
    """
    将平台名称转换为代码
    
    Args:
        name: 平台名称
        
    Returns:
        平台代码
    """
    name_to_code = {
        "微博": "wb",
        "抖音": "dy",
        "快手": "ks",
        "B站": "bili",
        "贴吧": "tieba",
        "知乎": "zhihu",
        "小红书": "xhs",
        "Hacker News": "hn",
        "Reddit": "reddit",
    }
    return name_to_code.get(name, name)


# ============================================================
# 导出工具函数
# ============================================================

__all__ = [
    "get_hot_news",
]
