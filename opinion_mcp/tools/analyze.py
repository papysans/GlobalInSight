"""
MCP 分析工具

包含舆论分析相关的 MCP 工具:
- analyze_topic: 启动舆论分析任务
- get_analysis_status: 查询分析进度
- get_analysis_result: 获取分析结果
- update_copywriting: 修改文案
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger

from opinion_mcp.config import config
from opinion_mcp.schemas import (
    JobStatus,
    EventType,
    AnalyzeTopicResponse,
    AnalysisStatusResponse,
    AnalysisResultResponse,
    Copywriting,
    AnalysisCards,
    WebhookData,
)
from opinion_mcp.services.backend_client import backend_client
from opinion_mcp.services.job_manager import job_manager
from opinion_mcp.services.webhook_manager import webhook_manager


def _build_cards_meta(result: Any) -> Optional[Dict[str, Any]]:
    if not result or not result.cards:
        return None

    raw_cards = result.cards
    specs = [
        ("title_card", "标题卡"),
        ("debate_timeline", "辩论时间线"),
        ("trend_analysis", "趋势分析"),
        ("platform_radar", "平台雷达图"),
    ]

    items: List[Dict[str, Any]] = []
    for field, label in specs:
        items.append(
            {
                "type": field,
                "label": label,
                "ready": bool(getattr(raw_cards, field, None)),
            }
        )

    return {
        "total_ready": sum(1 for item in items if item["ready"]),
        "items": items,
    }


# ============================================================
# 5.2 analyze_topic 工具 - 启动分析任务
# ============================================================


async def analyze_topic(
    topic: str,
    platforms: Optional[List[str]] = None,
    debate_rounds: int = 2,
    image_count: int = 2,
) -> Dict[str, Any]:
    """
    启动舆论分析任务

    启动一个后台分析任务，立即返回 job_id。
    分析过程在后台执行，可通过 get_analysis_status 查询进度。

    Args:
        topic: 要分析的话题/议题
        platforms: 要爬取的平台列表，可选值: wb, dy, ks, bili, tieba, zhihu, xhs, hn, reddit
                   留空则使用默认平台
        debate_rounds: 辩论轮数 (1-5)，影响分析深度，默认2轮
        image_count: 生成图片数量 (0-9)，0表示不生图，默认2张

    Returns:
        Dict 包含:
        - success: bool - 是否成功启动
        - job_id: str - 任务 ID
        - message: str - 消息
        - estimated_time_minutes: int - 预估时间
        - platforms: List[str] - 爬取平台
        - hint: str - 提示信息

    Raises:
        ValueError: 如果话题为空或已有任务在运行
    """
    logger.info(f"[analyze_topic] 收到分析请求: topic={topic}, platforms={platforms}")

    # 参数验证
    if not topic or not topic.strip():
        return {
            "success": False,
            "error": "话题不能为空",
            "job_id": None,
        }

    topic = topic.strip()

    # 防重复调用：检查是否有相同话题的任务在运行或刚刚创建
    current_job = job_manager.get_current_job()
    if current_job:
        # 如果当前任务正在运行
        if current_job.is_running:
            logger.warning(f"[analyze_topic] 已有任务在运行: {current_job.job_id}")
            return {
                "success": False,
                "error": f"已有任务在运行中",
                "job_id": current_job.job_id,
                "topic": current_job.topic,
                "progress": current_job.progress,
                "hint": "请使用 get_analysis_status 查询进度，或等待任务完成",
            }

        # 如果是相同话题且在 60 秒内创建的任务（防止快速重复调用）
        if current_job.topic == topic:
            elapsed = (datetime.now() - current_job.created_at).total_seconds()
            if elapsed < 60:
                logger.warning(
                    f"[analyze_topic] 相同话题任务刚刚创建: {current_job.job_id}, {elapsed:.1f}秒前"
                )
                return {
                    "success": False,
                    "error": "相同话题的任务刚刚创建，请稍后再试",
                    "job_id": current_job.job_id,
                    "status": current_job.status.value,
                    "hint": f"任务创建于 {elapsed:.0f} 秒前，请使用 get_analysis_status 查询状态",
                }

    # 验证并处理平台参数
    if platforms:
        # 处理 "all" 或 "全部" 的情况
        if "all" in platforms or "全部" in platforms:
            platforms = [p["code"] for p in config.AVAILABLE_PLATFORMS]
        else:
            # 验证平台代码
            platforms = config.validate_platforms(platforms)
            if not platforms:
                return {
                    "success": False,
                    "error": f"无效的平台代码，可用平台: {[p['code'] for p in config.AVAILABLE_PLATFORMS]}",
                    "job_id": None,
                }
    else:
        platforms = config.DEFAULT_PLATFORMS

    # 验证辩论轮数
    debate_rounds = max(1, min(debate_rounds, config.MAX_DEBATE_ROUNDS))

    # 验证图片数量
    image_count = max(0, min(image_count, config.MAX_IMAGE_COUNT))

    # 创建任务
    try:
        job_id = job_manager.create_job(
            topic=topic,
            platforms=platforms,
            debate_rounds=debate_rounds,
            image_count=image_count,
        )
    except ValueError as e:
        # 已有任务在运行
        current_job = job_manager.get_current_job()
        return {
            "success": False,
            "error": str(e),
            "job_id": current_job.job_id if current_job else None,
            "hint": "请等待当前任务完成，或使用 get_analysis_status 查询进度",
        }

    # 更新任务状态为运行中
    job_manager.update_status(job_id, status=JobStatus.RUNNING)

    # 启动后台任务
    asyncio.create_task(
        _run_analysis_task(job_id, topic, platforms, debate_rounds, image_count)
    )

    # 计算预估时间 (基于平台数量和辩论轮数)
    estimated_time = 5 + len(platforms) * 1.5 + debate_rounds * 2

    logger.info(f"[analyze_topic] 任务已启动: job_id={job_id}")

    return {
        "success": True,
        "job_id": job_id,
        "message": "分析任务已启动",
        "estimated_time_minutes": int(estimated_time),
        "platforms": platforms,
        "hint": "请使用 get_analysis_status 查询进度",
    }


# ============================================================
# 5.3 get_analysis_status 工具 - 查询进度
# ============================================================


async def get_analysis_status(job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    查询舆论分析任务的当前状态和进度

    Args:
        job_id: 任务 ID，由 analyze_topic 返回。留空则查询最近一次任务

    Returns:
        Dict 包含:
        - success: bool - 是否成功
        - job_id: str - 任务 ID
        - running: bool - 是否运行中
        - current_step: str - 当前步骤代码
        - current_step_name: str - 当前步骤名称（中文）
        - progress: int - 进度百分比 (0-100)
        - topic: str - 分析话题
        - current_platform: str - 当前爬取平台
        - started_at: str - 开始时间
        - elapsed_minutes: float - 已用时间
        - estimated_remaining_minutes: float - 预估剩余时间
    """
    logger.debug(f"[get_analysis_status] 查询状态: job_id={job_id}")

    # 获取任务
    if job_id:
        job = job_manager.get_job(job_id)
    else:
        job = job_manager.get_current_job()

    if not job:
        return {
            "success": True,
            "job_id": None,
            "running": False,
            "message": "没有找到任务" if job_id else "当前没有运行中的任务",
        }

    # 计算预估剩余时间
    estimated_remaining = None
    if job.is_running and job.progress > 0:
        elapsed = job.elapsed_minutes or 0
        if elapsed > 0:
            # 基于当前进度估算总时间
            total_estimated = elapsed / (job.progress / 100)
            estimated_remaining = max(0, total_estimated - elapsed)

    return {
        "success": True,
        "job_id": job.job_id,
        "running": job.is_running,
        "current_step": job.current_step,
        "current_step_name": job.current_step_name,
        "progress": job.progress,
        "topic": job.topic,
        "current_platform": job.current_platform,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "elapsed_minutes": round(job.elapsed_minutes, 2)
        if job.elapsed_minutes
        else None,
        "estimated_remaining_minutes": round(estimated_remaining, 2)
        if estimated_remaining
        else None,
        "status": job.status.value,
        "error_message": job.error_message,
    }


# ============================================================
# 5.4 get_analysis_result 工具 - 获取结果 (含 cards)
# ============================================================


async def get_analysis_result(job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取已完成的舆论分析结果，包含文案和配图

    Args:
        job_id: 任务 ID。留空则获取最近一次完成的任务结果

    Returns:
        Dict 包含:
        - success: bool - 是否成功
        - job_id: str - 任务 ID
        - topic: str - 分析话题
        - copywriting: Dict - 文案内容 (title, subtitle, content, tags)
        - cards: Dict - 数据卡片元数据（类型、名称、是否已就绪）
        - cards_meta: Dict - 数据卡片元数据（类型、名称、是否已就绪）
        - ai_images: List[str] - AI 生成图片 URL 列表
        - summary: str - 核心观点摘要
        - insight: str - 深度洞察分析
        - platforms_analyzed: List[str] - 已分析平台列表
        - platform_stats: Dict - 各平台数据量统计
        - output_file: str - 输出文件路径
        - completed_at: str - 完成时间
        - duration_minutes: float - 耗时
    """
    logger.debug(f"[get_analysis_result] 获取结果: job_id={job_id}")

    # 获取任务
    if job_id:
        job = job_manager.get_job(job_id)
    else:
        # 获取最近完成的任务
        completed_jobs = job_manager.list_jobs(status=JobStatus.COMPLETED, limit=1)
        job = completed_jobs[0] if completed_jobs else None

    if not job:
        return {
            "success": False,
            "error": "任务不存在" if job_id else "没有已完成的任务",
            "job_id": job_id,
        }

    # 检查任务状态
    if job.is_running:
        return {
            "success": False,
            "error": "任务仍在运行中，请等待完成",
            "job_id": job.job_id,
            "progress": job.progress,
            "current_step_name": job.current_step_name,
        }

    if job.is_failed:
        return {
            "success": False,
            "error": f"任务失败: {job.error_message or '未知错误'}",
            "job_id": job.job_id,
        }

    # 构建结果
    result = job.result
    if not result:
        return {
            "success": False,
            "error": "任务已完成但没有结果数据",
            "job_id": job.job_id,
        }

    # 计算耗时
    duration_minutes = None
    if job.started_at and job.completed_at:
        duration_minutes = (job.completed_at - job.started_at).total_seconds() / 60

    cards_meta = _build_cards_meta(result)

    return {
        "success": True,
        "job_id": job.job_id,
        "topic": job.topic,
        "copywriting": result.copywriting.model_dump() if result.copywriting else None,
        "cards": cards_meta,
        "cards_meta": cards_meta,
        "ai_images": result.ai_images,
        "summary": result.summary,
        "insight": result.insight,
        "platforms_analyzed": result.platforms_analyzed,
        "platform_stats": result.platform_stats,
        "output_file": result.output_file,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_minutes": round(duration_minutes, 2) if duration_minutes else None,
    }


# ============================================================
# 5.5 update_copywriting 工具 - 修改文案
# ============================================================


async def update_copywriting(
    job_id: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    修改分析结果的文案内容

    Args:
        job_id: 任务 ID
        title: 新标题（留空则不修改）
        subtitle: 新副标题（留空则不修改）
        content: 新正文内容（留空则不修改）
        tags: 新标签列表（留空则不修改）

    Returns:
        Dict 包含:
        - success: bool - 是否成功
        - job_id: str - 任务 ID
        - updated_fields: List[str] - 已更新的字段列表
        - copywriting: Dict - 更新后的文案内容
    """
    logger.info(f"[update_copywriting] 更新文案: job_id={job_id}")

    if not job_id:
        return {
            "success": False,
            "error": "job_id 不能为空",
        }

    # 检查是否有任何更新
    if title is None and subtitle is None and content is None and tags is None:
        return {
            "success": False,
            "error": "至少需要提供一个要更新的字段",
        }

    # 更新文案
    job, updated_fields = job_manager.update_copywriting(
        job_id=job_id,
        title=title,
        subtitle=subtitle,
        content=content,
        tags=tags,
    )

    if not job:
        return {
            "success": False,
            "error": f"任务不存在: {job_id}",
        }

    # 获取更新后的文案
    copywriting = None
    if job.result and job.result.copywriting:
        copywriting = job.result.copywriting.model_dump()

    return {
        "success": True,
        "job_id": job_id,
        "updated_fields": updated_fields,
        "copywriting": copywriting,
    }


# ============================================================
# 5.6 后台任务执行逻辑 (asyncio.create_task)
# ============================================================


async def _run_analysis_task(
    job_id: str,
    topic: str,
    platforms: List[str],
    debate_rounds: int,
    image_count: int = 2,
) -> None:
    """
    后台执行分析任务

    调用后端 API 进行分析，解析 SSE 事件并更新任务状态。
    在关键节点触发 Webhook 推送。

    Args:
        job_id: 任务 ID
        topic: 分析话题
        platforms: 平台列表
        debate_rounds: 辩论轮数
        image_count: AI 配图数量，默认 2 张
    """
    logger.info(f"[_run_analysis_task] 开始执行任务: job_id={job_id}")

    # 推送任务开始事件
    await webhook_manager.push_started(job_id, topic, platforms)

    # 用于跟踪当前步骤和平台完成情况
    current_step = None
    platform_stats: Dict[str, int] = {}
    platforms_analyzed: List[str] = []

    # 用于存储分析结果
    summary = ""
    insight = ""
    title = ""
    subtitle = ""
    content = ""
    tags: List[str] = []
    cards: Dict[str, str] = {}
    ai_images: List[str] = []
    output_file = None

    try:
        # 调用后端分析 API
        async for event in backend_client.call_analyze_api(
            topic=topic,
            platforms=platforms,
            debate_rounds=debate_rounds,
            image_count=image_count,
        ):
            # 处理错误事件
            if event.get("status") == "error":
                error_msg = event.get("step_content", "未知错误")
                logger.error(f"[_run_analysis_task] 分析出错: {error_msg}")

                job_manager.update_status(
                    job_id,
                    status=JobStatus.FAILED,
                    error_message=error_msg,
                )

                # 推送失败事件
                await webhook_manager.push_failed(job_id, error_msg, current_step)
                return

            # 解析事件数据
            agent_name = event.get("agent_name", "")
            step_content = event.get("step_content", "")
            status = event.get("status", "")

            # 5.7 在 SSE 事件中触发 Webhook 推送
            await _process_sse_event(
                job_id=job_id,
                agent_name=agent_name,
                step_content=step_content,
                status=status,
                event=event,
                current_step=current_step,
                platform_stats=platform_stats,
                platforms_analyzed=platforms_analyzed,
            )

            # 更新当前步骤
            new_step = _map_agent_to_step(agent_name)
            if new_step and new_step != current_step:
                current_step = new_step
                step_info = config.get_step_info(current_step)

                job_manager.update_status(
                    job_id,
                    current_step=current_step,
                    current_step_name=step_info["name"],
                    progress=step_info["progress"],
                )

                # 推送步骤变更事件
                await webhook_manager.push_step_change(
                    job_id,
                    current_step,
                    step_info["name"],
                    step_info["progress"],
                )

            # 提取结果数据
            summary_ref = {"value": summary}
            insight_ref = {"value": insight}
            title_ref = {"value": title}
            subtitle_ref = {"value": subtitle}
            content_ref = {"value": content}
            tags_ref = {"value": tags}
            cards_ref = {"value": cards}
            ai_images_ref = {"value": ai_images}
            output_file_ref = {"value": output_file}

            _extract_result_data(
                event=event,
                agent_name=agent_name,
                summary_ref=summary_ref,
                insight_ref=insight_ref,
                title_ref=title_ref,
                subtitle_ref=subtitle_ref,
                content_ref=content_ref,
                tags_ref=tags_ref,
                cards_ref=cards_ref,
                ai_images_ref=ai_images_ref,
                output_file_ref=output_file_ref,
            )

            # 从引用中更新变量
            if ai_images_ref["value"]:
                ai_images = ai_images_ref["value"]
                logger.info(
                    f"[_run_analysis_task] 从 _extract_result_data 获取到 {len(ai_images)} 张图片"
                )
            if cards_ref["value"]:
                cards = cards_ref["value"]
            if output_file_ref["value"]:
                output_file = output_file_ref["value"]

            # 更新引用值
            summary = summary or event.get("summary", "")
            insight = insight or event.get("insight", "")

            # 从 Analyst 输出中提取 SUMMARY 和 INSIGHT
            if agent_name.lower() == "analyst":
                analyst_content = step_content or ""
                if analyst_content:
                    parsed_analyst = _parse_analyst_output(analyst_content)
                    if parsed_analyst.get("summary") and not summary:
                        summary = parsed_analyst["summary"]
                    if parsed_analyst.get("insight") and not insight:
                        insight = parsed_analyst["insight"]
                    if parsed_analyst.get("title") and not title:
                        title = parsed_analyst["title"]
                    if parsed_analyst.get("subtitle") and not subtitle:
                        subtitle = parsed_analyst["subtitle"]

            # 处理 writer 输出 - 优先使用 final_copy 字段
            if agent_name.lower() == "writer":
                # 优先使用后端发送的 final_copy 字段
                writer_content = (
                    event.get("final_copy")
                    or step_content
                    or event.get("step_content", "")
                )
                logger.debug(
                    f"[_run_analysis_task] Writer 原始内容来源: final_copy={bool(event.get('final_copy'))}, step_content={bool(step_content)}"
                )
                logger.debug(
                    f"[_run_analysis_task] Writer 原始内容长度: {len(writer_content) if writer_content else 0}"
                )
                if writer_content:
                    # 解析 TITLE:, EMOJI:, THEME:, CONTENT: 格式
                    parsed = _parse_writer_output(writer_content)
                    if parsed.get("title"):
                        title = parsed["title"]
                    if parsed.get("content"):
                        content = parsed["content"]
                    if parsed.get("tags"):
                        tags = parsed["tags"]
                    logger.info(
                        f"[_run_analysis_task] Writer 输出解析: title={title[:20] if title else 'N/A'}..., content_len={len(content)}, tags_count={len(tags)}"
                    )

            # 处理图片生成输出
            if agent_name.lower() == "image_generator":
                # 直接从 event 中获取 image_urls
                img_urls = event.get("image_urls", [])
                if img_urls:
                    ai_images = img_urls
                    logger.info(
                        f"[_run_analysis_task] 获取到 {len(ai_images)} 张图片: {ai_images}"
                    )

            # 处理输出文件
            if event.get("output_file"):
                output_file = event.get("output_file")

            # 处理平台爬取完成
            if agent_name == "crawler_agent":
                platform_data = event.get("platform_data", {})
                if platform_data:
                    for platform_code, count in platform_data.items():
                        if platform_code not in platform_stats:
                            platform_stats[platform_code] = count
                            platform_name = config.get_platform_name(platform_code)
                            platforms_analyzed.append(platform_name)

                            # 推送平台完成事件
                            progress = min(10 + len(platform_stats) * 2, 20)
                            await webhook_manager.push_platform_done(
                                job_id,
                                platform_code,
                                platform_name,
                                count,
                                progress,
                            )

                            job_manager.update_status(
                                job_id,
                                current_platform=platform_code,
                                progress=progress,
                            )

        # 分析完成，存储结果
        job_manager.store_result(
            job_id=job_id,
            summary=summary,
            insight=insight,
            title=title,
            subtitle=subtitle,
            content=content,
            tags=tags,
            cards=cards,
            ai_images=ai_images,
            platforms_analyzed=platforms_analyzed,
            platform_stats=platform_stats,
            output_file=output_file,
        )

        # 更新任务状态为完成
        job_manager.update_status(
            job_id,
            status=JobStatus.COMPLETED,
            current_step="finished",
            current_step_name="完成",
            progress=100,
        )

        # 自动生成数据卡片（如果渲染服务可用）
        try:
            from opinion_mcp.tools.render_cards import generate_topic_cards

            logger.info(f"[_run_analysis_task] 尝试自动生成数据卡片: job_id={job_id}")
            cards_result = await generate_topic_cards(job_id=job_id)
            if cards_result.get("success"):
                logger.info(
                    f"[_run_analysis_task] 数据卡片生成成功: {cards_result.get('message')}"
                )
            else:
                logger.warning(
                    f"[_run_analysis_task] 数据卡片生成跳过/失败: {cards_result.get('message', '未知原因')}"
                )
        except Exception as card_err:
            # 卡片生成失败不影响主流程
            logger.warning(
                f"[_run_analysis_task] 数据卡片自动生成异常（不影响主流程）: {card_err}"
            )

        # 获取任务信息计算耗时
        job = job_manager.get_job(job_id)
        duration_minutes = job.elapsed_minutes if job else None

        # 推送完成事件
        await webhook_manager.push_completed(
            job_id,
            result=job.result if job else None,
            duration_minutes=duration_minutes,
        )

        logger.info(f"[_run_analysis_task] 任务完成: job_id={job_id}")

    except Exception as e:
        logger.exception(f"[_run_analysis_task] 任务执行异常: {e}")

        job_manager.update_status(
            job_id,
            status=JobStatus.FAILED,
            error_message=str(e),
        )

        await webhook_manager.push_failed(job_id, str(e), current_step)


async def _process_sse_event(
    job_id: str,
    agent_name: str,
    step_content: str,
    status: str,
    event: Dict[str, Any],
    current_step: Optional[str],
    platform_stats: Dict[str, int],
    platforms_analyzed: List[str],
) -> None:
    """
    处理 SSE 事件并触发 Webhook 推送

    Args:
        job_id: 任务 ID
        agent_name: Agent 名称
        step_content: 步骤内容
        status: 状态
        event: 完整事件数据
        current_step: 当前步骤
        platform_stats: 平台统计
        platforms_analyzed: 已分析平台
    """
    # 处理辩论轮次
    if agent_name == "debater" and "round" in step_content.lower():
        # 尝试提取轮次信息
        import re

        match = re.search(r"(\d+)", step_content)
        if match:
            round_num = match.group(1)
            await webhook_manager.push_progress(
                job_id,
                "debater",
                "多角度辩论",
                60,
                f"🔄 正在进行多角度辩论 (第{round_num}轮)...",
            )

    # 处理图片生成进度
    if agent_name == "image_generator" and status == "generating":
        image_progress = event.get("image_progress", {})
        current = image_progress.get("current", 0)
        total = image_progress.get("total", 0)
        if current and total:
            await webhook_manager.push_progress(
                job_id,
                "image_generator",
                "图片生成",
                95,
                f"🔄 正在生成配图 ({current}/{total})...",
            )


def _map_agent_to_step(agent_name: str) -> Optional[str]:
    """
    将 Agent 名称映射到步骤代码

    Args:
        agent_name: Agent 名称

    Returns:
        步骤代码，如果无法映射则返回 None
    """
    agent_step_map = {
        "crawler_agent": "crawler_agent",
        "crawler": "crawler_agent",
        "reporter": "reporter",
        "analyst": "analyst",
        "debater": "debater",
        "writer": "writer",
        "image_generator": "image_generator",
        "image generator": "image_generator",
        "finished": "finished",
        "system": "finished",
    }
    return agent_step_map.get(agent_name.lower())


def _parse_writer_output(content: str) -> Dict[str, Any]:
    """
    解析 Writer 输出的格式

    Writer 输出格式:
    TITLE: [标题]
    EMOJI: [emoji]
    THEME: [主题色]
    CONTENT:
    [正文内容]
    #标签 #标签

    Args:
        content: Writer 的原始输出

    Returns:
        解析后的字典，包含 title, emoji, theme, content, tags
    """
    import re

    result = {"title": "", "emoji": "", "theme": "", "content": "", "tags": []}

    if not content:
        logger.warning("[_parse_writer_output] 输入内容为空")
        return result

    # 打印原始内容的最后 200 个字符，用于调试标签问题
    logger.info(f"[_parse_writer_output] 开始解析，输入长度: {len(content)}")
    logger.info(
        f"[_parse_writer_output] 原始内容末尾 200 字符: ...{content[-200:] if len(content) > 200 else content}"
    )

    lines = content.split("\n")
    content_started = False
    content_lines = []

    for line in lines:
        line_stripped = line.strip()

        # 解析 TITLE:
        if line_stripped.upper().startswith("TITLE:"):
            result["title"] = line_stripped[6:].strip()
            logger.debug(
                f"[_parse_writer_output] 解析到 TITLE: {result['title'][:30]}..."
            )
            continue

        # 解析 EMOJI:
        if line_stripped.upper().startswith("EMOJI:"):
            result["emoji"] = line_stripped[6:].strip()
            continue

        # 解析 THEME:
        if line_stripped.upper().startswith("THEME:"):
            result["theme"] = line_stripped[6:].strip()
            continue

        # 解析 CONTENT: 开始
        if line_stripped.upper().startswith("CONTENT:"):
            content_started = True
            # CONTENT: 后面可能有内容
            remaining = line_stripped[8:].strip()
            if remaining:
                content_lines.append(remaining)
            logger.debug(f"[_parse_writer_output] 检测到 CONTENT: 标记，开始收集正文")
            continue

        # 收集正文内容
        if content_started:
            content_lines.append(line)

    # 合并正文
    full_content = "\n".join(content_lines).strip()
    logger.debug(f"[_parse_writer_output] 收集到正文长度: {len(full_content)}")

    # 提取标签 (以 # 开头的词，支持中文和英文)
    # 匹配 #标签 格式，标签可以包含中文、英文、数字
    tag_pattern = r"#([\w\u4e00-\u9fff]+)"
    tags = re.findall(tag_pattern, full_content)
    result["tags"] = tags
    logger.info(
        f"[_parse_writer_output] 提取到标签: {tags}, 正文中包含 # 的位置: {[i for i, c in enumerate(full_content) if c == '#']}"
    )

    # 移除标签行，保留纯正文
    # 标签通常在最后一行
    content_without_tags = re.sub(
        r"\n*#[\w\u4e00-\u9fff]+(\s+#[\w\u4e00-\u9fff]+)*\s*$", "", full_content
    ).strip()
    result["content"] = content_without_tags

    logger.info(
        f"[_parse_writer_output] 解析完成: title_len={len(result['title'])}, content_len={len(result['content'])}, tags={len(result['tags'])}"
    )

    return result


def _parse_analyst_output(content: str) -> Dict[str, Any]:
    """
    解析 Analyst 输出的格式

    Analyst 输出格式:
    SUMMARY: [核心观点]
    INSIGHT: [深度洞察]
    TITLE: [主标题]
    SUB: [副标题]

    Args:
        content: Analyst 的原始输出

    Returns:
        解析后的字典，包含 summary, insight, title, subtitle
    """
    import re

    result = {"summary": "", "insight": "", "title": "", "subtitle": ""}

    if not content:
        return result

    # 使用正则提取各字段
    # SUMMARY: 可能跨行，直到下一个标记
    summary_match = re.search(
        r"SUMMARY:\s*(.+?)(?=\n(?:INSIGHT|TITLE|SUB):|$)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if summary_match:
        result["summary"] = summary_match.group(1).strip()

    insight_match = re.search(
        r"INSIGHT:\s*(.+?)(?=\n(?:SUMMARY|TITLE|SUB):|$)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if insight_match:
        result["insight"] = insight_match.group(1).strip()

    title_match = re.search(r"TITLE:\s*(.+?)(?=\n|$)", content, re.IGNORECASE)
    if title_match:
        result["title"] = title_match.group(1).strip()

    sub_match = re.search(r"SUB:\s*(.+?)(?=\n|$)", content, re.IGNORECASE)
    if sub_match:
        result["subtitle"] = sub_match.group(1).strip()

    return result


def _extract_result_data(
    event: Dict[str, Any],
    agent_name: str,
    summary_ref: Dict[str, Any],
    insight_ref: Dict[str, Any],
    title_ref: Dict[str, Any],
    subtitle_ref: Dict[str, Any],
    content_ref: Dict[str, Any],
    tags_ref: Dict[str, Any],
    cards_ref: Dict[str, Any],
    ai_images_ref: Dict[str, Any],
    output_file_ref: Dict[str, Any],
) -> None:
    """
    从事件中提取结果数据

    使用引用字典来模拟可变参数
    """
    # 提取 summary 和 insight
    if event.get("summary"):
        summary_ref["value"] = event["summary"]
    if event.get("insight"):
        insight_ref["value"] = event["insight"]

    # 提取 writer 结果
    if agent_name == "writer":
        result = event.get("result", {})
        if isinstance(result, dict):
            if result.get("title"):
                title_ref["value"] = result["title"]
            if result.get("subtitle"):
                subtitle_ref["value"] = result["subtitle"]
            if result.get("content"):
                content_ref["value"] = result["content"]
            if result.get("tags"):
                tags_ref["value"] = result["tags"]

    # 提取图片生成结果
    if agent_name == "image_generator" or agent_name.lower() == "image generator":
        # 优先从 image_urls 获取（后端 SSE 发送的格式）
        img_urls = event.get("image_urls", [])
        if img_urls:
            ai_images_ref["value"] = img_urls
            logger.debug(
                f"[_extract_result_data] 从 image_urls 获取到 {len(img_urls)} 张图片"
            )
        else:
            # 兼容旧格式 result.images
            result = event.get("result", {})
            if isinstance(result, dict):
                if result.get("images"):
                    ai_images_ref["value"] = result["images"]
                if result.get("cards"):
                    cards_ref["value"] = result["cards"]

    # 提取输出文件
    if event.get("output_file"):
        output_file_ref["value"] = event["output_file"]


# ============================================================
# 导出工具函数
# ============================================================

__all__ = [
    "analyze_topic",
    "get_analysis_status",
    "get_analysis_result",
    "update_copywriting",
]
