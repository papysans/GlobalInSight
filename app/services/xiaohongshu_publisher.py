"""
小红书 MCP 发布服务

通过 HTTP 调用 xiaohongshu-mcp 服务发布内容到小红书。
MCP 服务地址：https://github.com/xpzouying/xiaohongshu-mcp
"""

import asyncio
import base64
import httpx
import os
import tempfile
from typing import List, Dict, Any, Optional
from loguru import logger


def _process_image(image: str) -> str:
    """
    处理图片路径/URL/Base64 数据
    
    - 如果是 Base64 data URL，保存为临时文件并返回路径
    - 如果是普通 URL 或本地路径，直接返回
    """
    if image.startswith("data:image/"):
        try:
            # Parse data URL: data:image/png;base64,xxxxx
            header, data = image.split(",", 1)
            # Extract extension from header
            ext = "png"
            if "image/jpeg" in header or "image/jpg" in header:
                ext = "jpg"
            elif "image/png" in header:
                ext = "png"
            elif "image/gif" in header:
                ext = "gif"
            elif "image/webp" in header:
                ext = "webp"
            
            # Decode and save to temp file
            image_data = base64.b64decode(data)
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"xhs_upload_{id(image)}.{ext}")
            with open(temp_path, "wb") as f:
                f.write(image_data)
            logger.info(f"[XHS] Converted Base64 image to temp file: {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"[XHS] Failed to process Base64 image: {e}")
            return image  # Return original on error
    return image


class XiaohongshuPublisher:
    """小红书 MCP 发布客户端"""

    def __init__(self, mcp_url: str = "http://localhost:18060/mcp"):
        self.mcp_url = mcp_url
        self._request_id = 0

    def _next_request_id(self) -> int:
        """生成下一个请求 ID"""
        self._request_id += 1
        return self._request_id

    async def _call_mcp(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具 (使用 HTTP 批处理模式以确保 Session 初始化)

        Args:
            tool_name: MCP 工具名称
            arguments: 工具参数
            timeout: 超时时间（秒）

        Returns:
            MCP 响应结果
        """
        # 1. Initialize Request
        init_id = self._next_request_id()
        init_req = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "xiaohongshu-client", "version": "1.0"}
            },
            "id": init_id,
        }

        # 2. Initialized Notification
        initialized_req = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }

        # 3. Tool Call Request
        call_id = self._next_request_id()
        call_req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
            "id": call_id,
        }

        # Batch Payload
        payload = [init_req, initialized_req, call_req]

        logger.info(f"[XHS MCP] Calling tool: {tool_name}, batch_mode=True, call_id: {call_id}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.mcp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                results = response.json()

                if not isinstance(results, list):
                    return {"success": False, "error": f"Invalid batch response type: {type(results)}"}

                # Find the result for our tool call
                tool_result = None
                for res in results:
                    if res.get("id") == call_id:
                        tool_result = res
                        break
                
                if not tool_result:
                    # Check for initialize errors
                    for res in results:
                        if "error" in res:
                            logger.error(f"[XHS MCP] Batch error (id={res.get('id')}): {res['error']}")
                            return {
                                "success": False, 
                                "error": f"MCP Error: {res['error'].get('message', res['error'])}"
                            }
                    return {"success": False, "error": "Tool call response not found in batch"}

                if "error" in tool_result:
                    error = tool_result["error"]
                    logger.error(f"[XHS MCP] Tool Error: {error}")
                    return {
                        "success": False,
                        "error": error.get("message", str(error)),
                        "code": error.get("code"),
                    }

                logger.info(f"[XHS MCP] Tool {tool_name} succeeded")
                return {"success": True, "result": tool_result.get("result")}

        except httpx.ConnectError as e:
            logger.error(f"[XHS MCP] Connection error: {e}")
            return {
                "success": False,
                "error": "无法连接到小红书 MCP 服务，请确保服务已启动",
            }
        except httpx.TimeoutException as e:
            logger.error(f"[XHS MCP] Timeout: {e}")
            return {
                "success": False,
                "error": f"请求超时（>{timeout:.0f}秒），请稍后重试",
            }
        except Exception as e:
            logger.error(f"[XHS MCP] Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    async def is_available(self) -> bool:
        """
        检查 MCP 服务是否可用
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 仅发送 initialize 请求检查
                request_id = self._next_request_id()
                payload = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "health-check", "version": "1.0"}
                    },
                    "id": request_id,
                }
                response = await client.post(
                    self.mcp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.debug(f"[XHS MCP] Service not available: {e}")
            return False

    async def check_login_status(self) -> Dict[str, Any]:
        """
        检查小红书登录状态

        Returns:
            登录状态信息
        """
        result = await self._call_mcp("check_login_status", timeout=10.0)

        if result.get("success"):
            # 解析 MCP 返回的登录状态
            mcp_result = result.get("result", {})
            # MCP 返回格式可能是 {"content": [{"type": "text", "text": "..."}]}
            content = mcp_result.get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                is_logged_in = "已登录" in text or "logged in" in text.lower()
                return {
                    "success": True,
                    "logged_in": is_logged_in,
                    "message": text,
                }
            return {
                "success": True,
                "logged_in": True,
                "message": "登录状态检查成功",
            }

        return {
            "success": False,
            "logged_in": False,
            "message": result.get("error", "登录状态检查失败"),
        }

    async def publish_content(
        self,
        title: str,
        content: str,
        images: List[str],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        发布图文内容到小红书

        Args:
            title: 标题
            content: 正文内容
            images: 图片列表（支持本地绝对路径或 HTTP URL）

        Returns:
            发布结果
        """
        if not title or not content:
            return {
                "success": False,
                "error": "标题和内容不能为空",
            }

        if not images:
            return {
                "success": False,
                "error": "至少需要一张图片",
            }

        # Process images: convert Base64 data URLs to temp files
        processed_images = [_process_image(img) for img in images]
        
        # Process tags: remove # prefix if present (MCP will add it)
        processed_tags = []
        if tags:
            processed_tags = [tag.lstrip('#') for tag in tags if tag]
        
        logger.info(f"[XHS MCP] Publishing: title='{title[:30]}...', images={len(processed_images)}")
        logger.info(f"[XHS MCP] Tags 详情: 原始={tags}, 处理后={processed_tags}")

        # Build MCP arguments
        mcp_args = {
            "title": title,
            "content": content,
            "images": processed_images,
        }
        
        # Add tags if provided (XHS MCP handles topic selection via browser automation)
        if processed_tags:
            mcp_args["tags"] = processed_tags

        publish_timeout = float(os.getenv("XHS_PUBLISH_TIMEOUT", "240"))
        max_attempts = 2
        last_error = "发布失败"

        for attempt in range(1, max_attempts + 1):
            result = await self._call_mcp(
                "publish_content",
                mcp_args,
                timeout=publish_timeout,
            )

            if result.get("success"):
                mcp_result = result.get("result", {})
                content_list = mcp_result.get("content", [])
                message = ""
                if (
                    content_list
                    and isinstance(content_list, list)
                    and len(content_list) > 0
                ):
                    message = content_list[0].get("text", "")

                return {
                    "success": True,
                    "message": message or "发布成功",
                    "data": mcp_result,
                }

            last_error = result.get("error", "发布失败")
            is_timeout = isinstance(last_error, str) and "超时" in last_error
            if is_timeout and attempt < max_attempts:
                logger.warning(
                    f"[XHS MCP] publish_content 超时，第 {attempt}/{max_attempts} 次失败，2 秒后重试"
                )
                await asyncio.sleep(2)
                continue

            break

        return {
            "success": False,
            "error": last_error,
        }

    async def get_status(self) -> Dict[str, Any]:
        """
        获取小红书 MCP 服务完整状态

        Returns:
            服务状态信息
        """
        # 检查服务可用性
        is_available = await self.is_available()
        if not is_available:
            return {
                "mcp_available": False,
                "login_status": False,
                "message": "小红书 MCP 服务未启动或无法连接",
            }

        # 检查登录状态
        login_result = await self.check_login_status()

        return {
            "mcp_available": True,
            "login_status": login_result.get("logged_in", False),
            "message": login_result.get("message", ""),
        }


# 全局单例
xiaohongshu_publisher = XiaohongshuPublisher()
