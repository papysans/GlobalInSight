#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试核心平台配置
验证：微博、知乎、B站、百度、百度贴吧、抖音、快手
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.tophub_collector import tophub_collector, TOPHUB_SOURCES
from loguru import logger


async def test_core_platforms():
    """测试核心平台配置"""
    print("\n" + "=" * 80)
    print(" 🎯 测试核心平台配置")
    print("=" * 80 + "\n")
    
    print("已配置的平台:")
    for source_id, info in sorted(TOPHUB_SOURCES.items(), key=lambda x: x[1]['priority']):
        print(f"  [{info['priority']}] {info['name']} ({info['platform']}) - {source_id}")
    
    print(f"\n总计: {len(TOPHUB_SOURCES)} 个平台")
    
    # 验证新增平台ID是否正确
    print("\n" + "-" * 80)
    print("验证新增平台:")
    
    # 测试百度贴吧
    print("\n1. 测试百度贴吧 (Om4ejxvxEN)...")
    tieba_result = await tophub_collector.fetch_source_news("Om4ejxvxEN")
    if tieba_result['status'] == 'success':
        print(f"   ✅ 成功！获取了 {tieba_result['news_count']} 条新闻")
        if tieba_result['news_items']:
            print(f"   示例: {tieba_result['news_items'][0]['title']}")
    else:
        print(f"   ❌ 失败: {tieba_result.get('error', '未知错误')}")
    
    await asyncio.sleep(1)
    
    # 测试快手
    print("\n2. 测试快手 (MZd7PrPerO)...")
    kuaishou_result = await tophub_collector.fetch_source_news("MZd7PrPerO")
    if kuaishou_result['status'] == 'success':
        print(f"   ✅ 成功！获取了 {kuaishou_result['news_count']} 条新闻")
        if kuaishou_result['news_items']:
            print(f"   示例: {kuaishou_result['news_items'][0]['title']}")
    else:
        print(f"   ❌ 失败: {kuaishou_result.get('error', '未知错误')}")
    
    # 收集所有平台
    print("\n" + "-" * 80)
    print("收集所有核心平台数据...")
    print("-" * 80 + "\n")
    
    result = await tophub_collector.collect_news(force_refresh=True)
    
    print(f"\n📊 收集结果:")
    print(f"   总平台数: {result['total_sources']}")
    print(f"   成功数: {result['successful_sources']}")
    print(f"   失败数: {result['total_sources'] - result['successful_sources']}")
    print(f"   总新闻数: {result['total_news']}")
    
    # 按平台统计
    from collections import defaultdict
    news_by_platform = defaultdict(int)
    for news in result['news_list']:
        news_by_platform[news['source']] += 1
    
    print(f"\n📈 各平台新闻数量:")
    for platform in sorted(news_by_platform.keys()):
        count = news_by_platform[platform]
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {platform}: {count} 条")
    
    # 检查是否所有核心平台都有数据
    expected_platforms = {info['name'] for info in TOPHUB_SOURCES.values()}
    actual_platforms = set(news_by_platform.keys())
    
    if len(actual_platforms) == len(expected_platforms):
        print(f"\n✅ 所有 {len(expected_platforms)} 个平台都成功获取数据！")
    else:
        missing = expected_platforms - actual_platforms
        if missing:
            print(f"\n⚠️  以下平台暂时无数据: {', '.join(missing)}")
            print("   （这是正常的，TopHub网站某些平台可能间歇性无数据）")


async def main():
    """主函数"""
    try:
        await test_core_platforms()
        
        print("\n" + "=" * 80)
        print(" ✅ 核心平台配置测试完成！")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.exception(f"测试出错: {e}")
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
