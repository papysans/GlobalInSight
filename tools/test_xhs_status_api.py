"""
测试后端 /api/xhs/status 接口的响应时间
"""

import asyncio
import time
import httpx
from loguru import logger


BACKEND_URL = "http://127.0.0.1:8000/api/xhs/status"


async def test_xhs_status_api():
    """测试 XHS 状态接口的响应时间"""
    
    logger.info("开始测试 /api/xhs/status 接口...")
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.get(BACKEND_URL)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 请求完成，耗时: {elapsed:.2f} 秒")
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"响应数据:")
            logger.info(f"  - mcp_available: {result.get('mcp_available')}")
            logger.info(f"  - login_status: {result.get('login_status')}")
            logger.info(f"  - message: {result.get('message')}")
            
            if result.get('mcp_available') and result.get('login_status'):
                logger.info("✅ 小红书 MCP 服务正常，已登录")
            elif result.get('mcp_available'):
                logger.warning("⚠️ 小红书 MCP 服务正常，但未登录")
            else:
                logger.error("❌ 小红书 MCP 服务不可用")
            
            return elapsed
            
    except httpx.ConnectError as e:
        logger.error(f"❌ 连接失败: {e}")
        logger.error("请确保后端服务已启动（端口 8000）")
        return None
    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ 请求超时（{elapsed:.2f} 秒）: {e}")
        return None
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ 请求失败（{elapsed:.2f} 秒）: {e}")
        return None


async def test_concurrent_requests():
    """测试并发请求的情况"""
    logger.info("\n" + "=" * 60)
    logger.info("测试并发请求场景（模拟页面加载）")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # 同时发起多个请求（模拟 onMounted 时的并发）
    tasks = [
        test_xhs_status_api(),
        test_xhs_status_api(),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = time.time() - start_time
    logger.info(f"\n并发请求完成，总耗时: {elapsed:.2f} 秒")
    
    success_count = sum(1 for r in results if isinstance(r, (int, float)))
    logger.info(f"成功: {success_count}/{len(tasks)}")


async def main():
    """运行测试"""
    logger.info("=" * 60)
    logger.info("小红书状态接口性能测试")
    logger.info("=" * 60)
    
    # 单次请求测试
    times = []
    for i in range(3):
        logger.info(f"\n第 {i+1} 次测试:")
        elapsed = await test_xhs_status_api()
        if elapsed:
            times.append(elapsed)
        await asyncio.sleep(1)
    
    if times:
        avg_time = sum(times) / len(times)
        logger.info("\n" + "=" * 60)
        logger.info(f"单次请求平均响应时间: {avg_time:.2f} 秒")
        logger.info(f"最快: {min(times):.2f} 秒，最慢: {max(times):.2f} 秒")
        
        if avg_time > 10:
            logger.warning("⚠️ 响应时间过长，可能影响用户体验")
        elif avg_time > 5:
            logger.warning("⚠️ 响应时间较慢")
        else:
            logger.info("✅ 响应时间正常")
    
    # 并发请求测试
    await test_concurrent_requests()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
