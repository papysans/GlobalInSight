import os
import re
from datetime import datetime
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from app.llm import get_agent_llm
from app.config import settings

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
你的任务是阅读提供的新闻内容（如果缺少内容，请根据主题模拟阅读），并提取核心事实。
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
2. **脚踏实地**：不要产生新的话题或外部辩论的幻觉（例如，如果主题是“AI”，不要扯到“地平论”）。
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
- 关注“真相揭秘”或“幕后”角度。
- 请用**中文**撰写。
"""

# --- 4. Node Functions ---

async def reporter_node(state: GraphState):
    print("--- REPORTER ---")
    topic = state["topic"]
    llm = get_agent_llm("reporter")
    
    messages = [
        SystemMessage(content=REPORTER_PROMPT),
        HumanMessage(content=f"主题: {topic}. 链接: {state['urls']}. 请总结核心事实。")
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    return {
        "news_content": content,
        "messages": [f"Reporter: {content[:100]}..."]
    }

async def analyst_node(state: GraphState):
    print("--- ANALYST ---")
    news_content = state["news_content"]
    critique = state.get("critique")
    llm = get_agent_llm("analyst")
    
    prompt = f"新闻事实: {news_content}"
    if critique:
        prompt += f"\n\n需要解决的反对意见: {critique}"
        
    messages = [
        SystemMessage(content=ANALYST_PROMPT),
        HumanMessage(content=prompt)
    ]
    response = await llm.ainvoke(messages)
    content = extract_text_content(response.content)
    
    # Update history
    history = state.get("debate_history", [])
    history.append(f"### Analyst (Round {state.get('revision_count', 0) + 1})\n{content}\n")
    
    return {
        "initial_analysis": content,
        "revision_count": state.get("revision_count", 0) + 1 if critique else 0,
        "messages": [f"Analyst: {content[:100]}..."],
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
        "messages": [f"Debater: {content[:100]}..."],
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
        "messages": [f"Writer: {content[:100]}...", f"System: Document saved to {file_path}"]
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
        
    if "VERDICT_PASS" in critique.upper() or revision_count >= settings.DEBATE_MAX_ROUNDS:
        return "writer"
    return "analyst"

# --- 6. Graph Construction ---

workflow = StateGraph(GraphState)

workflow.add_node("reporter", reporter_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("debater", debater_node)
workflow.add_node("writer", writer_node)

workflow.set_entry_point("reporter")

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
