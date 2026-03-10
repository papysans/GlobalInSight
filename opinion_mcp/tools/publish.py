"""
MCP 发布工具

包含小红书发布相关的 MCP 工具:
- publish_to_xhs: 将分析结果发布到小红书

支持两种发布模式:
- ai_only: 阶段 F，仅使用 AI 生成的配图
- ai_and_cards: 阶段 B，同时使用数据卡片和 AI 配图

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
"""

import os
import sys
from typing import Any, Dict, List, Optional
from loguru import logger

from opinion_mcp.services.backend_client import backend_client
from opinion_mcp.services.job_manager import job_manager
from opinion_mcp.utils.url_validator import download_images


# ============================================================
# 辅助函数
# ============================================================

def get_image_publish_mode() -> str:
    """
    获取当前图片发布模式
    
    Property 6: Configuration Mode Behavior
    For any configuration where `image_publish_mode` is "ai_only", 
    the publish tool SHALL use only AI images.
    """
    try:
        # 动态导入以支持热加载
        sys.path.insert(0, ".")
        from app.config import Config
        return Config.get_image_publish_mode()
    except ImportError:
        logger.warning("[publish] 无法导入 app.config，使用默认模式 ai_only")
        return "ai_only"


async def collect_images_for_publish(
    result: Any,
    mode: str,
) -> tuple[List[str], List[str]]:
    """
    根据发布模式收集图片并下载到本地
    
    火山引擎生成的图片 URL 有时效性，需要先下载到本地再上传到小红书。
    
    Property 4: Publish Image Ordering
    For any publish request in "ai_and_cards" mode, the images SHALL be ordered as:
    InsightCanvas → KeyFindingsCanvas → DebateTimelineCanvas → AI images.
    In "ai_only" mode, only AI images SHALL be included in their original order.
    
    Args:
        result: 分析结果对象
        mode: 发布模式 ("ai_only" 或 "ai_and_cards")
        
    Returns:
        Tuple[List[str], List[str]]: (本地图片路径列表, 下载失败的URL列表)
    """
    # 收集图片 URL
    all_images: List[str] = []
    # 已经是本地文件的路径（由 generate_topic_cards 写入），无需下载
    local_card_paths: List[str] = []
    
    if mode == "ai_and_cards":
        # 阶段 B: 先添加数据卡片，再添加 AI 配图
        if result.cards:
            cards = result.cards
            for card_path in [cards.title_card, cards.debate_timeline, cards.trend_analysis, cards.platform_radar]:
                if card_path:
                    if os.path.isfile(card_path):
                        local_card_paths.append(card_path)
                    else:
                        all_images.append(card_path)
    
    # 添加 AI 生成图片
    if result.ai_images:
        all_images.extend(result.ai_images)
    
    if not all_images and not local_card_paths:
        return [], []
    
    # 下载远程图片到本地（火山引擎 URL 有时效性）
    local_paths: List[str] = []
    failed_images: List[str] = []
    
    if all_images:
        logger.info(f"[collect_images] 开始下载 {len(all_images)} 张远程图片到本地...")
        downloaded_paths, download_results = await download_images(
            all_images,
            timeout=30.0,
            concurrency=3,
        )
        local_paths.extend(downloaded_paths)
        failed_images = [r.original_url for r in download_results if not r.success]
    
    # 本地卡片路径放在最前面
    final_paths = local_card_paths + local_paths
    
    return final_paths, failed_images


def _has_card_assets(result: Any) -> bool:
    cards = getattr(result, "cards", None)
    if not cards:
        return False
    return any(
        bool(path)
        for path in [
            getattr(cards, "title_card", None),
            getattr(cards, "debate_timeline", None),
            getattr(cards, "trend_analysis", None),
            getattr(cards, "platform_radar", None),
        ]
    )


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
    
    根据配置的 image_publish_mode 决定使用哪些图片:
    - ai_only: 仅使用 AI 生成的配图
    - ai_and_cards: 使用数据卡片 + AI 配图
    
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
        - images_used: int - 使用的图片数量
        - failed_images: List[str] - 验证失败的图片
        - publish_mode: str - 使用的发布模式
    """
    logger.info(f"[publish_to_xhs] 发布到小红书: job_id={job_id}")
    
    # 获取发布模式
    publish_mode = get_image_publish_mode()
    logger.info(f"[publish_to_xhs] 发布模式: {publish_mode}")
    
    # 参数验证
    if not job_id:
        return {
            "success": False,
            "error": "job_id 不能为空",
            "job_id": None,
            "note_url": None,
            "message": "缺少任务 ID",
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
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
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
        }
    
    # 检查是否已发布（防止重复发布）
    if job.published:
        logger.warning(f"[publish_to_xhs] 任务已发布过，拒绝重复发布: job_id={job_id}, published_at={job.published_at}")
        return {
            "success": False,
            "error": "该任务已发布过，不能重复发布。如需重新发布，请重新分析话题。",
            "job_id": job_id,
            "note_url": None,
            "message": "已发布过，拒绝重复发布",
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
            "already_published": True,
            "published_at": job.published_at.isoformat() if job.published_at else None,
        }
    
    # 检查任务状态
    if job.is_running:
        return {
            "success": False,
            "error": "任务仍在运行中，请等待完成后再发布",
            "job_id": job_id,
            "note_url": None,
            "message": "任务未完成",
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
        }
    
    if job.is_failed:
        return {
            "success": False,
            "error": f"任务失败，无法发布: {job.error_message}",
            "job_id": job_id,
            "note_url": None,
            "message": "任务失败",
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
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
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
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
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
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
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
        }
    
    # 使用自定义标签或原标签
    publish_tags = tags if tags else (copywriting.tags if copywriting.tags else [])
    logger.info(f"[publish_to_xhs] Tags 详情:")
    logger.info(f"  - 自定义 tags 参数: {tags}")
    logger.info(f"  - copywriting.tags: {copywriting.tags}")
    logger.info(f"  - 最终使用: {publish_tags}")
    
    # 获取正文内容
    content = copywriting.content
    if not content:
        return {
            "success": False,
            "error": "正文内容不能为空",
            "job_id": job_id,
            "note_url": None,
            "message": "缺少正文",
            "images_used": 0,
            "failed_images": [],
            "publish_mode": publish_mode,
        }
    
    # 收集并验证图片
    valid_images, failed_images = await collect_images_for_publish(result, publish_mode)
    fallback_used = False

    # 兜底: ai_only + 无 AI 图时，尝试回退到卡片发布，避免 image_count=0 无法发布
    if not valid_images and publish_mode == "ai_only" and _has_card_assets(result):
        logger.warning(
            "[publish_to_xhs] ai_only 模式下无可用 AI 图片，自动回退到 ai_and_cards 以继续发布"
        )
        valid_images, failed_images = await collect_images_for_publish(result, "ai_and_cards")
        if valid_images:
            publish_mode = "ai_and_cards"
            fallback_used = True
    
    if not valid_images:
        error_msg = "没有可发布的图片"
        if failed_images:
            error_msg += f"，{len(failed_images)} 个图片验证失败"
        if publish_mode == "ai_only":
            error_msg += "（当前模式为 ai_only，且未检测到可用 AI 图片）"
        return {
            "success": False,
            "error": error_msg,
            "job_id": job_id,
            "note_url": None,
            "message": error_msg,
            "images_used": 0,
            "failed_images": failed_images,
            "publish_mode": publish_mode,
        }
    
    # 记录图片信息
    logger.info(f"[publish_to_xhs] 本地图片: {len(valid_images)}, 下载失败: {len(failed_images)}")
    
    try:
        # 调用后端发布 API
        publish_result = await backend_client.publish_xhs(
            title=publish_title,
            content=content,
            images=valid_images,
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
                "images_used": len(valid_images),
                "failed_images": failed_images,
                "publish_mode": publish_mode,
            }
        
        # 获取笔记链接
        note_url = None
        data = publish_result.get("data")
        if isinstance(data, dict):
            note_url = data.get("note_url") or data.get("url")
        
        # 标记任务已发布（防止重复发布）
        from datetime import datetime
        job.published = True
        job.published_at = datetime.now()
        logger.info(f"[publish_to_xhs] 已标记任务为已发布: job_id={job_id}")
        
        logger.info(f"[publish_to_xhs] 发布成功: note_url={note_url}, images_used={len(valid_images)}")
        
        return {
            "success": True,
            "job_id": job_id,
            "note_url": note_url,
            "message": "发布成功（已自动回退到卡片发布）" if fallback_used else "发布成功",
            "images_used": len(valid_images),
            "failed_images": failed_images,
            "publish_mode": publish_mode,
            "fallback_used": fallback_used,
        }
        
    except Exception as e:
        logger.exception(f"[publish_to_xhs] 发布异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "job_id": job_id,
            "note_url": None,
            "message": f"发布异常: {str(e)}",
            "images_used": 0,
            "failed_images": failed_images,
            "publish_mode": publish_mode,
        }


# ============================================================
# 导出工具函数
# ============================================================

__all__ = [
    "publish_to_xhs",
]
