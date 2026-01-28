"""
MCP 发布工具

包含小红书发布相关的 MCP 工具:
- publish_to_xhs: 将分析结果发布到小红书
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from opinion_mcp.services.backend_client import backend_client
from opinion_mcp.services.job_manager import job_manager


# ============================================================
# 6.4 publish_to_xhs 工具 - 发布到小红书
# ============================================================

async def publish_to_xhs(
    job_id: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    将分析结果发布到小红书
    
    Args:
        job_id: 分析任务 ID，将使用该任务的结果发布
        title: 自定义标题，留空则使用分析结果的标题
        tags: 话题标签列表，留空则使用分析结果的标签
        
    Returns:
        Dict 包含:
        - success: bool - 是否成功
        - job_id: str - 任务 ID
        - note_url: str - 笔记链接（成功时）
        - message: str - 消息
    """
    logger.info(f"[publish_to_xhs] 发布到小红书: job_id={job_id}")
    
    # 参数验证
    if not job_id:
        return {
            "success": False,
            "error": "job_id 不能为空",
            "job_id": None,
            "note_url": None,
            "message": "缺少任务 ID",
        }
    
    # 获取任务信息
    job = job_manager.get_job(job_id)
    if not job:
        return {
            "success": False,
            "error": f"任务不存在: {job_id}",
            "job_id": job_id,
            "note_url": None,
            "message": "任务不存在",
        }
    
    # 检查任务状态
    if job.is_running:
        return {
            "success": False,
            "error": "任务仍在运行中，请等待完成后再发布",
            "job_id": job_id,
            "note_url": None,
            "message": "任务未完成",
        }
    
    if job.is_failed:
        return {
            "success": False,
            "error": f"任务失败，无法发布: {job.error_message}",
            "job_id": job_id,
            "note_url": None,
            "message": "任务失败",
        }
    
    # 获取分析结果
    result = job.result
    if not result:
        return {
            "success": False,
            "error": "任务没有结果数据",
            "job_id": job_id,
            "note_url": None,
            "message": "无结果数据",
        }
    
    # 获取文案内容
    copywriting = result.copywriting
    if not copywriting:
        return {
            "success": False,
            "error": "任务没有文案数据",
            "job_id": job_id,
            "note_url": None,
            "message": "无文案数据",
        }
    
    # 使用自定义标题或原标题
    publish_title = title or copywriting.title
    if not publish_title:
        return {
            "success": False,
            "error": "标题不能为空",
            "job_id": job_id,
            "note_url": None,
            "message": "缺少标题",
        }
    
    # 使用自定义标签或原标签
    publish_tags = tags or copywriting.tags or []
    
    # 获取正文内容
    content = copywriting.content
    if not content:
        return {
            "success": False,
            "error": "正文内容不能为空",
            "job_id": job_id,
            "note_url": None,
            "message": "缺少正文",
        }
    
    # 收集所有图片
    images: List[str] = []
    
    # 添加数据卡片
    if result.cards:
        cards = result.cards
        if cards.title_card:
            images.append(cards.title_card)
        if cards.debate_timeline:
            images.append(cards.debate_timeline)
        if cards.trend_analysis:
            images.append(cards.trend_analysis)
        if cards.platform_radar:
            images.append(cards.platform_radar)
    
    # 添加 AI 生成图片
    if result.ai_images:
        images.extend(result.ai_images)
    
    if not images:
        return {
            "success": False,
            "error": "没有可发布的图片",
            "job_id": job_id,
            "note_url": None,
            "message": "缺少图片",
        }
    
    try:
        # 调用后端发布 API
        publish_result = await backend_client.publish_xhs(
            title=publish_title,
            content=content,
            images=images,
            tags=publish_tags,
        )
        
        if not publish_result.get("success"):
            error_msg = publish_result.get("message") or publish_result.get("error") or "发布失败"
            logger.error(f"[publish_to_xhs] 发布失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "job_id": job_id,
                "note_url": None,
                "message": error_msg,
            }
        
        # 获取笔记链接
        note_url = None
        data = publish_result.get("data")
        if isinstance(data, dict):
            note_url = data.get("note_url") or data.get("url")
        
        logger.info(f"[publish_to_xhs] 发布成功: note_url={note_url}")
        
        return {
            "success": True,
            "job_id": job_id,
            "note_url": note_url,
            "message": "发布成功",
        }
        
    except Exception as e:
        logger.exception(f"[publish_to_xhs] 发布异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "job_id": job_id,
            "note_url": None,
            "message": f"发布异常: {str(e)}",
        }


# ============================================================
# 导出工具函数
# ============================================================

__all__ = [
    "publish_to_xhs",
]
