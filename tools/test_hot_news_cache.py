"""
测试热榜缓存配置和持久化
"""

import asyncio
import httpx
from datetime import datetime
from loguru import logger


BACKEND_URL = "http://127.0.0.1:8000/api"


async def test_cache_info():
    """测试缓存信息接口"""
    logger.info("=" * 60)
    logger.info("测试缓存信息")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/hot-news/cache-info")
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"缓存状态:")
            logger.info(f"  - 是否有缓存: {data.get('has_cache')}")
            logger.info(f"  - 缓存键: {data.get('cache_keys')}")
            logger.info(f"  - 最新缓存时间: {data.get('latest_cache_time')}")
            logger.info(f"  - 过期时间（分钟）: {data.get('expiry_minutes')}")
            
            expiry_minutes = data.get('expiry_minutes', 0)
            if expiry_minutes >= 240:
                logger.info(f"✅ 缓存过期时间已优化为 {expiry_minutes} 分钟（{expiry_minutes/60:.1f} 小时）")
            elif expiry_minutes == 30:
                logger.warning(f"⚠️ 缓存过期时间仍为 30 分钟，建议增加到 240 分钟")
            else:
                logger.info(f"ℹ️ 缓存过期时间: {expiry_minutes} 分钟")
            
            return data
            
    except Exception as e:
        logger.error(f"❌ 获取缓存信息失败: {e}")
        return None


async def test_scheduler_status():
    """测试调度器状态"""
    logger.info("\n" + "=" * 60)
    logger.info("测试调度器状态")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/hot-news/status")
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"调度器状态:")
            logger.info(f"  - 是否运行: {data.get('is_running')}")
            logger.info(f"  - 上次运行时间: {data.get('last_run_time')}")
            
            last_result = data.get('last_result')
            if last_result:
                logger.info(f"  - 上次结果: {'成功' if last_result.get('success') else '失败'}")
                if last_result.get('success'):
                    logger.info(f"    - 总新闻数: {last_result.get('total_news')}")
                    logger.info(f"    - 成功源数: {last_result.get('successful_sources')}/{last_result.get('total_sources')}")
            
            return data
            
    except Exception as e:
        logger.error(f"❌ 获取调度器状态失败: {e}")
        return None


async def test_hot_news_fetch():
    """测试热榜数据获取"""
    logger.info("\n" + "=" * 60)
    logger.info("测试热榜数据获取")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 第一次请求（可能从缓存）
            logger.info("第一次请求...")
            start_time = datetime.now()
            response = await client.post(
                f"{BACKEND_URL}/hot-news/collect",
                json={"platforms": ["all"], "force_refresh": False}
            )
            response.raise_for_status()
            data = response.json()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ 请求完成，耗时: {elapsed:.2f} 秒")
            logger.info(f"  - 总新闻数: {data.get('total_news')}")
            logger.info(f"  - 从缓存: {data.get('from_cache')}")
            logger.info(f"  - 正在刷新: {data.get('refreshing')}")
            logger.info(f"  - 收集时间: {data.get('collection_time')}")
            
            # 第二次请求（应该从缓存）
            logger.info("\n第二次请求（应该从缓存）...")
            start_time = datetime.now()
            response = await client.post(
                f"{BACKEND_URL}/hot-news/collect",
                json={"platforms": ["all"], "force_refresh": False}
            )
            response.raise_for_status()
            data2 = response.json()
            elapsed2 = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ 请求完成，耗时: {elapsed2:.2f} 秒")
            logger.info(f"  - 从缓存: {data2.get('from_cache')}")
            
            if data2.get('from_cache') and elapsed2 < 1.0:
                logger.info("✅ 缓存命中，响应速度快")
            elif not data2.get('from_cache'):
                logger.warning("⚠️ 未命中缓存，可能缓存已过期")
            
            return data
            
    except Exception as e:
        logger.error(f"❌ 获取热榜数据失败: {e}")
        return None


async def test_manual_refresh():
    """测试手动刷新"""
    logger.info("\n" + "=" * 60)
    logger.info("测试手动刷新")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info("触发手动刷新...")
            start_time = datetime.now()
            response = await client.post(f"{BACKEND_URL}/hot-news/run-once")
            response.raise_for_status()
            data = response.json()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ 刷新完成，耗时: {elapsed:.2f} 秒")
            logger.info(f"  - 成功: {data.get('success')}")
            
            last_result = data.get('last_result')
            if last_result and last_result.get('success'):
                logger.info(f"  - 总新闻数: {last_result.get('total_news')}")
                logger.info(f"  - 成功源数: {last_result.get('successful_sources')}/{last_result.get('total_sources')}")
            
            return data
            
    except Exception as e:
        logger.error(f"❌ 手动刷新失败: {e}")
        return None


async def main():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("热榜缓存优化测试")
    logger.info("=" * 60)
    
    # 1. 检查缓存配置
    cache_info = await test_cache_info()
    
    # 2. 检查调度器状态
    scheduler_status = await test_scheduler_status()
    
    # 3. 测试数据获取和缓存
    hot_news = await test_hot_news_fetch()
    
    # 4. 测试手动刷新（可选，会触发实际抓取）
    # manual_refresh = await test_manual_refresh()
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    if cache_info and cache_info.get('expiry_minutes') >= 240:
        logger.info("✅ 缓存过期时间已优化")
    else:
        logger.warning("⚠️ 缓存过期时间需要优化")
    
    if scheduler_status and scheduler_status.get('is_running'):
        logger.info("✅ 调度器正常运行")
    else:
        logger.warning("⚠️ 调度器未运行")
    
    if hot_news and hot_news.get('from_cache'):
        logger.info("✅ 缓存功能正常")
    else:
        logger.info("ℹ️ 首次请求或缓存已过期")
    
    logger.info("\n提示: 重启后端服务以应用新配置")


if __name__ == "__main__":
    asyncio.run(main())
