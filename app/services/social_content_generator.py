"""
社交内容生成服务

将行情推演结果转化为适合社交平台发布的内容：
- 小红书图文（争议性标题 + 多空对决 + 情绪数据 + AI配图）
- 微博短文（140字以内，尖锐观点 + 反问引导）
- 雪球长文（完整多空辩论 + 数据论证）
- 知乎长文（争议性问题标题 + "回答"体裁 + 逻辑推理）
- 每日速报（情绪概况 + 大盘概况 + 板块异动 + 热点解读）

所有内容生成后经过合规脱敏处理，持久化到数据库。
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from app.llm import get_agent_llm
from app.schemas import (
    SocialContent,
    SocialContentRequest,
    StockAnalysisResult,
    StockNewsItem,
)
from app.services.compliance_service import compliance_service


# ---------------------------------------------------------------------------
# LLM Prompt 模板
# ---------------------------------------------------------------------------

XHS_PROMPT = """你是一位深谙小红书流量密码的资深财经内容策划。
请基于以下行情推演结果，创作一篇争议性的股票分析笔记。

推演主题：{topic}
争议性结论：{conclusion}
多头核心观点：{bull_summary}
空头核心观点：{bear_summary}
{sentiment_hint}

【写作原则】
1. 标题要争议性十足，能引发讨论（12-18字，含1个emoji）
2. 正文呈现多空双方核心论点，构建"你站哪边？"式互动
3. 融入情绪数据亮点（如"散户恐慌指数已飙到 85"）增强传播力
4. 结尾用互动引导收尾（如"你怎么看？评论区见"）
5. 控制在 200-400 字
6. 禁止使用 **bold** 格式

【输出格式（严格遵守）】
TITLE: [标题]
CONTENT:
[正文内容]
TAGS: [标签1,标签2,标签3]"""

WEIBO_PROMPT = """你是一位微博财经大V，擅长用一句话引爆评论区。
请基于以下推演结果，生成一条微博短文。

争议性结论：{conclusion}
多头核心观点：{bull_summary}
空头核心观点：{bear_summary}
{sentiment_hint}

【写作原则】
1. 从争议性结论中提取最尖锐的观点
2. 结合情绪指数数据增强冲击力
3. 用反问句收尾引发讨论
4. 严格控制在 140 字以内（含标签）
5. 附带 2-3 个话题标签（#话题#格式）

【输出格式（严格遵守）】
CONTENT:
[正文内容，含话题标签，总计不超过140字]
TAGS: [标签1,标签2,标签3]"""

XUEQIU_PROMPT = """你是一位雪球社区的资深投资者，擅长深度分析长文。
请基于以下推演结果，生成一篇雪球长文。

推演主题：{topic}
争议性结论：{conclusion}
多头观点：{bull_argument}
空头观点：{bear_argument}
多空交锋对话：{debate_dialogue}
{sentiment_hint}

【写作原则】
1. 以争议性标题开头
2. 完整呈现多空交锋对话
3. 引用情绪指数各分项得分作为量化论据
4. 结尾带免责声明
5. 控制在 800-1500 字

【输出格式（严格遵守）】
TITLE: [标题]
CONTENT:
[正文内容]
TAGS: [标签1,标签2,标签3]"""

ZHIHU_PROMPT = """你是一位知乎财经领域的优质回答者，擅长逻辑推理和数据引用。
请基于以下推演结果，生成一篇知乎风格的深度分析。

推演主题：{topic}
争议性结论：{conclusion}
多头观点：{bull_argument}
空头观点：{bear_argument}
{sentiment_hint}

【写作原则】
1. 以争议性问题为标题（如"XX行业真的到了拐点吗？"）
2. 以知乎"回答"体裁展开，先摆数据和事实
3. 引用情绪数据作为量化论据
4. 用逻辑推理而非情绪渲染
5. 结尾带免责声明和互动引导
6. 控制在 800-1500 字

【输出格式（严格遵守）】
TITLE: [问题标题]
CONTENT:
[回答正文]
TAGS: [标签1,标签2,标签3]"""

DAILY_REPORT_PROMPT = """你是一位资深财经编辑，负责撰写每日股市速报。
请基于以下今日热点资讯，生成一份{platform_name}风格的每日速报。

今日热点资讯：
{news_summary}

{sentiment_hint}

【速报结构（必须包含以下板块）】
1. 情绪概况：综合恐慌/贪婪指数、各分项得分变化、情绪趋势方向
2. 大盘概况：今日大盘走势概述
3. 板块异动：涨幅/跌幅居前的板块
4. 热点事件解读：今日最受关注的 2-3 条资讯解读

【平台风格要求】
{platform_style}

【输出格式（严格遵守）】
TITLE: [标题]
CONTENT:
[正文内容]
TAGS: [标签1,标签2,标签3]"""

PLATFORM_STYLES = {
    "xhs": "小红书风格：标题含emoji，正文轻松活泼，200-400字，互动引导收尾",
    "weibo": "微博风格：简洁有力，140字以内，话题标签，反问句收尾",
    "xueqiu": "雪球风格：专业深度，数据引用，800-1500字，免责声明",
    "zhihu": "知乎风格：逻辑严谨，数据论证，800-1500字，免责声明",
}

PLATFORM_NAMES = {
    "xhs": "小红书",
    "weibo": "微博",
    "xueqiu": "雪球",
    "zhihu": "知乎",
}

DISCLAIMER = "以上内容仅为市场观点讨论，不构成任何投资建议"

ENABLED_PLATFORMS = ["xhs"]  # 当前支持全自动发布的平台


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _extract_text(content: Any) -> str:
    """从 LLM 响应中提取纯文本"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _parse_llm_output(raw: str) -> Dict[str, str]:
    """解析 LLM 输出，提取 TITLE / CONTENT / TAGS 字段"""
    result = {"title": "", "body": "", "tags": []}
    lines = raw.strip().split("\n")
    current_field = None
    content_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("TITLE:"):
            if current_field == "body":
                result["body"] = "\n".join(content_lines).strip()
                content_lines = []
            result["title"] = stripped[6:].strip()
            current_field = "title"
        elif stripped.upper().startswith("CONTENT:"):
            if current_field == "body":
                result["body"] = "\n".join(content_lines).strip()
            content_lines = []
            current_field = "body"
        elif stripped.upper().startswith("TAGS:"):
            if current_field == "body":
                result["body"] = "\n".join(content_lines).strip()
                content_lines = []
            tags_raw = stripped[5:].strip()
            # 支持逗号分隔或空格分隔
            tags = [t.strip().lstrip("#").strip() for t in tags_raw.replace("，", ",").split(",")]
            result["tags"] = [t for t in tags if t]
            current_field = "tags"
        elif current_field == "body":
            content_lines.append(line)

    if current_field == "body" and content_lines:
        result["body"] = "\n".join(content_lines).strip()

    return result


def _build_sentiment_hint(sentiment_context: Optional[Dict]) -> str:
    """根据情绪数据构建 prompt 提示片段"""
    if sentiment_context is None:
        return ""
    try:
        index_val = sentiment_context.get("index_value", sentiment_context.get("composite_index", "N/A"))
        label = sentiment_context.get("label", "未知")
        sub_scores = sentiment_context.get("sub_scores", {})
        comment = sub_scores.get("comment", "N/A")
        baidu = sub_scores.get("baidu_vote", "N/A")
        margin = sub_scores.get("margin", "N/A")
        trend = sentiment_context.get("trend_direction", "N/A")
        return (
            f"\n【当前市场情绪数据】\n"
            f"综合情绪指数: {index_val}（{label}），趋势: {trend}\n"
            f"评论情绪: {comment}，百度投票看涨: {baidu}，融资融券: {margin}\n"
            f"请在内容中引用以上情绪数据增强说服力。\n"
        )
    except Exception:
        return ""


def _generate_content_id() -> str:
    """生成内容唯一 ID"""
    return f"sc_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _ensure_disclaimer(body: str) -> str:
    """确保正文包含免责声明"""
    if DISCLAIMER not in body:
        body = body.rstrip() + f"\n\n{DISCLAIMER}"
    return body


# ---------------------------------------------------------------------------
# SocialContentGenerator
# ---------------------------------------------------------------------------

class SocialContentGenerator:
    """社交内容生成服务

    将行情推演结果转化为适合社交平台发布的内容，
    集成配图生成和小红书发布能力。
    """

    def __init__(self):
        self._image_service = None
        self._xhs_publisher = None

    @property
    def image_service(self):
        if self._image_service is None:
            from app.services.image_generator import image_generator_service
            self._image_service = image_generator_service
        return self._image_service

    @property
    def xhs_publisher(self):
        if self._xhs_publisher is None:
            from app.services.xiaohongshu_publisher import xiaohongshu_publisher
            self._xhs_publisher = xiaohongshu_publisher
        return self._xhs_publisher

    # ------------------------------------------------------------------
    # LLM 调用
    # ------------------------------------------------------------------

    async def _call_llm(self, system_prompt: str, user_content: str) -> str:
        """调用 writer agent LLM"""
        llm = get_agent_llm("writer")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]
        response = await llm.ainvoke(messages)
        return _extract_text(response.content)

    # ------------------------------------------------------------------
    # 合规脱敏处理
    # ------------------------------------------------------------------

    def _apply_compliance(self, body: str, platform: str) -> str:
        """对内容执行完整合规流程：脱敏 → 免责声明 → 合规检查。

        流程：
        1. 获取平台对应的脱敏级别
        2. desensitize_content() 脱敏处理
        3. add_disclaimer() 附加免责声明
        4. check_compliance() 合规检查（仅记录警告，不拦截）
        """
        level = compliance_service.get_desensitization_level(platform)
        body = compliance_service.desensitize_content(body, level)
        body = compliance_service.add_disclaimer(body)
        result = compliance_service.check_compliance(body)
        if not result.is_compliant:
            logger.warning(
                f"合规检查警告 [{platform}]: violations={result.violations}"
            )
        if result.warnings:
            logger.info(f"合规提示 [{platform}]: {result.warnings}")
        return body

    # ------------------------------------------------------------------
    # 情绪数据获取（Phase 3 可选依赖）
    # ------------------------------------------------------------------

    def _get_sentiment_context(self, analysis: StockAnalysisResult) -> Optional[Dict]:
        """从推演结果中获取情绪上下文，不可用时返回 None"""
        return analysis.sentiment_context

    # ------------------------------------------------------------------
    # 各平台内容生成
    # ------------------------------------------------------------------

    async def generate_xhs_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成小红书风格图文内容"""
        sentiment_ctx = self._get_sentiment_context(analysis)
        sentiment_hint = _build_sentiment_hint(sentiment_ctx)

        prompt_content = XHS_PROMPT.format(
            topic=analysis.news_titles[0] if analysis.news_titles else "",
            conclusion=analysis.controversial_conclusion[:300],
            bull_summary=analysis.bull_argument[:200],
            bear_summary=analysis.bear_argument[:200],
            sentiment_hint=sentiment_hint,
        )

        raw = await self._call_llm(
            "你是一位深谙小红书流量密码的资深财经内容策划。",
            prompt_content,
        )
        parsed = _parse_llm_output(raw)

        # 生成配图
        image_urls = []
        try:
            image_urls = await self.image_service.generate_images(
                parsed.get("body", ""), insight=analysis.controversial_conclusion, image_count=2
            )
        except Exception as e:
            logger.warning(f"小红书配图生成失败: {e}")

        # 合规脱敏处理
        original_body = parsed.get("body", "")
        body = self._apply_compliance(original_body, "xhs")

        return SocialContent(
            id=_generate_content_id(),
            platform="xhs",
            title=parsed.get("title", ""),
            body=body,
            tags=parsed.get("tags", []),
            image_urls=image_urls,
            source_analysis_id=analysis.id,
            content_type="analysis",
            status="draft",
            created_at=datetime.now().isoformat(),
            original_content=original_body,
        )

    async def generate_weibo_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成微博短文内容（140字以内）"""
        sentiment_ctx = self._get_sentiment_context(analysis)
        sentiment_hint = _build_sentiment_hint(sentiment_ctx)

        prompt_content = WEIBO_PROMPT.format(
            conclusion=analysis.controversial_conclusion[:300],
            bull_summary=analysis.bull_argument[:150],
            bear_summary=analysis.bear_argument[:150],
            sentiment_hint=sentiment_hint,
        )

        raw = await self._call_llm(
            "你是一位微博财经大V，擅长用一句话引爆评论区。",
            prompt_content,
        )
        parsed = _parse_llm_output(raw)

        original_body = parsed.get("body", "")
        # 微博 140 字限制：截断
        if len(original_body) > 140:
            original_body = original_body[:137] + "..."
        # 合规脱敏处理
        body = self._apply_compliance(original_body, "weibo")

        return SocialContent(
            id=_generate_content_id(),
            platform="weibo",
            title="",
            body=body,
            tags=parsed.get("tags", []),
            image_urls=[],
            source_analysis_id=analysis.id,
            content_type="analysis",
            status="draft",
            created_at=datetime.now().isoformat(),
            original_content=original_body,
        )

    async def generate_xueqiu_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成雪球长文内容"""
        sentiment_ctx = self._get_sentiment_context(analysis)
        sentiment_hint = _build_sentiment_hint(sentiment_ctx)

        prompt_content = XUEQIU_PROMPT.format(
            topic=analysis.news_titles[0] if analysis.news_titles else "",
            conclusion=analysis.controversial_conclusion[:300],
            bull_argument=analysis.bull_argument[:500],
            bear_argument=analysis.bear_argument[:500],
            debate_dialogue=analysis.debate_dialogue[:800],
            sentiment_hint=sentiment_hint,
        )

        raw = await self._call_llm(
            "你是一位雪球社区的资深投资者，擅长深度分析长文。",
            prompt_content,
        )
        parsed = _parse_llm_output(raw)
        original_body = parsed.get("body", "")
        body = self._apply_compliance(original_body, "xueqiu")

        return SocialContent(
            id=_generate_content_id(),
            platform="xueqiu",
            title=parsed.get("title", ""),
            body=body,
            tags=parsed.get("tags", []),
            image_urls=[],
            source_analysis_id=analysis.id,
            content_type="analysis",
            status="draft",
            created_at=datetime.now().isoformat(),
            original_content=original_body,
        )

    async def generate_zhihu_content(self, analysis: StockAnalysisResult) -> SocialContent:
        """生成知乎风格长文内容"""
        sentiment_ctx = self._get_sentiment_context(analysis)
        sentiment_hint = _build_sentiment_hint(sentiment_ctx)

        prompt_content = ZHIHU_PROMPT.format(
            topic=analysis.news_titles[0] if analysis.news_titles else "",
            conclusion=analysis.controversial_conclusion[:300],
            bull_argument=analysis.bull_argument[:500],
            bear_argument=analysis.bear_argument[:500],
            sentiment_hint=sentiment_hint,
        )

        raw = await self._call_llm(
            "你是一位知乎财经领域的优质回答者，擅长逻辑推理和数据引用。",
            prompt_content,
        )
        parsed = _parse_llm_output(raw)
        original_body = parsed.get("body", "")
        body = self._apply_compliance(original_body, "zhihu")

        return SocialContent(
            id=_generate_content_id(),
            platform="zhihu",
            title=parsed.get("title", ""),
            body=body,
            tags=parsed.get("tags", []),
            image_urls=[],
            source_analysis_id=analysis.id,
            content_type="analysis",
            status="draft",
            created_at=datetime.now().isoformat(),
            original_content=original_body,
        )

    async def generate_daily_report(
        self, news_items: List[StockNewsItem]
    ) -> Dict[str, SocialContent]:
        """生成每日速报，为每个平台生成独立的内容副本"""
        # 构建资讯摘要
        news_summary = "\n".join(
            f"- [{item.source_name}] {item.title}"
            for item in (news_items or [])[:20]
        )
        if not news_summary:
            news_summary = "暂无今日热点资讯"

        # 尝试获取情绪数据（Phase 3 可选依赖）
        sentiment_hint = ""
        # 当前阶段无情绪数据，跳过

        results: Dict[str, SocialContent] = {}
        for platform in ["xhs", "weibo", "xueqiu", "zhihu"]:
            try:
                prompt_content = DAILY_REPORT_PROMPT.format(
                    platform_name=PLATFORM_NAMES.get(platform, platform),
                    news_summary=news_summary,
                    sentiment_hint=sentiment_hint,
                    platform_style=PLATFORM_STYLES.get(platform, ""),
                )

                raw = await self._call_llm(
                    f"你是一位资深财经编辑，负责撰写{PLATFORM_NAMES.get(platform, '')}风格的每日速报。",
                    prompt_content,
                )
                parsed = _parse_llm_output(raw)
                original_body = parsed.get("body", "")

                # 微博速报也需要控制字数
                if platform == "weibo" and len(original_body) > 140:
                    original_body = original_body[:137] + "..."

                # 合规脱敏处理
                body = self._apply_compliance(original_body, platform)

                results[platform] = SocialContent(
                    id=_generate_content_id(),
                    platform=platform,
                    title=parsed.get("title", f"今日股市速报"),
                    body=body,
                    tags=parsed.get("tags", ["股市速报", "A股"]),
                    image_urls=[],
                    source_analysis_id=None,
                    content_type="daily_report",
                    status="draft",
                    created_at=datetime.now().isoformat(),
                    original_content=original_body,
                )
            except Exception as e:
                logger.error(f"生成 {platform} 速报失败: {e}")

        return results

    # ------------------------------------------------------------------
    # 统一生成入口
    # ------------------------------------------------------------------

    async def generate_content(
        self, analysis: StockAnalysisResult, platform: str
    ) -> SocialContent:
        """根据平台类型生成对应格式的社交内容"""
        generators = {
            "xhs": self.generate_xhs_content,
            "weibo": self.generate_weibo_content,
            "xueqiu": self.generate_xueqiu_content,
            "zhihu": self.generate_zhihu_content,
        }
        generator = generators.get(platform)
        if not generator:
            raise ValueError(f"不支持的平台: {platform}，支持的平台: {list(generators.keys())}")

        content = await generator(analysis)

        # 持久化到数据库
        await self._persist_content(content)

        return content

    # ------------------------------------------------------------------
    # 发布功能
    # ------------------------------------------------------------------

    async def publish_to_xhs(self, content: SocialContent) -> Dict[str, Any]:
        """通过 XHS MCP 发布到小红书"""
        result = await self.xhs_publisher.publish_content(
            title=content.title,
            content=content.body,
            images=content.image_urls,
            tags=content.tags,
        )
        if result.get("success"):
            content.status = "published"
            content.published_at = datetime.now().isoformat()
            await self._update_content_status(content)
        return result

    async def publish_all_platforms(self, content: SocialContent) -> Dict[str, Dict]:
        """一键发布到全平台（当前 = 小红书）"""
        platform_publishers = {
            "xhs": self.publish_to_xhs,
        }
        results = {}
        for platform_id, publish_fn in platform_publishers.items():
            try:
                result = await publish_fn(content)
                results[platform_id] = {"status": "published", "result": result}
            except Exception as e:
                logger.error(f"发布到 {platform_id} 失败: {e}")
                results[platform_id] = {"status": "failed", "error": str(e)}
        return results

    def copy_to_clipboard(self, content: SocialContent) -> str:
        """将内容格式化为可复制文本（半自动方案）"""
        parts = []
        if content.title:
            parts.append(content.title)
            parts.append("")
        parts.append(content.body)
        if content.tags:
            parts.append("")
            parts.append(" ".join(f"#{tag}" for tag in content.tags))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # 数据库持久化
    # ------------------------------------------------------------------

    async def _persist_content(self, content: SocialContent):
        """将社交内容持久化到数据库"""
        try:
            from app.database import async_session_factory
            from app.models import SocialContentDB

            async with async_session_factory() as session:
                db_record = SocialContentDB(
                    id=content.id,
                    platform=content.platform,
                    content_type=content.content_type,
                    title=content.title,
                    body=content.body,
                    tags=json.dumps(content.tags, ensure_ascii=False),
                    image_urls=json.dumps(content.image_urls, ensure_ascii=False),
                    desensitization_level=content.desensitization_level,
                    original_content=content.original_content,
                    user_acknowledged_risk=content.user_acknowledged_risk,
                    status=content.status,
                    published_at=None,
                    source_analysis_id=content.source_analysis_id,
                    created_at=datetime.fromisoformat(content.created_at)
                    if content.created_at
                    else datetime.utcnow(),
                )
                session.add(db_record)
                await session.commit()
                logger.info(f"✓ 社交内容已持久化: {content.id} ({content.platform})")
        except Exception as e:
            logger.error(f"❌ 社交内容持久化失败: {e}")

    async def _update_content_status(self, content: SocialContent):
        """更新内容发布状态"""
        try:
            from sqlalchemy import update
            from app.database import async_session_factory
            from app.models import SocialContentDB

            async with async_session_factory() as session:
                stmt = (
                    update(SocialContentDB)
                    .where(SocialContentDB.id == content.id)
                    .values(
                        status=content.status,
                        published_at=datetime.fromisoformat(content.published_at)
                        if content.published_at
                        else None,
                    )
                )
                await session.execute(stmt)
                await session.commit()
        except Exception as e:
            logger.error(f"❌ 更新内容状态失败: {e}")

    # ------------------------------------------------------------------
    # 历史查询
    # ------------------------------------------------------------------

    async def get_history(
        self, limit: int = 20, offset: int = 0, platform: Optional[str] = None
    ) -> List[SocialContent]:
        """获取历史内容记录，支持分页和平台筛选"""
        try:
            from sqlalchemy import select
            from app.database import async_session_factory
            from app.models import SocialContentDB

            async with async_session_factory() as session:
                stmt = select(SocialContentDB).order_by(
                    SocialContentDB.created_at.desc()
                )
                if platform:
                    stmt = stmt.where(SocialContentDB.platform == platform)
                stmt = stmt.limit(limit).offset(offset)

                result = await session.execute(stmt)
                rows = result.scalars().all()
                return [self._db_to_schema(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ 查询内容历史失败: {e}")
            return []

    async def get_by_id(self, content_id: str) -> Optional[SocialContent]:
        """根据 ID 获取单条内容"""
        try:
            from sqlalchemy import select
            from app.database import async_session_factory
            from app.models import SocialContentDB

            async with async_session_factory() as session:
                stmt = select(SocialContentDB).where(SocialContentDB.id == content_id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row:
                    return self._db_to_schema(row)
                return None
        except Exception as e:
            logger.error(f"❌ 查询内容失败: {e}")
            return None

    @staticmethod
    def _db_to_schema(row) -> SocialContent:
        """将数据库行转换为 schema 对象"""
        tags = []
        if row.tags:
            try:
                tags = json.loads(row.tags)
            except Exception:
                tags = []

        image_urls = []
        if row.image_urls:
            try:
                image_urls = json.loads(row.image_urls)
            except Exception:
                image_urls = []

        return SocialContent(
            id=row.id,
            platform=row.platform,
            title=row.title or "",
            body=row.body or "",
            tags=tags,
            image_urls=image_urls,
            source_analysis_id=row.source_analysis_id,
            content_type=row.content_type,
            status=row.status or "draft",
            published_at=row.published_at.isoformat() if row.published_at else None,
            created_at=row.created_at.isoformat() if row.created_at else "",
            desensitization_level=row.desensitization_level or "medium",
            original_content=row.original_content,
            user_acknowledged_risk=row.user_acknowledged_risk or False,
        )


# ---------------------------------------------------------------------------
# 全局实例
# ---------------------------------------------------------------------------

social_content_generator = SocialContentGenerator()
