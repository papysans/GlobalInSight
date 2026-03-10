"""
Opinion MCP Server - 舆论分析 MCP 服务器主入口

基于 FastAPI 实现的 MCP 兼容服务器，
暴露舆论分析工具供 AI 助手调用。

支持两种协议:
1. 标准 MCP 协议 (SSE + JSON-RPC) - 用于 ClawdBot 等 MCP 客户端
2. HTTP REST API - 用于直接调用和测试

功能:
- 8 个 MCP 工具注册
- SSE 传输层 (标准 MCP 协议)
- 健康检查端点
- 命令行参数解析
- 优雅关闭处理

使用方法:
    python -m opinion_mcp.server --port 18061
"""

import argparse
import asyncio
import json
import signal
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from opinion_mcp.config import config

# 导入所有工具函数
from opinion_mcp.tools import (
    analyze_topic,
    get_analysis_status,
    get_analysis_result,
    update_copywriting,
    get_hot_news,
    publish_to_xhs,
    get_settings,
    register_webhook,
    generate_topic_cards,
)
from opinion_mcp.tools.validate_publish import validate_publish


# ============================================================
# MCP 协议数据模型
# ============================================================

class MCPToolInput(BaseModel):
    """MCP 工具输入参数"""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class MCPTool(BaseModel):
    """MCP 工具定义"""
    name: str
    description: str
    inputSchema: MCPToolInput


class MCPToolsResponse(BaseModel):
    """MCP 工具列表响应"""
    tools: List[MCPTool]


class MCPCallToolRequest(BaseModel):
    """MCP 工具调用请求"""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPCallToolResponse(BaseModel):
    """MCP 工具调用响应"""
    content: List[Dict[str, Any]]
    isError: bool = False


class MCPServerInfo(BaseModel):
    """MCP 服务器信息"""
    name: str
    version: str
    protocolVersion: str = "2024-11-05"


class MCPInitializeResponse(BaseModel):
    """MCP 初始化响应"""
    serverInfo: MCPServerInfo
    capabilities: Dict[str, Any]


# ============================================================
# 服务器状态
# ============================================================

_server_started_at: Optional[datetime] = None
_shutdown_event: Optional[asyncio.Event] = None


# ============================================================
# 7.2 初始化 FastAPI 应用 (MCP 兼容)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _server_started_at
    _server_started_at = datetime.now()
    logger.info("Opinion MCP Server 启动中...")
    yield
    logger.info("Opinion MCP Server 关闭中...")


app = FastAPI(
    title="Opinion MCP Server",
    description="GlobalInSight 舆论分析 MCP 服务 - 提供多平台舆情分析、热榜获取、小红书发布等功能",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 7.3 注册所有工具 (8个) - 工具定义
# ============================================================

MCP_TOOLS: List[MCPTool] = [
    MCPTool(
        name="analyze_topic",
        description="启动舆论分析任务。启动一个后台分析任务，立即返回 job_id。分析过程在后台执行，可通过 get_analysis_status 查询进度。",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "topic": {"type": "string", "description": "要分析的话题/议题"},
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要爬取的平台列表，可选值: wb, dy, ks, bili, tieba, zhihu, xhs, hn, reddit。留空则使用默认平台"
                },
                "debate_rounds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 2,
                    "description": "辩论轮数 (1-5)，影响分析深度，默认2轮"
                },
                "image_count": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9,
                    "default": 2,
                    "description": "生成图片数量 (0-9)，0表示不生图，默认2张"
                }
            },
            required=["topic"]
        )
    ),
    MCPTool(
        name="get_analysis_status",
        description="查询舆论分析任务的当前状态和进度",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "job_id": {
                    "type": "string",
                    "description": "任务 ID，由 analyze_topic 返回。留空则查询最近一次任务"
                }
            },
            required=[]
        )
    ),
    MCPTool(
        name="get_analysis_result",
        description="获取已完成的舆论分析结果，包含文案和配图",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "job_id": {
                    "type": "string",
                    "description": "任务 ID。留空则获取最近一次完成的任务结果"
                }
            },
            required=[]
        )
    ),
    MCPTool(
        name="update_copywriting",
        description="修改分析结果的文案内容",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "job_id": {"type": "string", "description": "任务 ID"},
                "title": {"type": "string", "description": "新标题（留空则不修改）"},
                "subtitle": {"type": "string", "description": "新副标题（留空则不修改）"},
                "content": {"type": "string", "description": "新正文内容（留空则不修改）"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "新标签列表（留空则不修改）"
                }
            },
            required=["job_id"]
        )
    ),
    MCPTool(
        name="get_hot_news",
        description="获取多平台热榜数据，可用于发现热门话题",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "返回条数 (1-100)，默认 20"
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "筛选平台列表，留空返回所有平台"
                },
                "include_hn": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否包含 Hacker News，默认 True"
                }
            },
            required=[]
        )
    ),
    MCPTool(
        name="publish_to_xhs",
        description="将分析结果发布到小红书",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "job_id": {"type": "string", "description": "分析任务 ID，将使用该任务的结果发布"},
                "title": {"type": "string", "description": "自定义标题，留空则使用分析结果的标题"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "话题标签列表，留空则使用分析结果的标签"
                }
            },
            required=["job_id"]
        )
    ),
    MCPTool(
        name="get_settings",
        description="获取当前的分析配置，包括默认平台、图片数量等",
        inputSchema=MCPToolInput(
            type="object",
            properties={},
            required=[]
        )
    ),
    MCPTool(
        name="register_webhook",
        description="注册进度推送的 Webhook URL。MCP Server 会在关键节点主动推送进度到指定 URL。",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "callback_url": {"type": "string", "description": "接收进度推送的 URL"},
                "job_id": {"type": "string", "description": "要监听的任务 ID"}
            },
            required=["callback_url", "job_id"]
        )
    ),
    MCPTool(
        name="validate_publish",
        description="验证发布条件是否满足。检查 XHS-MCP 服务状态、任务完成状态、图片 URL 有效性，返回详细验证结果和修复建议。",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "job_id": {
                    "type": "string",
                    "description": "任务 ID，留空则使用最近完成的任务"
                }
            },
            required=[]
        )
    ),
    MCPTool(
        name="generate_topic_cards",
        description="为已完成的分析任务生成数据卡片图片（标题卡、观点卡、辩论时间线、趋势图、雷达图、核心发现、平台热度）。需要先启动渲染服务 (renderer/)。",
        inputSchema=MCPToolInput(
            type="object",
            properties={
                "job_id": {
                    "type": "string",
                    "description": "分析任务 ID，留空则使用最近完成的任务"
                },
                "card_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "指定要生成的卡片类型，留空默认生成四张核心卡（title, debate_timeline, trend, radar）。可选: title, insight, debate_timeline, trend, radar, key_findings, platform_heat"
                }
            },
            required=[]
        )
    ),
]

# 工具名称到函数的映射
TOOL_HANDLERS = {
    "analyze_topic": analyze_topic,
    "get_analysis_status": get_analysis_status,
    "get_analysis_result": get_analysis_result,
    "update_copywriting": update_copywriting,
    "get_hot_news": get_hot_news,
    "publish_to_xhs": publish_to_xhs,
    "get_settings": get_settings,
    "register_webhook": register_webhook,
    "validate_publish": validate_publish,
    "generate_topic_cards": generate_topic_cards,
}


# ============================================================
# MCP 协议端点 - 标准 SSE 传输层
# ============================================================

# 存储 SSE 会话
_sse_sessions: Dict[str, asyncio.Queue] = {}


async def handle_jsonrpc_request(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理 JSON-RPC 请求
    
    Args:
        request_data: JSON-RPC 请求数据
        
    Returns:
        JSON-RPC 响应，如果是通知则返回 None
    """
    method = request_data.get("method", "")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    logger.debug(f"[MCP] JSON-RPC 请求: method={method}, id={request_id}")
    
    # 通知消息不需要响应
    if request_id is None:
        return None
    
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "Opinion Analyzer",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {"listChanged": False}
                }
            }
        elif method == "tools/list":
            result = {
                "tools": [tool.model_dump() for tool in MCP_TOOLS]
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            logger.info(f"[MCP] 调用工具: {tool_name}, 参数: {arguments}")
            
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知工具: {tool_name}"
                    }
                }
            
            # 调用工具
            tool_result = await handler(**arguments)
            result_text = json.dumps(tool_result, ensure_ascii=False, indent=2)
            
            result = {
                "content": [{"type": "text", "text": result_text}],
                "isError": False
            }
        elif method == "ping":
            result = {}
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"未知方法: {method}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
    except Exception as e:
        logger.exception(f"[MCP] 处理请求失败: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


@app.get("/sse")
async def sse_endpoint(request: Request):
    """
    SSE 端点 - 标准 MCP 协议传输层
    
    客户端通过此端点建立 SSE 连接，接收服务器推送的消息。
    """
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _sse_sessions[session_id] = queue
    
    logger.info(f"[MCP] SSE 连接建立: session={session_id}")
    
    async def event_generator():
        try:
            # 发送 endpoint 事件，告知客户端 POST 消息的地址
            endpoint_event = f"event: endpoint\ndata: /message?sessionId={session_id}\n\n"
            yield endpoint_event
            
            # 持续发送队列中的消息
            while True:
                try:
                    # 检查客户端是否断开
                    if await request.is_disconnected():
                        break
                    
                    # 等待消息，超时后继续循环检查连接
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield f"event: message\ndata: {json.dumps(message)}\n\n"
                    except asyncio.TimeoutError:
                        # 发送心跳
                        yield ": heartbeat\n\n"
                        
                except asyncio.CancelledError:
                    break
                    
        finally:
            # 清理会话
            _sse_sessions.pop(session_id, None)
            logger.info(f"[MCP] SSE 连接关闭: session={session_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/message")
async def message_endpoint(request: Request, sessionId: str = None):
    """
    消息端点 - 接收客户端的 JSON-RPC 请求
    
    客户端通过此端点发送 JSON-RPC 请求，响应通过 SSE 推送。
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"[MCP] 解析请求体失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    logger.debug(f"[MCP] 收到消息: session={sessionId}, body={body}")
    
    # 支持批量请求
    if isinstance(body, list):
        requests = body
    else:
        requests = [body]
    
    responses = []
    for req in requests:
        response = await handle_jsonrpc_request(req)
        if response is not None:
            responses.append(response)
    
    # 如果有 SSE 会话，通过 SSE 推送响应
    if sessionId and sessionId in _sse_sessions:
        queue = _sse_sessions[sessionId]
        for resp in responses:
            await queue.put(resp)
        return {"status": "accepted"}
    
    # 否则直接返回响应
    if len(responses) == 1:
        return responses[0]
    return responses


@app.post("/mcp")
async def mcp_post_endpoint(request: Request):
    """
    MCP POST 端点 - 兼容直接 POST JSON-RPC 请求
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"[MCP] 解析请求体失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # 支持批量请求
    if isinstance(body, list):
        requests = body
    else:
        requests = [body]
    
    responses = []
    for req in requests:
        response = await handle_jsonrpc_request(req)
        if response is not None:
            responses.append(response)
    
    if len(responses) == 1:
        return responses[0]
    return responses


@app.get("/mcp")
async def mcp_info():
    """MCP 服务信息端点"""
    return {
        "name": "Opinion Analyzer",
        "version": "1.0.0",
        "protocolVersion": "2024-11-05",
        "description": "GlobalInSight 舆论分析 MCP 服务",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse",
            "message": "/message"
        }
    }


# 根路径处理 - 兼容 mcporter 等客户端
@app.get("/")
async def root_get():
    """根路径 GET - 返回服务信息"""
    return {
        "name": "Opinion Analyzer",
        "version": "1.0.0",
        "protocolVersion": "2024-11-05",
        "description": "GlobalInSight 舆论分析 MCP 服务",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse",
            "message": "/message",
            "mcp": "/mcp"
        }
    }


@app.post("/")
async def root_post(request: Request):
    """根路径 POST - 处理 JSON-RPC 请求（兼容 mcporter）"""
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"[MCP] 解析请求体失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # 支持批量请求
    if isinstance(body, list):
        requests = body
    else:
        requests = [body]
    
    responses = []
    for req in requests:
        response = await handle_jsonrpc_request(req)
        if response is not None:
            responses.append(response)
    
    if len(responses) == 1:
        return responses[0]
    return responses if responses else {"status": "ok"}


@app.post("/mcp/initialize")
async def mcp_initialize() -> MCPInitializeResponse:
    """MCP 初始化端点 (HTTP 模式)"""
    return MCPInitializeResponse(
        serverInfo=MCPServerInfo(
            name="Opinion Analyzer",
            version="1.0.0",
            protocolVersion="2024-11-05"
        ),
        capabilities={
            "tools": {"listChanged": False},
        }
    )


@app.get("/mcp/tools")
@app.post("/mcp/tools/list")
async def mcp_list_tools() -> MCPToolsResponse:
    """MCP 工具列表端点"""
    return MCPToolsResponse(tools=MCP_TOOLS)


@app.post("/mcp/tools/call")
async def mcp_call_tool(request: MCPCallToolRequest) -> MCPCallToolResponse:
    """MCP 工具调用端点 (HTTP 模式)"""
    tool_name = request.name
    arguments = request.arguments
    
    logger.info(f"[MCP] 调用工具: {tool_name}, 参数: {arguments}")
    
    # 查找工具处理函数
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        logger.error(f"[MCP] 未知工具: {tool_name}")
        return MCPCallToolResponse(
            content=[{"type": "text", "text": f"未知工具: {tool_name}"}],
            isError=True
        )
    
    try:
        # 调用工具函数
        result = await handler(**arguments)
        
        # 格式化响应
        result_text = json.dumps(result, ensure_ascii=False, indent=2)
        
        logger.info(f"[MCP] 工具 {tool_name} 执行成功")
        
        return MCPCallToolResponse(
            content=[{"type": "text", "text": result_text}],
            isError=False
        )
        
    except Exception as e:
        logger.exception(f"[MCP] 工具 {tool_name} 执行失败: {e}")
        return MCPCallToolResponse(
            content=[{"type": "text", "text": f"工具执行失败: {str(e)}"}],
            isError=True
        )


# ============================================================
# 7.4 实现健康检查端点
# ============================================================

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点
    
    返回服务器状态信息，用于监控和负载均衡。
    """
    uptime_seconds = None
    if _server_started_at:
        uptime_seconds = (datetime.now() - _server_started_at).total_seconds()
    
    return {
        "status": "healthy",
        "service": "Opinion MCP Server",
        "version": "1.0.0",
        "started_at": _server_started_at.isoformat() if _server_started_at else None,
        "uptime_seconds": round(uptime_seconds, 2) if uptime_seconds else None,
        "available_tools": [tool.name for tool in MCP_TOOLS],
        "backend_url": config.BACKEND_URL,
    }


# ============================================================
# 直接 API 端点 (便于测试和兼容)
# ============================================================

# 请求体模型
class AnalyzeTopicRequest(BaseModel):
    """分析话题请求体"""
    topic: str
    platforms: Optional[List[str]] = None
    debate_rounds: int = 2
    image_count: int = 2


class JobIdRequest(BaseModel):
    """任务 ID 请求体"""
    job_id: Optional[str] = None


class HotNewsRequest(BaseModel):
    """热榜请求体"""
    limit: int = 20
    platforms: Optional[List[str]] = None
    include_hn: bool = True


class PublishXhsRequest(BaseModel):
    """发布小红书请求体"""
    job_id: str
    title: Optional[str] = None
    tags: Optional[List[str]] = None


class WebhookRequest(BaseModel):
    """Webhook 注册请求体"""
    callback_url: str
    job_id: str


class UpdateCopywritingRequest(BaseModel):
    """更新文案请求体"""
    job_id: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class GenerateCardsRequest(BaseModel):
    """生成数据卡片请求体"""
    job_id: Optional[str] = None
    card_types: Optional[List[str]] = None


# 兼容直接调用工具名的端点
@app.post("/analyze_topic")
async def direct_analyze_topic_post(body: AnalyzeTopicRequest) -> Dict[str, Any]:
    """直接调用分析工具（POST 请求）"""
    return await analyze_topic(
        topic=body.topic,
        platforms=body.platforms,
        debate_rounds=body.debate_rounds,
        image_count=body.image_count,
    )


@app.get("/analyze_topic")
async def direct_analyze_topic_get(
    topic: str,
    platforms: Optional[str] = None,
    debate_rounds: int = 2,
    image_count: int = 2,
) -> Dict[str, Any]:
    """直接调用分析工具（GET 请求）"""
    # 解析 platforms 参数（逗号分隔）
    platform_list = None
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    
    return await analyze_topic(
        topic=topic,
        platforms=platform_list,
        debate_rounds=debate_rounds,
        image_count=image_count,
    )


@app.post("/get_analysis_status")
async def direct_get_status_post(body: JobIdRequest) -> Dict[str, Any]:
    """直接查询状态（POST 请求）"""
    return await get_analysis_status(job_id=body.job_id)


@app.get("/get_analysis_status")
async def direct_get_status_get(job_id: Optional[str] = None) -> Dict[str, Any]:
    """直接查询状态（GET 请求 - 查询参数）"""
    return await get_analysis_status(job_id=job_id)


@app.get("/get_analysis_status/{job_id}")
async def direct_get_status_path(job_id: str) -> Dict[str, Any]:
    """直接查询状态（GET 请求 - 路径参数）"""
    return await get_analysis_status(job_id=job_id)


@app.post("/get_analysis_result")
async def direct_get_result_post(body: JobIdRequest) -> Dict[str, Any]:
    """直接获取结果（POST 请求）"""
    return await get_analysis_result(job_id=body.job_id)


@app.get("/get_analysis_result")
async def direct_get_result_get(job_id: Optional[str] = None) -> Dict[str, Any]:
    """直接获取结果（GET 请求 - 查询参数）"""
    return await get_analysis_result(job_id=job_id)


@app.get("/get_analysis_result/{job_id}")
async def direct_get_result_path(job_id: str) -> Dict[str, Any]:
    """直接获取结果（GET 请求 - 路径参数）"""
    return await get_analysis_result(job_id=job_id)


@app.post("/get_hot_news")
async def direct_get_hotnews_post(body: HotNewsRequest) -> Dict[str, Any]:
    """直接获取热榜（POST 请求）"""
    return await get_hot_news(
        limit=body.limit,
        platforms=body.platforms,
        include_hn=body.include_hn,
    )


@app.get("/get_hot_news")
async def direct_get_hotnews_get(
    limit: int = 20,
    include_hn: bool = True,
) -> Dict[str, Any]:
    """直接获取热榜（GET 请求）"""
    return await get_hot_news(limit=limit, include_hn=include_hn)


@app.post("/get_settings")
@app.get("/get_settings")
async def direct_get_settings() -> Dict[str, Any]:
    """直接获取设置（兼容端点）"""
    return await get_settings()


@app.post("/publish_to_xhs")
async def direct_publish_xhs(body: PublishXhsRequest) -> Dict[str, Any]:
    """直接发布到小红书"""
    return await publish_to_xhs(
        job_id=body.job_id,
        title=body.title,
        tags=body.tags,
    )


@app.post("/generate_topic_cards")
async def direct_generate_topic_cards_post(body: GenerateCardsRequest) -> Dict[str, Any]:
    """直接生成数据卡片（POST 请求）"""
    return await generate_topic_cards(job_id=body.job_id, card_types=body.card_types)


@app.get("/generate_topic_cards")
async def direct_generate_topic_cards_get(
    job_id: Optional[str] = None,
    card_types: Optional[str] = None,
) -> Dict[str, Any]:
    """直接生成数据卡片（GET 请求）"""
    parsed_types = None
    if card_types:
        parsed_types = [item.strip() for item in card_types.split(",") if item.strip()]
    return await generate_topic_cards(job_id=job_id, card_types=parsed_types)


@app.post("/register_webhook")
async def direct_register_webhook(body: WebhookRequest) -> Dict[str, Any]:
    """直接注册 Webhook"""
    return await register_webhook(
        callback_url=body.callback_url,
        job_id=body.job_id,
    )


@app.post("/update_copywriting")
async def direct_update_copywriting(body: UpdateCopywritingRequest) -> Dict[str, Any]:
    """直接更新文案"""
    return await update_copywriting(
        job_id=body.job_id,
        title=body.title,
        subtitle=body.subtitle,
        content=body.content,
        tags=body.tags,
    )


class ValidatePublishRequest(BaseModel):
    """发布验证请求体"""
    job_id: Optional[str] = None


@app.post("/validate_publish")
async def direct_validate_publish(body: ValidatePublishRequest) -> Dict[str, Any]:
    """直接验证发布条件"""
    return await validate_publish(job_id=body.job_id)


@app.get("/validate_publish")
async def direct_validate_publish_get(job_id: Optional[str] = None) -> Dict[str, Any]:
    """直接验证发布条件（GET 请求）"""
    return await validate_publish(job_id=job_id)


@app.get("/validate_publish/{job_id}")
async def direct_validate_publish_path(job_id: str) -> Dict[str, Any]:
    """直接验证发布条件（路径参数）"""
    return await validate_publish(job_id=job_id)


# 原有的 /api/ 前缀端点
@app.post("/api/analyze")
async def api_analyze_topic(
    topic: str,
    platforms: Optional[List[str]] = None,
    debate_rounds: int = 2,
    image_count: int = 2,
) -> Dict[str, Any]:
    """直接调用分析工具"""
    return await analyze_topic(
        topic=topic,
        platforms=platforms,
        debate_rounds=debate_rounds,
        image_count=image_count,
    )


@app.get("/api/status")
@app.get("/api/status/{job_id}")
async def api_get_status(job_id: Optional[str] = None) -> Dict[str, Any]:
    """直接查询状态"""
    return await get_analysis_status(job_id=job_id)


@app.get("/api/result")
@app.get("/api/result/{job_id}")
async def api_get_result(job_id: Optional[str] = None) -> Dict[str, Any]:
    """直接获取结果"""
    return await get_analysis_result(job_id=job_id)


@app.get("/api/hotnews")
async def api_get_hotnews(
    limit: int = 20,
    include_hn: bool = True,
) -> Dict[str, Any]:
    """直接获取热榜"""
    return await get_hot_news(limit=limit, include_hn=include_hn)


@app.get("/api/settings")
async def api_get_settings() -> Dict[str, Any]:
    """直接获取设置"""
    return await get_settings()


# ============================================================
# 7.5 实现命令行参数解析 (--port)
# ============================================================

def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        description="Opinion MCP Server - GlobalInSight 舆论分析 MCP 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python -m opinion_mcp.server                    # 使用默认端口 18061
    python -m opinion_mcp.server --port 18062      # 使用自定义端口
    python -m opinion_mcp.server --host 0.0.0.0    # 监听所有接口
        """,
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=config.MCP_PORT,
        help=f"服务器端口 (默认: {config.MCP_PORT})",
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=config.MCP_HOST,
        help=f"服务器主机 (默认: {config.MCP_HOST})",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式",
    )
    
    return parser.parse_args()


# ============================================================
# 7.6 实现优雅关闭处理
# ============================================================

def setup_signal_handlers() -> None:
    """
    设置信号处理器，支持优雅关闭
    """
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        sig_name = signal.Signals(signum).name
        logger.info(f"收到信号 {sig_name}，正在优雅关闭...")
        
        if _shutdown_event:
            _shutdown_event.set()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    # Unix 系统额外处理 SIGTERM
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)
    
    logger.debug("信号处理器已设置")


def log_startup_info(host: str, port: int) -> None:
    """
    记录启动信息
    
    Args:
        host: 服务器主机
        port: 服务器端口
    """
    tools = [tool.name for tool in MCP_TOOLS]
    
    logger.info("=" * 60)
    logger.info("Opinion MCP Server 启动")
    logger.info("=" * 60)
    logger.info(f"  服务地址: http://{host}:{port}")
    logger.info(f"  健康检查: http://{host}:{port}/health")
    logger.info(f"  MCP 端点: http://{host}:{port}/mcp")
    logger.info(f"  后端地址: {config.BACKEND_URL}")
    logger.info(f"  可用工具: {len(tools)} 个")
    for tool in tools:
        logger.info(f"    - {tool}")
    logger.info("=" * 60)


# ============================================================
# 主入口
# ============================================================

def main() -> None:
    """
    MCP 服务器主入口
    """
    # 解析命令行参数
    args = parse_args()
    
    # 配置日志级别
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 记录启动信息
    log_startup_info(args.host, args.port)
    
    try:
        # 运行 FastAPI 服务器
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="debug" if args.debug else "info",
        )
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在关闭...")
    except Exception as e:
        logger.exception(f"服务器运行出错: {e}")
        sys.exit(1)
    finally:
        logger.info("服务器已关闭")


if __name__ == "__main__":
    main()
