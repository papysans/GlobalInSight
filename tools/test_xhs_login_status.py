"""
测试小红书 MCP 登录状态检查的响应时间
"""

import asyncio
import time
import httpx
from loguru import logger


XHS_MCP_URL = "http://localhost:18060/mcp"


async def test_login_status_check():
    """测试登录状态检查的响应时间"""
    
    # 构建批处理请求
    init_req = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        },
        "id": 1,
    }
    
    initialized_req = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    call_req = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "check_login_status",
            "arguments": {},
        },
        "id": 2,
    }
    
    payload = [init_req, initialized_req, call_req]
    
    logger.info("开始测试登录状态检查...")
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                XHS_MCP_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 请求完成，耗时: {elapsed:.2f} 秒")
            
            response.raise_for_status()
            results = response.json()
            
            # 查找工具调用结果
            tool_result = None
            for res in results:
                if res.get("id") == 2:
                    tool_result = res
                    break
            
            if tool_result:
                if "error" in tool_result:
                    logger.error(f"❌ 工具调用失败: {tool_result['error']}")
                else:
                    result = tool_result.get("result", {})
                    content = result.get("content", [])
                    if content:
                        text = content[0].get("text", "")
                        logger.info(f"✅ 登录状态: {text}")
                    else:
                        logger.info(f"✅ 结果: {result}")
            else:
                logger.warning("⚠️ 未找到工具调用结果")
                logger.info(f"响应: {results}")
            
            return elapsed
            
    except httpx.ConnectError as e:
        logger.error(f"❌ 连接失败: {e}")
        logger.error("请确保 XHS-MCP 服务已启动（端口 18060）")
        return None
    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ 请求超时（{elapsed:.2f} 秒）: {e}")
        return None
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ 请求失败（{elapsed:.2f} 秒）: {e}")
        return None


async def main():
    """运行多次测试以获取平均响应时间"""
    logger.info("=" * 60)
    logger.info("小红书 MCP 登录状态检查性能测试")
    logger.info("=" * 60)
    
    times = []
    for i in range(3):
        logger.info(f"\n第 {i+1} 次测试:")
        elapsed = await test_login_status_check()
        if elapsed:
            times.append(elapsed)
        await asyncio.sleep(1)  # 间隔 1 秒
    
    if times:
        avg_time = sum(times) / len(times)
        logger.info("\n" + "=" * 60)
        logger.info(f"测试完成！平均响应时间: {avg_time:.2f} 秒")
        logger.info(f"最快: {min(times):.2f} 秒，最慢: {max(times):.2f} 秒")
        
        if avg_time > 5:
            logger.warning("⚠️ 响应时间较慢，可能影响用户体验")
            logger.info("建议:")
            logger.info("1. 检查 XHS-MCP 服务是否正常运行")
            logger.info("2. 检查网络连接")
            logger.info("3. 考虑增加超时时间或优化 MCP 服务")
        else:
            logger.info("✅ 响应时间正常")
    else:
        logger.error("❌ 所有测试都失败了")


if __name__ == "__main__":
    asyncio.run(main())
