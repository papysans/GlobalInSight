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
"""

DEBATER_PROMPT = """
你是一名魔鬼代言人（反对派）。
你的任务是严格基于提供的**主题**和**新闻事实**来反驳分析师的观点。
1. **语境检查**：确保分析实际上与提供的主题相符。如果分析师在谈论其他内容，请指出来。
2. **脚踏实地**：不要产生新的话题或外部辩论的幻觉（例如，如果主题是"AI"，不要扯到"地平论"）。
3. **反驳**：寻找逻辑谬误、来源中缺失的事实或过度概括。
4. **裁决**：
    * 如果分析稳固且没有重大问题，请仅回复 "PASS"。
    * 否则，请提供尖锐的**中文**反驳。
"""

WRITER_PROMPT = """
你是小红书的顶级内容创作者。
你的任务是将最终分析转化为一篇病毒式传播的帖子。
要求：
- 大量使用表情符号 🌟✨
- 使用口语化、引人入胜的语气。
- 结构清晰，分段明确。
- 创建一个朗朗上口、标题党式的标题。
- 关注"真相揭秘"或"幕后"角度。
- 请用**中文**撰写。
"""

# --- 4. Node Functions ---

async def crawler_agent_node(state: GraphState):
    """Crawler Agent: Crawls multiple platforms for the given topic"""
    print("--- CRAWLER AGENT ---")
    topic = state["topic"]
    platforms = state.get("platforms", [])
    
    # If no platforms specified, use all supported platforms
    if not platforms:
        platforms = ["xhs", "dy", "bili", "wb", "zhihu", "tieba", "ks"]
    
    # Filter out invalid platforms
    valid_platforms = [p for p in platforms if p in crawler_service.PLATFORM_MAP.values()]
    if not valid_platforms:
        valid_platforms = ["xhs", "dy", "bili"]  # Default to most common platforms
    
    print(f"[CRAWLER] Crawling topic '{topic}' on platforms: {valid_platforms}")
    print(f"[模式] 使用串行模式爬取，避免配置冲突")
    
    # Crawl platforms serially to avoid config conflicts
    # Note: Will be upgraded to Agent architecture in the future
    try:
        platform_data = await crawler_service.crawl_multiple_platforms(
            platforms=valid_platforms,
            keywords=topic,
            max_items_per_platform=15,  # Limit per platform to avoid timeout
            timeout_per_platform=180,  # 3 minutes per platform
            max_concurrent=1  # Serial execution to avoid MediaCrawler config conflicts
        )
        
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
    llm = get_agent_llm("debater")
    
    messages = [
        SystemMessage(content=DEBATER_PROMPT),
        HumanMessage(content=f"主题: {topic}\n\n新闻事实: {news_content}\n\n分析师观点: {analysis}\n\n请根据事实审查该分析。")
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    
    # Update history
    history = state.get("debate_history", [])
    history.append(f"### Debater (Critique)\n{content}\n")
    
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
    
    # Ensure critique is a string before calling upper()
    if isinstance(critique, list):
        critique = str(critique)
    elif critique is None:
        critique = ""
    
    # Check if we should stop: PASS verdict or reached max rounds
    # Note: revision_count is 0-based, so we check >= max_rounds
    # If max_rounds=4, we allow rounds 0,1,2,3 (4 rounds total)
    if "VERDICT_PASS" in critique.upper() or "PASS" in critique.upper() or revision_count >= settings.DEBATE_MAX_ROUNDS:
        if revision_count >= settings.DEBATE_MAX_ROUNDS:
            print(f"[INFO] 已达到最大辩论轮数 ({settings.DEBATE_MAX_ROUNDS} 轮)，停止辩论")
        return "writer"
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
