import os
import re
from datetime import datetime
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from app.llm import get_agent_llm
from app.config import settings

from app.services.media_crawler_service import crawler_service

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
    messages: List[str] # Keep for SSE compatibility
    debate_history: List[str] # Track the debate process

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

**标题要求（采用二极管标题法）**：
1. 善于使用标题吸引人，制造反差或悬念
2. 使用爆款关键词（如：真相、内幕、竟然、居然、没想到等）
3. 了解小红书平台的标题特性（短小精悍、情绪化）
4. 标题含适当的emoji表情
5. 标题要能抓住眼球，让人忍不住点开

**正文要求**：
1. **写作风格**：接地气、口语化、亲切自然，像和朋友聊天一样
2. **写作开篇方法**：用疑问句、感叹句或直接切入主题，快速抓住注意力
3. **文本结构**：分段明确，每段2-3句话，使用emoji表情增强表现力
4. **互动引导方法**：在文中适当使用"你们觉得呢？"、"有没有同感的？"等互动语句
5. **小技巧**：使用爆炸词（如：绝了、太绝了、真的、真的假的、天哪等）增强情绪
6. **SEO关键词**：从生成的内容中抽取3~6个SEO关键词，生成#标签放在文章最后
7. **禁止使用**：```首先、其次、然而、总的来说、最后```这些副词

**输出格式要求（必须严格遵守）**：
你的输出必须包含以下两个标记，每个标记占一行：
TITLE: [小红书风格标题，含emoji，使用二极管标题法和爆款关键词]
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
    
    print(f"[CRAWLER] 接收到的平台参数: {platforms} (类型: {type(platforms)})")
    
    # If no platforms specified, use all supported platforms
    if not platforms:
        print("[CRAWLER] 未指定平台，使用所有支持的平台")
        platforms = ["xhs", "dy", "bili", "wb", "zhihu", "tieba", "ks"]
    else:
        print(f"[CRAWLER] 使用用户选择的平台: {platforms}")
    
    # Filter out invalid platforms
    valid_platforms = [p for p in platforms if p in crawler_service.PLATFORM_MAP.values()]
    if not valid_platforms:
        print(f"[CRAWLER] 警告: 所有平台都被过滤，使用默认平台")
        valid_platforms = ["xhs", "dy", "bili"]  # Default to most common platforms
    
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
                "zhihu": "知乎"
            }
            platform_display = platform_name_map.get(platform, platform)
            await workflow_status.update_step("crawler_agent", current_platform=platform_display)
            print(f"[CRAWLER] 正在爬取平台: {platform_display} ({idx+1}/{total_platforms})")
            
            # 爬取单个平台
            try:
                items = await crawler_service.crawl_platform(
                    platform=platform,
                    keywords=topic,
                    max_items=15,
                    timeout=180
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
        
        msg = f"Crawler Agent: Successfully crawled {len(unique_data)} unique items from {len(platform_data)} platforms."
        if not unique_data:
            msg = f"Crawler Agent: No data found for topic '{topic}' on any platform."
        
        print(f"[SUCCESS] Crawler completed: {len(unique_data)} items from {len(platform_data)} platforms")
        
        return {
            "crawler_data": unique_data,
            "platform_data": platform_data,
            "messages": [msg]
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
        SystemMessage(content=REPORTER_PROMPT),
        HumanMessage(content=f"主题: {topic}. 来源: {source_info}.\n\n内容:\n{content_text}\n\n请总结核心事实。")
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    return {
        "news_content": content,
        "messages": [f"Reporter: {content}"]
    }

async def analyst_node(state: GraphState):
    print("--- ANALYST ---")
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
        SystemMessage(content=ANALYST_PROMPT),
        HumanMessage(content=prompt)
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    
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
        SystemMessage(content=DEBATER_PROMPT),
        HumanMessage(content=f"主题: {topic}\n\n新闻事实: {news_content}\n\n分析师观点: {analysis}{prompt_suffix}\n\n请根据事实审查该分析。")
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    
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
    analysis = state["initial_analysis"]
    topic = state["topic"]
    llm = get_agent_llm("writer")
    
    messages = [
        SystemMessage(content=WRITER_PROMPT),
        HumanMessage(content=f"请将此分析转化为小红书帖子：\n{analysis}")
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    
    # Save to Markdown file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Sanitize topic for filename
    safe_topic = re.sub(r'[\\/*?:"<>|]', "", topic)[:20] 
    filename = f"{timestamp}_{safe_topic}.md"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    
    debate_history = "\n".join(state.get("debate_history", []))
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n")
        f.write("## 最终文案\n\n")
        f.write(content)
        f.write("\n\n---\n\n")
        f.write("## 辩论过程记录\n\n")
        f.write(debate_history)
        
    return {
        "final_copy": content,
        "messages": [f"Writer: {content}\n\nSystem: Document saved to {file_path}"]
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

workflow.add_edge("writer", END)

app_graph = workflow.compile()
