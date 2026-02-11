"""
股票行情推演服务
实现九步推演流程：情绪数据获取 → 资讯汇总 → 影响分析 → 多头激辩 → 空头激辩
→ 多空交锋 → 争议性结论 → 文案生成 → 配图生成

以 async generator 方式 yield StockAnalysisStep 事件，支持 SSE 流式输出。
推演结果缓存 60 分钟，并持久化到 SQLite 数据库。
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from app.llm import get_agent_llm
from app.schemas import StockAnalysisRequest, StockAnalysisResult, StockAnalysisStep
from app.services.stock_workflow_status import stock_workflow_status


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _extract_text(content: Any) -> str:
    """从 LLM 响应中提取纯文本（兼容 str / list[dict] 格式）"""
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


def _topic_cache_key(topic: str) -> str:
    """根据 topic 生成缓存 key"""
    h = hashlib.md5(topic.encode("utf-8")).hexdigest()[:12]
    return f"stock_analysis_{h}"


# ---------------------------------------------------------------------------
# Agent Prompts
# ---------------------------------------------------------------------------

NEWS_SUMMARY_PROMPT = """你是一名资深财经记者。
请根据用户提供的推演主题和关联资讯，提取核心事实并生成结构化摘要。
重点关注：涉及哪些股票/板块、关键事件、时间节点、市场影响方向。
{sentiment_hint}
请用中文输出简明扼要的事实摘要（300字以内）。"""

IMPACT_ANALYSIS_PROMPT = """你是一名资深股票分析师。
请根据以下资讯摘要和市场情绪数据，分析对相关股票/板块的潜在影响。
{sentiment_hint}
要求：
1. 明确指出利好/利空因素
2. 引用情绪数据佐证（如有）
3. 给出初步的影响判断
请用中文输出影响分析（500字以内）。"""

BULL_ARGUMENT_PROMPT = """你是一名坚定的多头分析师，你的立场是看多。
请基于以下资讯和分析，用激进、有说服力的语言论证为什么应该买入。
{sentiment_hint}
要求：
1. 立场坚定，语气自信甚至略带挑衅
2. 引用具体数据和历史类比
3. 如有情绪数据，用来佐证你的观点（如"当前情绪指数仅25，处于恐慌区间，正是别人恐惧我贪婪的时候"）
4. 不要给出任何看空的观点
请用中文输出多头激辩观点（500字以内）。"""

BEAR_ARGUMENT_PROMPT = """你是一名坚定的空头分析师，你的立场是看空。
请基于以下资讯和分析，用犀利、有冲击力的语言论证为什么应该远离。
{sentiment_hint}
要求：
1. 立场坚定，揭示风险，反驳多头论点
2. 引用具体数据揭示隐患
3. 如有情绪数据，用来佐证你的观点（如"情绪指数已达85，散户极度贪婪，历史上每次到这个位置都是见顶信号"）
4. 不要给出任何看多的观点
请用中文输出空头激辩观点（500字以内）。"""

DEBATE_PROMPT = """你是一名金融辩论主持人。
请根据以下多头和空头的观点，模拟双方的直接对话交锋。
这是第 {round_num} 轮交锋（共 {total_rounds} 轮），请逐步升级争议强度。

多头观点：
{bull_argument}

空头观点：
{bear_argument}

{prev_dialogue}

要求：
1. 以对话体呈现（多头："..."，空头："..."）
2. 每轮各方发言 2-3 段
3. 争议强度逐轮升级
4. 引用具体数据和逻辑反驳对方
请用中文输出本轮多空交锋对话。"""

CONCLUSION_PROMPT = """你是一名争议性财经评论员。
请根据以下多空交锋的完整过程，选择一个有争议性的立场（偏多或偏空），
用标题党风格输出一个能引发讨论的核心观点。

多头观点：{bull_argument}
空头观点：{bear_argument}
交锋对话：{debate_dialogue}
{sentiment_hint}

要求：
1. 不要给出"客观中立"的结论，必须选边站
2. 标题党风格，能引发讨论和争议
3. 附带简短的风险提示
4. 在输出末尾标注你的立场：STANCE: bull 或 STANCE: bear

请用中文输出争议性结论（300字以内）。"""

WRITER_PROMPT_STOCK = """你是一位深谙小红书流量密码的资深财经内容策划。
请基于以下行情推演结果，创作一篇争议性的股票分析笔记。

推演主题：{topic}
争议性结论：{conclusion}
多头核心观点：{bull_summary}
空头核心观点：{bear_summary}
{sentiment_hint}

【写作原则】
1. 标题要争议性十足，能引发讨论
2. 正文呈现多空双方核心论点
3. 融入情绪数据亮点（如有）
4. 结尾用互动引导收尾
5. 控制在 200-300 字
6. 禁止使用 **bold** 格式

【输出格式】
TITLE: [12-18字标题，含1个emoji]
CONTENT:
[正文内容]
#标签 #标签 #标签"""


# ---------------------------------------------------------------------------
# StockAnalysisService
# ---------------------------------------------------------------------------

class StockAnalysisService:
    """股票行情推演服务

    以 async generator 方式 yield StockAnalysisStep 事件，
    支持 SSE 流式输出九步推演流程。
    """

    def __init__(self):
        # 缓存服务（延迟导入避免循环依赖）
        self._cache_service = None
        # 配图生成服务
        self._image_service = None

    @property
    def cache_service(self):
        if self._cache_service is None:
            from app.services.hot_news_cache import hot_news_cache
            self._cache_service = hot_news_cache
        return self._cache_service

    @property
    def image_service(self):
        if self._image_service is None:
            from app.services.image_generator import image_generator_service
            self._image_service = image_generator_service
        return self._image_service

    # ------------------------------------------------------------------
    # 情绪数据获取（集成 SentimentAnalyzer）
    # ------------------------------------------------------------------

    async def _fetch_sentiment_context(self, topic: str) -> Optional[Dict[str, Any]]:
        """获取情绪数据，不可用时返回 None（降级模式）。

        Extracts a stock_code from the topic if possible, otherwise
        fetches the overall market sentiment context.
        """
        try:
            from app.services.sentiment_analyzer import SentimentAnalyzer

            analyzer = SentimentAnalyzer()
            # Try to extract a stock code from the topic (6-digit pattern)
            import re
            stock_code_match = re.search(r"\b(\d{6})\b", topic)
            stock_code = stock_code_match.group(1) if stock_code_match else None

            context = await analyzer.get_sentiment_context(stock_code)
            if context is None:
                return None

            # Convert SentimentContext pydantic model to dict for storage
            return context.model_dump()
        except Exception as e:
            logger.warning(f"情绪数据获取失败，降级为无情绪数据模式: {e}")
            return None

    def _build_sentiment_hint(self, sentiment_context: Optional[Dict]) -> str:
        """根据情绪数据构建 prompt 提示片段，包含综合指数和各分项得分。"""
        if sentiment_context is None:
            return ""
        try:
            index_value = sentiment_context.get("index_value", "N/A")
            label = sentiment_context.get("label", "未知")
            trend = sentiment_context.get("trend_direction", "stable")
            sample_count = sentiment_context.get("sample_count", 0)
            sub_scores = sentiment_context.get("sub_scores", {})

            trend_label = {"up": "上升", "down": "下降", "stable": "平稳"}.get(trend, "平稳")

            def _fmt(v):
                return f"{v:.1f}" if v is not None else "N/A"

            return (
                f"\n【当前散户情绪参考数据（混合数据源综合分析）】\n"
                f"- 综合情绪指数：{_fmt(index_value)}（{label}）\n"
                f"- 评论情绪分：{_fmt(sub_scores.get('comment'))}\n"
                f"- 百度投票看涨比例：{_fmt(sub_scores.get('baidu_vote'))}\n"
                f"- 新闻情绪分：{_fmt(sub_scores.get('news'))}\n"
                f"- 融资融券信号：{_fmt(sub_scores.get('margin'))}\n"
                f"- AKShare 聚合分：{_fmt(sub_scores.get('akshare'))}\n"
                f"- 趋势方向：{trend_label}\n"
                f"- 样本量：{sample_count}\n"
                f"请在分析中综合引用散户情绪状态和各分项数据。\n"
            )
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # LLM 调用封装
    # ------------------------------------------------------------------

    async def _call_llm(self, agent_name: str, system_prompt: str, user_content: str) -> str:
        """调用 LLM 并返回文本结果"""
        llm = get_agent_llm(agent_name)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]
        response = await llm.ainvoke(messages)
        return _extract_text(response.content)

    # ------------------------------------------------------------------
    # 缓存检查
    # ------------------------------------------------------------------

    def _check_cache(self, topic: str) -> Optional[StockAnalysisResult]:
        """检查推演结果缓存（60 分钟有效）"""
        cache_key = _topic_cache_key(topic)
        # 临时设置 60 分钟过期
        original_ttl = self.cache_service.cache_expiry_minutes
        self.cache_service.cache_expiry_minutes = 60
        cached = self.cache_service.get_cached_data(cache_key=cache_key)
        self.cache_service.cache_expiry_minutes = original_ttl
        if cached and "id" in cached:
            try:
                return StockAnalysisResult(**cached)
            except Exception:
                pass
        return None

    def _save_cache(self, result: StockAnalysisResult, topic: str):
        """保存推演结果到缓存"""
        cache_key = _topic_cache_key(topic)
        self.cache_service.save_to_cache(result.model_dump(), cache_key=cache_key)

    # ------------------------------------------------------------------
    # 数据库持久化
    # ------------------------------------------------------------------

    async def _persist_to_db(self, result: StockAnalysisResult):
        """将推演结果持久化到 SQLite 数据库"""
        try:
            from app.database import async_session_factory
            from app.models import StockAnalysisResultDB

            async with async_session_factory() as session:
                db_record = StockAnalysisResultDB(
                    id=result.id,
                    topic=result.news_titles[0] if result.news_titles else "",
                    news_titles=json.dumps(result.news_titles, ensure_ascii=False),
                    summary=result.summary,
                    impact_analysis=result.impact_analysis,
                    bull_argument=result.bull_argument,
                    bear_argument=result.bear_argument,
                    debate_dialogue=result.debate_dialogue,
                    controversial_conclusion=result.controversial_conclusion,
                    stance=result.stance,
                    risk_warning=result.risk_warning,
                    sentiment_context=json.dumps(result.sentiment_context, ensure_ascii=False)
                    if result.sentiment_context
                    else None,
                    cache_hit=result.cache_hit,
                    created_at=datetime.fromisoformat(result.created_at)
                    if result.created_at
                    else datetime.utcnow(),
                )
                session.add(db_record)
                await session.commit()
                logger.info(f"✓ 推演结果已持久化: {result.id}")
        except Exception as e:
            logger.error(f"❌ 推演结果持久化失败: {e}")

    # ------------------------------------------------------------------
    # 历史查询
    # ------------------------------------------------------------------

    async def get_history(self, limit: int = 20, offset: int = 0) -> List[StockAnalysisResult]:
        """获取历史推演记录，按时间倒序"""
        try:
            from sqlalchemy import select
            from app.database import async_session_factory
            from app.models import StockAnalysisResultDB

            async with async_session_factory() as session:
                stmt = (
                    select(StockAnalysisResultDB)
                    .order_by(StockAnalysisResultDB.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()
                return [self._db_to_schema(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ 查询历史记录失败: {e}")
            return []

    async def get_by_id(self, analysis_id: str) -> Optional[StockAnalysisResult]:
        """根据 ID 获取单条推演结果"""
        try:
            from sqlalchemy import select
            from app.database import async_session_factory
            from app.models import StockAnalysisResultDB

            async with async_session_factory() as session:
                stmt = select(StockAnalysisResultDB).where(
                    StockAnalysisResultDB.id == analysis_id
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row:
                    return self._db_to_schema(row)
                return None
        except Exception as e:
            logger.error(f"❌ 查询推演结果失败: {e}")
            return None

    @staticmethod
    def _db_to_schema(row) -> StockAnalysisResult:
        """将数据库行转换为 schema 对象"""
        news_titles = []
        if row.news_titles:
            try:
                news_titles = json.loads(row.news_titles)
            except Exception:
                news_titles = [row.news_titles]

        sentiment_ctx = None
        if row.sentiment_context:
            try:
                sentiment_ctx = json.loads(row.sentiment_context)
            except Exception:
                pass

        return StockAnalysisResult(
            id=row.id,
            news_titles=news_titles,
            summary=row.summary or "",
            impact_analysis=row.impact_analysis or "",
            bull_argument=row.bull_argument or "",
            bear_argument=row.bear_argument or "",
            debate_dialogue=row.debate_dialogue or "",
            controversial_conclusion=row.controversial_conclusion or "",
            stance=row.stance or "",
            risk_warning=row.risk_warning or "",
            sentiment_context=sentiment_ctx,
            created_at=row.created_at.isoformat() if row.created_at else "",
            cache_hit=row.cache_hit or False,
        )


    # ------------------------------------------------------------------
    # 核心推演流程（async generator，yield SSE 事件）
    # ------------------------------------------------------------------

    async def analyze(
        self, request: StockAnalysisRequest
    ) -> AsyncGenerator[StockAnalysisStep, None]:
        """执行九步行情推演，以 async generator 方式 yield StockAnalysisStep 事件。

        流程：
        0. 情绪数据获取
        1. 资讯汇总
        2. 影响分析
        3. 多头激辩
        4. 空头激辩
        5. 多空交锋（多轮）
        6. 争议性结论
        7. 文案生成
        8. 配图生成
        """
        topic = request.topic
        debate_rounds = max(1, min(request.debate_rounds or 2, 5))
        news_items = request.news_items or []

        # 检查缓存
        cached_result = self._check_cache(topic)
        if cached_result:
            logger.info(f"📦 推演结果命中缓存: {topic}")
            cached_result.cache_hit = True
            yield StockAnalysisStep(
                agent_name="cache",
                step_content="命中缓存，直接返回历史推演结果。",
                status="finished",
            )
            # 将完整结果作为最终事件 yield
            yield StockAnalysisStep(
                agent_name="result",
                step_content=cached_result.model_dump_json(),
                status="finished",
            )
            return

        # 生成唯一 ID
        analysis_id = str(uuid.uuid4())[:8] + "_" + datetime.now().strftime("%Y%m%d%H%M%S")

        # 准备资讯标题列表
        news_titles = [item.title for item in news_items] if news_items else [topic]
        news_context = ""
        if news_items:
            news_context = "\n".join(
                f"- [{item.source_name}] {item.title}: {item.summary[:150]}"
                for item in news_items[:10]
            )
        else:
            news_context = f"推演主题: {topic}"

        await stock_workflow_status.start_workflow(topic)

        try:
            # ============================================================
            # Step 0: 情绪数据获取
            # ============================================================
            await stock_workflow_status.update_step("sentiment_fetch", current_agent="情绪数据获取")
            yield StockAnalysisStep(
                agent_name="sentiment_fetch",
                step_content="正在获取市场情绪数据...",
                status="thinking",
            )

            sentiment_context = await self._fetch_sentiment_context(topic)
            sentiment_hint = self._build_sentiment_hint(sentiment_context)

            if sentiment_context:
                sentiment_msg = (
                    f"情绪数据获取成功：综合指数 {sentiment_context.get('index_value', 'N/A')}"
                    f"（{sentiment_context.get('label', '未知')}），"
                    f"趋势方向：{sentiment_context.get('trend_direction', 'stable')}，"
                    f"样本量：{sentiment_context.get('sample_count', 0)}"
                )
            else:
                sentiment_msg = "情绪数据暂不可用，将以无情绪数据模式进行推演。"

            yield StockAnalysisStep(
                agent_name="sentiment_fetch",
                step_content=sentiment_msg,
                status="finished",
            )

            # ============================================================
            # Step 1: 资讯汇总
            # ============================================================
            await stock_workflow_status.update_step("news_summary", current_agent="资讯汇总")
            yield StockAnalysisStep(
                agent_name="news_summary",
                step_content="正在汇总分析资讯...",
                status="thinking",
            )

            summary_prompt = NEWS_SUMMARY_PROMPT.format(sentiment_hint=sentiment_hint)
            summary = await self._call_llm(
                "analyst",
                summary_prompt,
                f"推演主题: {topic}\n\n关联资讯:\n{news_context}",
            )

            yield StockAnalysisStep(
                agent_name="news_summary",
                step_content=summary,
                status="finished",
            )

            # ============================================================
            # Step 2: 影响分析
            # ============================================================
            await stock_workflow_status.update_step("impact_analysis", current_agent="影响分析")
            yield StockAnalysisStep(
                agent_name="impact_analysis",
                step_content="正在分析市场影响...",
                status="thinking",
            )

            impact_prompt = IMPACT_ANALYSIS_PROMPT.format(sentiment_hint=sentiment_hint)
            impact_analysis = await self._call_llm(
                "analyst",
                impact_prompt,
                f"资讯摘要:\n{summary}\n\n原始主题: {topic}",
            )

            yield StockAnalysisStep(
                agent_name="impact_analysis",
                step_content=impact_analysis,
                status="finished",
            )

            # ============================================================
            # Step 3: 多头激辩
            # ============================================================
            await stock_workflow_status.update_step("bull_argument", current_agent="多头激辩")
            yield StockAnalysisStep(
                agent_name="bull_argument",
                step_content="多头分析师正在构建看多论点...",
                status="thinking",
            )

            bull_prompt = BULL_ARGUMENT_PROMPT.format(sentiment_hint=sentiment_hint)
            bull_argument = await self._call_llm(
                "debater",
                bull_prompt,
                f"主题: {topic}\n资讯摘要: {summary}\n影响分析: {impact_analysis}",
            )

            yield StockAnalysisStep(
                agent_name="bull_argument",
                step_content=bull_argument,
                status="finished",
            )

            # ============================================================
            # Step 4: 空头激辩
            # ============================================================
            await stock_workflow_status.update_step("bear_argument", current_agent="空头激辩")
            yield StockAnalysisStep(
                agent_name="bear_argument",
                step_content="空头分析师正在构建看空论点...",
                status="thinking",
            )

            bear_prompt = BEAR_ARGUMENT_PROMPT.format(sentiment_hint=sentiment_hint)
            bear_argument = await self._call_llm(
                "debater",
                bear_prompt,
                f"主题: {topic}\n资讯摘要: {summary}\n影响分析: {impact_analysis}\n多头观点: {bull_argument}",
            )

            yield StockAnalysisStep(
                agent_name="bear_argument",
                step_content=bear_argument,
                status="finished",
            )

            # ============================================================
            # Step 5: 多空交锋（多轮对话）
            # ============================================================
            await stock_workflow_status.update_step("debate", current_agent="多空交锋")

            debate_dialogue_parts: List[str] = []
            for round_num in range(1, debate_rounds + 1):
                yield StockAnalysisStep(
                    agent_name="debate",
                    step_content=f"第 {round_num}/{debate_rounds} 轮多空交锋进行中...",
                    status="thinking",
                )

                prev_dialogue = ""
                if debate_dialogue_parts:
                    prev_dialogue = f"前几轮交锋记录:\n{''.join(debate_dialogue_parts)}"

                debate_user_content = DEBATE_PROMPT.format(
                    round_num=round_num,
                    total_rounds=debate_rounds,
                    bull_argument=bull_argument,
                    bear_argument=bear_argument,
                    prev_dialogue=prev_dialogue,
                )

                round_dialogue = await self._call_llm(
                    "debater",
                    "你是一名金融辩论主持人，负责组织多空双方的直接交锋对话。",
                    debate_user_content,
                )

                debate_dialogue_parts.append(f"\n--- 第 {round_num} 轮 ---\n{round_dialogue}\n")

                yield StockAnalysisStep(
                    agent_name="debate",
                    step_content=f"【第 {round_num} 轮交锋】\n{round_dialogue}",
                    status="finished" if round_num == debate_rounds else "thinking",
                )

            debate_dialogue = "".join(debate_dialogue_parts)

            # ============================================================
            # Step 6: 争议性结论
            # ============================================================
            await stock_workflow_status.update_step("conclusion", current_agent="争议性结论")
            yield StockAnalysisStep(
                agent_name="conclusion",
                step_content="正在生成争议性结论...",
                status="thinking",
            )

            conclusion_content = CONCLUSION_PROMPT.format(
                bull_argument=bull_argument[:500],
                bear_argument=bear_argument[:500],
                debate_dialogue=debate_dialogue[:800],
                sentiment_hint=sentiment_hint,
            )
            conclusion_raw = await self._call_llm(
                "writer",
                "你是一名争议性财经评论员，擅长输出能引发讨论的观点。",
                conclusion_content,
            )

            # 解析立场
            stance = "bull"
            if "STANCE: bear" in conclusion_raw.lower() or "stance:bear" in conclusion_raw.lower():
                stance = "bear"
            # 清理 STANCE 标记
            controversial_conclusion = conclusion_raw
            for tag in ["STANCE: bull", "STANCE: bear", "STANCE:bull", "STANCE:bear",
                         "stance: bull", "stance: bear"]:
                controversial_conclusion = controversial_conclusion.replace(tag, "").strip()

            risk_warning = "以上内容仅为市场观点讨论，不构成任何投资建议。股市有风险，投资需谨慎。"

            yield StockAnalysisStep(
                agent_name="conclusion",
                step_content=controversial_conclusion,
                status="finished",
            )

            # ============================================================
            # Step 7: 文案生成
            # ============================================================
            await stock_workflow_status.update_step("writer", current_agent="文案生成")
            yield StockAnalysisStep(
                agent_name="writer",
                step_content="正在生成社交平台文案...",
                status="thinking",
            )

            writer_content = WRITER_PROMPT_STOCK.format(
                topic=topic,
                conclusion=controversial_conclusion[:300],
                bull_summary=bull_argument[:200],
                bear_summary=bear_argument[:200],
                sentiment_hint=sentiment_hint,
            )
            final_copy = await self._call_llm(
                "writer",
                "你是一位深谙小红书流量密码的资深财经内容策划。",
                writer_content,
            )

            yield StockAnalysisStep(
                agent_name="writer",
                step_content=final_copy,
                status="finished",
            )

            # ============================================================
            # Step 8: 配图生成
            # ============================================================
            await stock_workflow_status.update_step("image_generator", current_agent="配图生成")
            yield StockAnalysisStep(
                agent_name="image_generator",
                step_content="正在生成金融风格配图...",
                status="thinking",
            )

            image_urls: List[str] = []
            try:
                image_urls = await self.image_service.generate_images(
                    final_copy, insight=impact_analysis, image_count=2
                )
            except Exception as e:
                logger.warning(f"配图生成失败: {e}")

            image_msg = f"已生成 {len(image_urls)} 张配图。" if image_urls else "配图生成跳过或失败。"
            yield StockAnalysisStep(
                agent_name="image_generator",
                step_content=image_msg,
                status="finished",
            )

            # ============================================================
            # 组装最终结果
            # ============================================================
            result = StockAnalysisResult(
                id=analysis_id,
                news_titles=news_titles,
                summary=summary,
                impact_analysis=impact_analysis,
                bull_argument=bull_argument,
                bear_argument=bear_argument,
                debate_dialogue=debate_dialogue,
                controversial_conclusion=controversial_conclusion,
                stance=stance,
                risk_warning=risk_warning,
                sentiment_context=sentiment_context,
                created_at=datetime.now().isoformat(),
                cache_hit=False,
            )

            # 缓存 + 持久化
            self._save_cache(result, topic)
            await self._persist_to_db(result)

            await stock_workflow_status.finish_workflow()

            # yield 最终结果
            yield StockAnalysisStep(
                agent_name="result",
                step_content=result.model_dump_json(),
                status="finished",
            )

        except Exception as e:
            logger.error(f"❌ 行情推演失败: {e}")
            await stock_workflow_status.finish_workflow()
            yield StockAnalysisStep(
                agent_name="error",
                step_content=f"推演过程出错: {str(e)}",
                status="error",
            )


# ---------------------------------------------------------------------------
# 全局实例
# ---------------------------------------------------------------------------

stock_analysis_service = StockAnalysisService()
