import os
import re
from datetime import datetime
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from app.llm import get_agent_llm
from app.config import settings

from app.services.crawler_router_service import crawler_router_service
from app.services.image_generator import image_generator_service
from app.services.xiaohongshu_publisher import xiaohongshu_publisher


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_ASCII_LETTER_RE = re.compile(r"[A-Za-z]")

# --- Workflow Content Safety (political redaction / blocking) ---
# This is a backend-only safety layer, controlled by settings.WORKFLOW_CONTENT_SAFETY.
_POLITICAL_RE = re.compile(
    r"("
    # CN
    r"习近平|中共|共产党|国安|外交部|国务院|人大|政协|政府|政党|"
    r"总统|总理|首相|国会|参议院|众议院|白宫|克里姆林宫|联合国|北约|"
    r"选举|大选|政变|制裁|战争|袭击|空袭|导弹|军队|入侵|"
    r"台湾|台独|香港|乌克兰|俄罗斯|以色列|巴勒斯坦|哈马斯|"
    r"特朗普|拜登|普京|泽连斯基|内塔尼亚胡|马杜罗|"
    # EN
    r"Trump|Biden|Putin|Zelensky|Maduro|Netanyahu|"
    r"White\s+House|Kremlin|United\s+Nations|UN\b|NATO\b|"
    r"election|president|prime\s+minister|government|parliament|congress|senate|"
    r"sanction|strike|airstrike|missile|troops|invasion|war"
    r")",
    flags=re.IGNORECASE,
)


def _safety_cfg() -> Dict[str, Any]:
    cfg = getattr(settings, "WORKFLOW_CONTENT_SAFETY", None) or {}
    return {
        "redact_politics": bool(cfg.get("redact_politics", True)),
        "block_political_topics": bool(cfg.get("block_political_topics", True)),
        "redaction_token": str(cfg.get("redaction_token", "【已脱敏】")),
    }


def _looks_political(text: str) -> bool:
    if not text:
        return False
    return bool(_POLITICAL_RE.search(text))


def _redact_political(text: str) -> str:
    """Best-effort redaction to remove political signals from text."""
    if not text:
        return text
    cfg = _safety_cfg()
    if not cfg["redact_politics"]:
        return text
    token = cfg["redaction_token"]

    matches = list(_POLITICAL_RE.finditer(text))
    # If heavily political, replace whole content to avoid leaking signals via context.
    if len(matches) >= 6:
        return "（内容涉及敏感政治话题，已按后台安全策略隐藏）"
    return _POLITICAL_RE.sub(token, text)


def _with_safety_instruction(base_prompt: str) -> str:
    cfg = _safety_cfg()
    if not cfg["redact_politics"]:
        return base_prompt
    return (
        base_prompt
        + "\n\n"
        + "【安全要求】输出中不得出现政治敏感信号（人物/国家机构/战争选举等具体指称）。"
        + "如不可避免，请使用抽象替代（如“某国”“某政府部门”“某领导人”），避免点名与敏感词。"
    )


def _contains_cjk(text: str) -> bool:
    return bool(text and _CJK_RE.search(text))


def _contains_ascii_letters(text: str) -> bool:
    return bool(text and _ASCII_LETTER_RE.search(text))


async def _translate_topic_to_english_search_query(topic: str) -> Optional[str]:
    """Translate a Chinese topic into concise English search keywords.

    Best-effort: returns None if translation fails or looks invalid.
    """
    if not topic:
        return None

    translator_llm = None
    try:
        # Use a dedicated translator/query-builder agent for clearer separation of concerns.
        translator_llm = get_agent_llm("translator")
    except Exception:
        translator_llm = None

    if translator_llm is None:
        return None

    prompt = (
        "你是一个专业的搜索关键词翻译引擎，专门为英文网站（如Hacker News、Reddit）生成搜索关键词。\n"
        "你的任务是将中文话题转换为适合英文网站搜索的关键词短语。\n\n"
        "**核心要求**：\n"
        "- 只输出英文关键词短语，不要任何解释、前缀或标记\n"
        "- 提取核心实体（人名、地名、组织名、产品名等专有名词）和关键动作词\n"
        "- 保留所有专有名词的原始英文拼写（如：Trump, Venezuela, Maduro, OpenAI, Tesla等）\n"
        "- 关键词数量控制在3-8个词之间，优先保留最重要的实体和动作\n"
        "- 用空格分隔词，不要换行，不要使用引号或特殊符号\n\n"
        "**翻译策略**：\n"
        "- 如果话题包含人名，直接使用英文原名（如：特朗普→Trump，马杜罗→Maduro）\n"
        "- 如果话题包含地名，使用标准英文地名（如：委内瑞拉→Venezuela）\n"
        "- 提取核心动作词（如：capture, claim, say, announce, launch等）\n"
        "- 去除冗余的修饰词和连接词，只保留最核心的搜索关键词\n\n"
        "**示例**：\n"
        "- 输入：\"特朗普声称捕获委内瑞拉总统\"\n"
        "- 输出：Trump Venezuela Maduro capture\n"
        "- 输入：\"OpenAI发布新模型\"\n"
        "- 输出：OpenAI new model release\n"
        "- 输入：\"特斯拉股价上涨\"\n"
        "- 输出：Tesla stock price\n"
    )

    try:
        resp = await translator_llm.ainvoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(content=topic),
            ]
        )
        english = extract_text_content(getattr(resp, "content", "")).strip()
        english = re.sub(r"\s+", " ", english).strip()
        english = re.sub(r"(?i)^(english|translation)\s*:\s*", "", english).strip()

        if not english:
            return None
        # If it still contains Chinese, treat as failed.
        if _contains_cjk(english):
            return None
        # Basic sanity: must contain at least one ASCII letter.
        if not _contains_ascii_letters(english):
            return None

        # Keep it reasonably short for search queries.
        if len(english) > 200:
            english = english[:200].rsplit(" ", 1)[0].strip() or english[:200]
        return english
    except Exception:
        return None

# --- Helper Function ---
def extract_text_content(content: Any) -> str:
    """Extract clean text content from LLM response which might be a list of dicts."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Extract 'text' field if available, ignoring 'extras'
                if "text" in item:
                    text_parts.append(item["text"])
            elif isinstance(item, str):
                text_parts.append(item)
            else:
                # Fallback for other types, but try to avoid raw dict stringification if possible
                text_parts.append(str(item))
        return "\n".join(text_parts)
    return str(content)

# --- 1. State Definition ---
class GraphState(TypedDict):
    urls: List[str]
    topic: str
    platforms: List[str]  # Platforms to crawl
    debate_rounds: int  # Number of debate rounds (1-5)
    crawler_data: List[Dict[str, Any]]  # Standardized crawled data
    platform_data: Dict[str, List[Dict[str, Any]]]  # Data grouped by platform
    news_content: str
    initial_analysis: str
    critique: Optional[str]
    revision_count: int
    final_copy: str
    image_urls: List[str]
    output_file: Optional[str]
    messages: List[str] # Keep for SSE compatibility
    debate_history: List[str] # Track the debate process
    # Safety control (backend-only)
    safety_blocked: bool
    safety_reason: Optional[str]
    # Xiaohongshu Publish
    xhs_publish_enabled: bool # Whether to auto-publish
    xhs_publish_result: Optional[Dict[str, Any]]

# --- 2. LLM Setup ---
# LLMs are now retrieved via get_agent_llm() inside nodes or globally if preferred.
# We will instantiate them inside nodes to allow dynamic config changes if needed,
# or just use the factory here.

# --- 3. Prompts ---
REPORTER_PROMPT = """
你是一名资深新闻记者。
你的任务是阅读提供的新闻内容或社交媒体数据，并提取核心事实。
重点关注：谁（Who）、什么（What）、何时（When）、何地（Where）、为什么（Why）。
请用**中文**输出事实事件的简明摘要。
"""

ANALYST_PROMPT = """
你是一名舆论分析师。
你的任务是分析提供的新闻事实。
特别关注国内（中国）和国外媒体之间的叙事差异。
识别立场、情绪和任何隐藏的议程。
请一步步思考，并用**中文**输出你的分析。

重要提示：如果你收到反驳意见，请评估其是否与原始新闻主题相关。
如果反驳离题（产生幻觉），请忽略它并坚持原始事实。

**输出格式要求（必须严格遵守）**：
你的输出必须包含以下三个标记，每个标记占一行：
INSIGHT: [100字左右的深度洞察，分析事件背后的社会焦虑、群体心理或结构性矛盾]
TITLE: [4-8字的吸睛主标题，用于数据海报]
SUB: [8-12字的补充副标题，用于数据海报]

示例：
INSIGHT: 这一事件反映了当前社会对信息透明度的普遍焦虑，以及公众对权威机构公信力的质疑。背后是信息不对称导致的信任危机。
TITLE: 信息透明危机
SUB: 公信力重建的紧迫性
"""

DEBATER_PROMPT = """
你是一名魔鬼代言人（反对派）。
你的任务是严格基于提供的**主题**和**新闻事实**来反驳分析师的观点。

你的目标是挑战分析师，迫使他们进行更深层次的思考。即使分析看起来不错，也要尝试从以下角度寻找突破口：
1. **逻辑漏洞**：是否存在过度推断、因果倒置或幸存者偏差？
2. **视角缺失**：是否忽略了某些利益相关者的声音？是否只关注了宏观叙事而忽略了微观个体？
3. **证据强度**：分析是否过度依赖某些可能存在偏见的来源？
4. **语境检查**：确保分析实际上与提供的主题相符。

裁决规则：
- 只有当分析已经极其完美、无懈可击，且你实在找不到任何可以改进的地方时，才回复 "PASS"。
- 在前几轮辩论中，你应该尽可能地提出建设性的批评，而不是轻易放行。
- 你的反驳必须使用**中文**，且言辞犀利但基于事实。
"""

WRITER_PROMPT = """
你是一位书写小红书爆款文案的专家，精通小红书爆款文案书写格式和要求，熟悉热点词汇，善于抓住流量密码，十分擅长写作。

你的任务是将最终分析转化为一篇病毒式传播的小红书爆款帖子。

**核心要求**：
- 使用接地气的写作风格撰写评论文章
- 禁止使用```首先、其次、然而、总的来说、最后```这些副词
- 每句话尽量口语化、简短
- 文章总篇幅控制在200字左右
# - 大量使用表情符号 🌟✨
- 关注"真相揭秘"或"幕后"角度
- 请用**中文**撰写

**标题要求（必须严格遵守）**：
1. **字数限制**：**务必控制在 20 字以内**（包含标点和Emoji），否则无法发布！
2. 善于使用标题吸引人，制造反差或悬念
3. 使用爆款关键词（如：真相、内幕、竟然、居然、没想到等）
4. 了解小红书平台的标题特性（短小精悍、情绪化）
5. 标题含适当的emoji表情（1-2个即可，不要过多导致超长）
6. 标题要能抓住眼球，让人忍不住点开

**正文要求**：
1. **写作风格**：接地气、口语化、亲切自然，像和朋友聊天一样
2. **写作开篇方法**：用疑问句、感叹句或直接切入主题，快速抓住注意力
3. **文本结构**：分段明确，每段2-3句话，使用emoji表情增强表现力
4. **互动引导方法**：在文中适当使用"你们觉得呢？"、"有没有同感的？"等互动语句
5. **小技巧**：使用爆炸词（如：绝了、太绝了、真的、真的假的、天哪等）增强情绪
6. **SEO关键词**：从生成的内容中抽取3~6个SEO关键词，生成#标签放在文章最后
7. **禁止使用**：```首先、其次、然而、总的来说、最后```这些副词
8. **字数控制**：总字数控制在 800 字以内

**输出格式要求（必须严格遵守）**：
你的输出必须包含以下两个标记，每个标记占一行：
TITLE: [20字以内的标题]
CONTENT: [正文内容，分段，口语化，每段含emoji，文末加3-6个#标签]

注意：你的输出应该是最终结果，禁止在输出中包含"标题"、"正文"、"标签"这些词本身。

示例：
TITLE: 🔥 真相来了！这件事背后竟然...
CONTENT: 
姐妹们，今天要聊一个超级重要的话题！💡

最近大家都在讨论XXX，但是真相到底是什么？🤔

让我来给大家扒一扒...真的绝了！✨

#真相 #热点 #深度分析 #内幕 #爆料
"""

# --- 4. Node Functions ---

async def crawler_agent_node(state: GraphState):
    """Crawler Agent: Crawls multiple platforms for the given topic"""
    print("--- CRAWLER AGENT ---")
    topic = state["topic"]
    platforms = state.get("platforms", [])

    # Backend-only safety gate: block political topics early to avoid generating political signals.
    cfg = _safety_cfg()
    if cfg["block_political_topics"] and _looks_political(topic):
        safe_msg = "安全模式已开启：检测到敏感政治话题，工作流已自动停止生成内容。"
        print(f"[SAFETY] Blocked political topic: {topic!r}")
        return {
            "crawler_data": [],
            "platform_data": {},
            "news_content": "（内容已按安全策略隐藏）",
            "initial_analysis": "（内容已按安全策略隐藏）",
            "final_copy": "TITLE: 内容已隐藏\nCONTENT: 该话题涉及敏感政治内容，已按后台安全策略停止生成。",
            "image_urls": [],
            "messages": [safe_msg],
            "debate_history": [],
            "safety_blocked": True,
            "safety_reason": "politics",
        }
    
    print(f"[CRAWLER] 接收到的平台参数: {platforms} (类型: {type(platforms)})")
    
    # If no platforms specified, use all supported platforms
    if not platforms:
        print("[CRAWLER] 未指定平台，使用所有支持的平台")
        platforms = ["xhs", "dy", "bili", "wb", "zhihu", "tieba", "ks"]
    else:
        print(f"[CRAWLER] 使用用户选择的平台: {platforms}")
    
    # Normalize + filter out invalid platforms
    valid_platforms = []
    invalid_platforms = []
    for p in platforms:
        normalized = crawler_router_service.normalize_platform(p)
        if normalized in crawler_router_service.supported_platforms:
            valid_platforms.append(normalized)
        else:
            invalid_platforms.append(p)
    if invalid_platforms:
        print(f"[CRAWLER] 这些平台不支持/被过滤: {invalid_platforms}")
    if not valid_platforms:
        print(f"[CRAWLER] 警告: 所有平台都被过滤，使用默认平台")
        valid_platforms = ["xhs", "dy", "bili"]  # Default to most common platforms

    # If user topic is Chinese-only and foreign platforms are selected,
    # translate once and use the English query for foreign crawlers.
    foreign_platforms = {"hn", "reddit"}
    needs_foreign_translation = (
        any(p in foreign_platforms for p in valid_platforms)
        and _contains_cjk(topic)
        and not _contains_ascii_letters(topic)
    )
    foreign_topic = topic
    if needs_foreign_translation:
        translated = await _translate_topic_to_english_search_query(topic)
        if translated:
            foreign_topic = translated
            print(f"[CRAWLER] 检测到中文话题，已翻译用于外网平台检索: {foreign_topic}")
        else:
            print("[CRAWLER] 检测到中文话题，但翻译失败，将使用原话题尝试外网检索")
    
    print(f"[CRAWLER] Crawling topic '{topic}' on platforms: {valid_platforms}")
    print(f"[模式] 使用串行模式爬取，避免配置冲突")
    
    # Import workflow_status to update current platform
    from app.services.workflow_status import workflow_status
    
    # Crawl platforms serially to avoid config conflicts
    # Note: Will be upgraded to Agent architecture in the future
    try:
        # 由于是串行执行，我们可以逐个爬取并更新状态
        platform_data = {}
        total_platforms = len(valid_platforms)
        
        for idx, platform in enumerate(valid_platforms):
            # 更新当前爬取的平台
            platform_name_map = {
                "wb": "微博",
                "bili": "B站",
                "xhs": "小红书",
                "dy": "抖音",
                "ks": "快手",
                "tieba": "贴吧",
                "zhihu": "知乎",
                "hn": "Hacker News",
                "reddit": "Reddit",
            }
            platform_display = platform_name_map.get(platform, platform)
            await workflow_status.update_step("crawler_agent", current_platform=platform_display)
            print(f"[CRAWLER] 正在爬取平台: {platform_display} ({idx+1}/{total_platforms})")
            
            # 爬取单个平台
            try:
                platform_keywords = foreign_topic if platform in foreign_platforms else topic
                items = await crawler_router_service.crawl_platform(
                    platform=platform,
                    keywords=platform_keywords,
                    max_items=15,
                    timeout=180,
                )
                platform_data[platform] = items
                print(f"[CRAWLER] 平台 {platform_display} 爬取完成，获得 {len(items)} 条数据")
            except Exception as e:
                print(f"[警告] 平台 {platform_display} 爬取出错: {str(e)}")
                platform_data[platform] = []
        
        # 爬取完成后，清空当前平台信息
        await workflow_status.update_step("crawler_agent", current_platform=None)
        
        # Flatten all platform data into single list
        all_data = []
        for platform, items in platform_data.items():
            all_data.extend(items)
        
        # Remove duplicates based on content_id
        seen_ids = set()
        unique_data = []
        for item in all_data:
            content_id = item.get("content_id", "")
            if content_id and content_id not in seen_ids:
                seen_ids.add(content_id)
                unique_data.append(item)
        
        msg = f"爬虫完成：从 {len(platform_data)} 个平台共获取 {len(unique_data)} 条去重数据。"
        if not unique_data:
            msg = f"爬虫完成：话题『{topic}』未获取到数据。"
        
        print(f"[SUCCESS] Crawler completed: {len(unique_data)} items from {len(platform_data)} platforms")
        
        return {
            "crawler_data": unique_data,
            "platform_data": platform_data,
            "messages": [_redact_political(msg)]
        }
        
    except Exception as e:
        error_msg = f"Crawler Agent: Error during crawling - {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "crawler_data": [],
            "platform_data": {},
            "messages": [error_msg]
        }

async def reporter_node(state: GraphState):
    print("--- REPORTER ---")
    if state.get("safety_blocked"):
        return {
            "news_content": "（内容已按安全策略隐藏）",
            "messages": ["Reporter: （内容已按安全策略隐藏）"],
        }
    topic = state["topic"]
    crawler_data = state.get("crawler_data", [])
    platform_data = state.get("platform_data", {})
    urls = state.get("urls", [])
    llm = get_agent_llm("reporter")
    
    content_text = ""
    if crawler_data:
        # Format crawler data with platform information
        items_text = []
        # Use top 20 items from all platforms to get diverse perspectives
        for item in crawler_data[:20]:
            platform = item.get("platform", "unknown")
            title = item.get("title", "")
            content = item.get("content", "")
            author = item.get("author", {}).get("nickname", "Unknown")
            interactions = item.get("interactions", {})
            
            item_text = f"[平台: {platform}] 作者: {author}\n标题: {title}\n内容: {content}\n"
            item_text += f"互动数据: 点赞{interactions.get('liked_count', 0)}, "
            item_text += f"评论{interactions.get('comment_count', 0)}, "
            item_text += f"分享{interactions.get('share_count', 0)}\n"
            items_text.append(item_text)
        
        content_text = "\n---\n".join(items_text)
        
        # Add platform summary
        platform_summary = ", ".join([f"{p}({len(platform_data.get(p, []))}条)" for p in platform_data.keys()])
        source_info = f"多平台社交媒体数据 ({platform_summary})"
    elif urls:
        content_text = f"URLs provided: {urls}"
        source_info = "Provided URLs"
    else:
        content_text = "No content provided. Please simulate based on topic."
        source_info = "Simulation"

    messages = [
        SystemMessage(content=_with_safety_instruction(REPORTER_PROMPT)),
        HumanMessage(
            content=f"主题: {_redact_political(topic)}. 来源: {source_info}.\n\n内容:\n{content_text}\n\n请总结核心事实。"
        ),
    ]
    response = await llm.ainvoke(messages)
    content = _redact_political(extract_text_content(response.content))
    return {
        "news_content": content,
        "messages": [f"Reporter: {content}"]
    }

async def analyst_node(state: GraphState):
    print("--- ANALYST ---")
    if state.get("safety_blocked"):
        content = "（内容已按安全策略隐藏）"
        history = state.get("debate_history", [])
        history.append(f"### Analyst\n{content}\n")
        return {
            "initial_analysis": content,
            "messages": [f"Analyst: {content}"],
            "debate_history": history,
        }
    news_content = state["news_content"]
    critique = state.get("critique")
    llm = get_agent_llm("analyst")
    
    prompt = f"新闻事实: {news_content}"
    if critique:
        prompt += f"\n\n需要解决的反对意见: {critique}"
    
    # Calculate current round number (0-based, but display as 1-based)
    current_revision_count = state.get("revision_count", 0)
    if critique:
        # If there's a critique, this is a new round, so increment
        current_revision_count += 1
    # If no critique, this is the first round, so revision_count stays 0
        
    messages = [
        SystemMessage(content=_with_safety_instruction(ANALYST_PROMPT)),
        HumanMessage(content=_redact_political(prompt)),
    ]
    response = await llm.ainvoke(messages)
    content = _redact_political(extract_text_content(response.content))
    
    # Update history
    history = state.get("debate_history", [])
    history.append(f"### Analyst (Round {current_revision_count + 1})\n{content}\n")
    
    return {
        "initial_analysis": content,
        "revision_count": current_revision_count,
        "messages": [f"Analyst: {content}"],
        "debate_history": history
    }

async def debater_node(state: GraphState):
    print("--- DEBATER ---")
    if state.get("safety_blocked"):
        content = "（内容已按安全策略隐藏）"
        history = state.get("debate_history", [])
        history.append(f"### Debater\n{content}\n")
        return {
            "critique": content,
            "messages": [f"Debater: {content}"],
            "debate_history": history,
        }
    analysis = state["initial_analysis"]
    topic = state["topic"]
    news_content = state["news_content"]
    revision_count = state.get("revision_count", 0)
    debate_rounds = state.get("debate_rounds", settings.DEBATE_MAX_ROUNDS)
    llm = get_agent_llm("debater")
    
    prompt_suffix = ""
    if revision_count + 1 < debate_rounds:
        prompt_suffix = f"\n\n当前是第 {revision_count + 1} 轮辩论（目标总轮数: {debate_rounds}）。请尽可能提出尖锐的改进建议，除非分析已经完美到无可挑剔，否则不要回复 PASS。"
    else:
        prompt_suffix = f"\n\n当前是最后一轮辩论。如果分析已经足够好，可以回复 PASS。"

    messages = [
        SystemMessage(content=_with_safety_instruction(DEBATER_PROMPT)),
        HumanMessage(
            content=_redact_political(
                f"主题: {topic}\n\n新闻事实: {news_content}\n\n分析师观点: {analysis}{prompt_suffix}\n\n请根据事实审查该分析。"
            )
        ),
    ]
    response = await llm.ainvoke(messages)
    content = _redact_political(extract_text_content(response.content))
    
    # Update history
    history = state.get("debate_history", [])
    history.append(f"### Debater (Critique Round {revision_count + 1})\n{content}\n")
    
    return {
        "critique": content,
        "messages": [f"Debater: {content}"],
        "debate_history": history
    }

async def writer_node(state: GraphState):
    print("--- WRITER ---")
    if state.get("safety_blocked"):
        content = "TITLE: 内容已隐藏\nCONTENT: 该话题涉及敏感政治内容，已按后台安全策略停止生成。"
        return {
            "final_copy": content,
            "output_file": None,
            "messages": [f"Writer: {content}"],
        }
    analysis = state["initial_analysis"]
    topic = state["topic"]
    llm = get_agent_llm("writer")
    
    messages = [
        SystemMessage(content=_with_safety_instruction(WRITER_PROMPT)),
        HumanMessage(content=_redact_political(f"请将此分析转化为小红书帖子：\n{analysis}")),
    ]
    response = await llm.ainvoke(messages)
    content = _redact_political(extract_text_content(response.content))
    
    # Save to Markdown file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Sanitize topic for filename
    safe_topic = re.sub(r'[\\/*?:"<>|]', "", _redact_political(topic))[:20]
    filename = f"{timestamp}_{safe_topic}.md"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    
    debate_history = "\n".join(state.get("debate_history", []))
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {_redact_political(topic)}\n\n")
        f.write("## 最终文案\n\n")
        f.write(content)
        f.write("\n\n---\n\n")
        f.write("## 辩论过程记录\n\n")
        f.write(debate_history)
        
    return {
        "final_copy": content,
        "output_file": file_path,
        "messages": [f"Writer: {content}"]
    }

async def image_generator_node(state: GraphState):
    print("--- IMAGE GENERATOR ---")
    if state.get("safety_blocked"):
        return {
            "image_urls": [],
            "messages": ["Image Generator: skipped by safety policy."],
        }
    final_copy = state["final_copy"]
    output_file = state.get("output_file")
    
    # Update status
    from app.services.workflow_status import workflow_status
    await workflow_status.update_step("image_generator")
    
    image_urls = await image_generator_service.generate_images(final_copy)
    
    if output_file and os.path.exists(output_file) and image_urls:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n\n## 生成的配图\n\n")
            for idx, url in enumerate(image_urls):
                f.write(f"![图片{idx+1}]({url})\n\n")
    
    return {
        "image_urls": image_urls,
        "messages": [f"Image Generator: Generated {len(image_urls)} images."]
    }

async def xiaohongshu_publisher_node(state: GraphState):
    print("--- XHS PUBLISHER ---")
    
    # Check if enabled in state or global config (for now, rely on manual button or future auto-publish flag)
    # The requirement was "call XHS MCP directly after generation", so we add the capability.
    # We check settings first.
    auto_publish = settings.XHS_MCP_CONFIG.get("auto_publish", False)
    state_enabled = state.get("xhs_publish_enabled", False)
    
    if not (auto_publish or state_enabled):
        print("[XHS] Auto-publish disabled, skipping.")
        return {
            "xhs_publish_result": None,
            "messages": ["XHS Publisher: Skipped (auto-publish disabled)."]
        }

    if state.get("safety_blocked"):
        return {
            "xhs_publish_result": None,
            "messages": ["XHS Publisher: Skipped (safety blocked)."]
        }
        
    final_copy = state.get("final_copy", "")
    image_urls = state.get("image_urls", [])
    
    if not final_copy or not image_urls:
        print("[XHS] Missing content or images, skipping.")
        return {
            "xhs_publish_result": {"success": False, "error": "Missing content or images"},
            "messages": ["XHS Publisher: Skipped (missing content/images)."]
        }
        
    # Extract title and content from final_copy
    # Expected format:
    # TITLE: [title]
    # CONTENT: [content]
    
    title = ""
    content = ""
    
    # Simple parsing logic
    lines = final_copy.split('\n')
    is_content = False
    content_lines = []
    
    for line in lines:
        if line.strip().startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.strip().startswith("CONTENT:"):
            content_lines.append(line.replace("CONTENT:", "").strip())
            is_content = True
        elif is_content:
            content_lines.append(line)
            
    content = "\n".join(content_lines).strip()
    
    # Fallback parsing if structure is lost
    if not title:
        title = state["topic"]
    if not content:
        content = final_copy
        
    print(f"[XHS] Publishing: {title} with {len(image_urls)} images")
    
    # Check MCP status first
    status = await xiaohongshu_publisher.get_status()
    if not status["mcp_available"] or not status["login_status"]:
        msg = f"XHS Publisher: Failed - {status['message']}"
        print(f"[XHS] {msg}")
        return {
            "xhs_publish_result": {"success": False, "error": status['message']},
            "messages": [msg]
        }

    # Publish
    result = await xiaohongshu_publisher.publish_content(
        title=title,
        content=content,
        images=image_urls
    )
    
    msg = f"XHS Publisher: {result.get('message', 'Unknown status')}"
    if result.get("success"):
        print("[XHS] Publish success!")
    else:
        print(f"[XHS] Publish failed: {result.get('error')}")
        
    return {
        "xhs_publish_result": result,
        "messages": [msg]
    }

# --- 5. Conditional Logic ---

def should_continue(state: GraphState):
    critique = state.get("critique", "")
    revision_count = state.get("revision_count", 0)
    debate_rounds = state.get("debate_rounds", settings.DEBATE_MAX_ROUNDS)
    
    # Ensure critique is a string before calling upper()
    if isinstance(critique, list):
        critique = str(critique)
    elif critique is None:
        critique = ""
    
    # Check if we should stop: PASS verdict or reached max rounds
    # Note: revision_count is 0-based, so we check >= debate_rounds
    # If debate_rounds=2, we allow rounds 0,1 (2 rounds total)
    max_rounds = min(debate_rounds, settings.DEBATE_MAX_ROUNDS)  # 取两者较小值
    
    # 更精确的 PASS 检查：通常 PASS 响应会比较短
    is_pass = "PASS" in critique.upper()
    if is_pass and len(critique.strip()) > 100:
        # 如果响应很长，可能只是正文中提到了 pass 这个词，而不是真正的跳过
        if not (critique.strip().upper().startswith("PASS") or critique.strip().upper().endswith("PASS")):
            is_pass = False

    if is_pass or revision_count >= max_rounds:
        if revision_count >= max_rounds:
            print(f"[INFO] 已达到最大辩论轮数 ({max_rounds} 轮)，停止辩论")
        else:
            print(f"[INFO] Debater 给出 PASS，停止辩论")
        return "writer"
    
    print(f"[INFO] 继续辩论: 第 {revision_count + 1} 轮完成，目标 {max_rounds} 轮")
    return "analyst"

# --- 6. Graph Construction ---

workflow = StateGraph(GraphState)

workflow.add_node("crawler_agent", crawler_agent_node)
workflow.add_node("reporter", reporter_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("debater", debater_node)
workflow.add_node("writer", writer_node)
workflow.add_node("image_generator", image_generator_node)
workflow.add_node("xhs_publisher", xiaohongshu_publisher_node)

workflow.set_entry_point("crawler_agent")

workflow.add_edge("crawler_agent", "reporter")
workflow.add_edge("reporter", "analyst")
workflow.add_edge("analyst", "debater")

workflow.add_conditional_edges(
    "debater",
    should_continue,
    {
        "analyst": "analyst",
        "writer": "writer"
    }
)

workflow.add_edge("writer", "image_generator")
workflow.add_edge("image_generator", "xhs_publisher")
workflow.add_edge("xhs_publisher", END)

app_graph = workflow.compile()
