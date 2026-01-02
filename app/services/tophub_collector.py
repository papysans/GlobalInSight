#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TopHub 全网热点新闻收集器
从 https://tophub.today/ 聚合网站收集热点新闻
比原来的多平台爬取策略简单高效
"""

import asyncio
import httpx
import re
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
from bs4 import BeautifulSoup


# TopHub 热门榜单配置（只保留用户指定的平台）
TOPHUB_SOURCES = {
    # 综合热榜
    "hot": {"name": "全平台热榜", "category": "综合", "platform": "all", "priority": 0},

    # 社交媒体
    "KqndgxeLl9": {"name": "微博热搜榜", "category": "社交", "platform": "weibo", "priority": 1},

    # 社区问答
    "mproPpoq6O": {"name": "知乎热榜", "category": "社区", "platform": "zhihu", "priority": 2},

    # 视频平台
    "74KvxwokxM": {"name": "B站全站日榜", "category": "视频", "platform": "bilibili", "priority": 3},

    # 搜索引擎
    "Jb0vmloB1G": {"name": "百度实时热点", "category": "搜索", "platform": "baidu", "priority": 4},

    # 社区论坛
    "Om4ejxvxEN": {"name": "百度贴吧热榜", "category": "社区", "platform": "tieba", "priority": 5},

    # 短视频
    "DpQvNABoNE": {"name": "抖音热榜", "category": "短视频", "platform": "douyin", "priority": 6},
    "MZd7PrPerO": {"name": "快手热榜", "category": "短视频", "platform": "kuaishou", "priority": 7},
}

# 记录暂不支持的平台（方便前端展示灰度状态）
PENDING_PLATFORMS = {}


class TopHubCollector:
    """TopHub 全网热点新闻收集器"""
    
    def __init__(self, use_cache: bool = True):
        """
        初始化收集器
        
        Args:
            use_cache: 是否启用缓存功能
        """
        self.base_url = "https://tophub.today"
        self.use_cache = use_cache
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://tophub.today/",
        }
        
        # 导入缓存服务
        if self.use_cache:
            from app.services.hot_news_cache import hot_news_cache
            self.cache_service = hot_news_cache
        else:
            self.cache_service = None
    
    async def fetch_source_news(self, source_id: str) -> Dict:
        """
        从指定的 TopHub 榜单获取新闻
        
        Args:
            source_id: TopHub 榜单ID
            
        Returns:
            包含新闻数据的字典
        """
        source_info = TOPHUB_SOURCES.get(source_id, {"name": "未知来源", "category": "其他"})
        source_name = source_info["name"]
        # 全平台热榜页面使用 /hot，其他使用 /n/{source_id}
        url = f"{self.base_url}/hot" if source_id == "hot" else f"{self.base_url}/n/{source_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                news_items: List[Dict] = []

                # 全平台热榜特殊处理（/hot 页面结构不同）
                if source_id == "hot":
                    # 全榜使用 <li class="child-item"> 结构
                    items = soup.find_all('li', class_='child-item')
                    for idx, item in enumerate(items, 1):
                        try:
                            # 排名在 <span class="index-N">
                            rank_span = item.find('span', class_=re.compile(r'index-\d+'))
                            rank = idx
                            if rank_span:
                                rank_text = rank_span.get_text(strip=True)
                                if rank_text.isdigit():
                                    rank = int(rank_text)

                            # 标题在 <p class="medium-txt"> 里的 <a>
                            title_a = item.select_one('p.medium-txt a')
                            if not title_a:
                                continue
                            title = title_a.get_text(strip=True)
                            link = title_a.get('href', '')

                            # 平台和热度在 <p class="small-txt">
                            # 格式: "知乎 ‧ 684万热度"
                            small_txt = item.select_one('p.small-txt')
                            platform = '未知平台'
                            hot_value = ''
                            if small_txt:
                                text = small_txt.get_text(strip=True)
                                # 用分隔符 ‧ 或 · 分割
                                parts = re.split(r'[‧·]', text)
                                if len(parts) >= 1:
                                    platform = parts[0].strip()
                                if len(parts) >= 2:
                                    hot_value = parts[1].strip()

                            news_items.append({
                                'rank': rank,
                                'title': title,
                                'url': link,
                                'hot_value': hot_value,
                                'platform': platform,  # 全榜特有：记录平台
                            })
                        except Exception as e:
                            logger.warning(f"全榜解析行失败: {e}")
                else:
                    # 1) 优先解析表格结构（大多数节点都在 table.table 内）
                    table = soup.find('table', class_='table')
                    if table:
                        rows = table.find_all('tr')[1:]  # 跳过表头
                        for idx, row in enumerate(rows, 1):
                            try:
                                cols = row.find_all('td')

                                # 排名列：取首个纯数字单元格，缺省用 idx
                                rank_text = next((c.get_text(strip=True).rstrip('.') for c in cols if c.get_text(strip=True).rstrip('.').isdigit()), "")
                                rank = int(rank_text) if rank_text else idx

                                # 标题列：行内任意有文本的链接（跳过纯图标链接）
                                title_tag = None
                                for a in row.find_all('a', href=True):
                                    text = a.get_text(strip=True)
                                    if text:
                                        title_tag = a
                                        break
                                if not title_tag:
                                    continue

                                title = title_tag.get_text(strip=True)
                                link = title_tag.get('href', '')
                                if link.startswith('/link?'):
                                    link = f"{self.base_url}{link}"

                                # 热度/描述：优先 item-desc / item-extra，再兜底最后一列文本
                                desc = row.select_one('.item-desc')
                                extra = row.select_one('.item-extra')
                                hot_parts = []
                                if desc:
                                    hot_parts.append(desc.get_text(strip=True))
                                if extra:
                                    hot_parts.append(extra.get_text(strip=True))
                                # 常见位置：最后一列或带 hot/heat/count 的元素
                                if not hot_parts and cols:
                                    # Weibo 等场景：热度在 class="ws" 的单元格，或最后一列
                                    ws_td = row.find('td', class_='ws')
                                    if ws_td:
                                        hot_parts.append(ws_td.get_text(strip=True))
                                    else:
                                        hot_parts.append(cols[-1].get_text(strip=True))
                                if not hot_parts:
                                    # 再尝试匹配 class 含 hot/heat/count/热度
                                    hot_span = row.find(class_=re.compile(r"hot|heat|count|热度", re.IGNORECASE))
                                    if hot_span:
                                        hot_parts.append(hot_span.get_text(strip=True))
                                hot_value = " | ".join([p for p in hot_parts if p])

                                if not hot_value:
                                    logger.debug(f"{source_name} 缺少热度值，rank={rank}, raw='{row.get_text(' ', strip=True)[:160]}'")

                                news_items.append({
                                    'rank': rank,
                                    'title': title,
                                    'url': link,
                                    'hot_value': hot_value,
                                })
                            except Exception as e:
                                logger.warning(f"解析表格行失败: {e}")

                    # 2) 回退解析：部分节点采用列表结构，抓取含 itemid 的链接（TopHub 列表型模板）
                    if not news_items:
                        anchors = soup.select('a[itemid]') or soup.select('a[href*="/link?"]')
                        for idx, a in enumerate(anchors, 1):
                            try:
                                title = a.get_text(strip=True)
                                if not title:
                                    continue
                                link = a.get('href', '')
                                if link.startswith('/link?'):
                                    link = f"{self.base_url}{link}"
                                hot_desc = ""
                                hot_node = a.find_next(class_='item-desc') or a.find_next('span')
                                if hot_node:
                                    hot_desc = hot_node.get_text(strip=True)
                                if not hot_desc:
                                    siblings_text = a.parent.get_text(" ", strip=True) if a.parent else ""
                                    hot_desc = siblings_text
                                news_items.append({
                                    'rank': idx,
                                    'title': title,
                                    'url': link,
                                    'hot_value': hot_desc,
                                })
                            except Exception as e:
                                logger.warning(f"解析列表节点失败: {e}")

                logger.info(f"✓ {source_name}: 成功获取 {len(news_items)} 条新闻")
                
                return {
                    'source_id': source_id,
                    'source_name': source_name,
                    'category': source_info['category'],
                    'status': 'success',
                    'news_count': len(news_items),
                    'news_items': news_items,
                    'timestamp': datetime.now().isoformat()
                }
                
        except httpx.TimeoutException:
            logger.error(f"✗ {source_name}: 请求超时")
            return {
                'source_id': source_id,
                'source_name': source_name,
                'status': 'timeout',
                'error': '请求超时',
                'news_items': [],
                'timestamp': datetime.now().isoformat()
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"✗ {source_name}: HTTP错误 {e.response.status_code}")
            return {
                'source_id': source_id,
                'source_name': source_name,
                'status': 'http_error',
                'error': f'HTTP {e.response.status_code}',
                'news_items': [],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.exception(f"✗ {source_name}: 未知错误 - {e}")
            return {
                'source_id': source_id,
                'source_name': source_name,
                'status': 'error',
                'error': str(e),
                'news_items': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def collect_news(self, source_ids: Optional[List[str]] = None, force_refresh: bool = False) -> Dict:
        """
        收集热点新闻
        
        Args:
            source_ids: 指定要收集的榜单ID列表，None表示收集所有支持的榜单
            force_refresh: 是否强制刷新（忽略缓存）
            
        Returns:
            包含收集结果的字典
        """
        # 如果不强制刷新，尝试从缓存读取
        if not force_refresh and self.use_cache and self.cache_service:
            cached_data = self.cache_service.get_cached_data()
            if cached_data:
                logger.info("📦 使用缓存数据")
                return cached_data
        
        logger.info("=" * 80)
        logger.info("🚀 开始从 TopHub 收集全网热点新闻...")
        logger.info(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 选择要收集的榜单
        if source_ids is None:
            source_ids = list(TOPHUB_SOURCES.keys())
        
        logger.info(f"📊 将从 {len(source_ids)} 个榜单收集数据:")
        for source_id in source_ids:
            source_name = TOPHUB_SOURCES.get(source_id, {}).get('name', source_id)
            logger.info(f"   - {source_name}")
        logger.info("=" * 80)
        
        try:
            # 并发获取所有榜单的新闻（但添加适当延迟避免被封）
            results = []
            for source_id in source_ids:
                result = await self.fetch_source_news(source_id)
                results.append(result)
                # 避免请求过快
                await asyncio.sleep(0.5)
            
            # 统计信息
            successful_sources = sum(1 for r in results if r['status'] == 'success')
            total_news = sum(r.get('news_count', 0) for r in results)
            
            # 整理所有新闻为统一格式
            all_news = []
            for result in results:
                if result['status'] == 'success':
                    for item in result['news_items']:
                        hot_val = item['hot_value']
                        # 抖音热榜: 优先提取 "12345次播放" 模式
                        play_match = re.search(r'([\d,\.]+\s*次播放)', hot_val)
                        if play_match:
                            hot_val = play_match.group(1).strip()
                        elif '|' in hot_val or '｜' in hot_val:
                            parts = re.split(r'[|｜]', hot_val)
                            if parts:
                                hot_val = parts[-1].strip()

                        news_obj = {
                            'id': f"{result['source_id']}_{item['rank']}",
                            'title': item['title'],
                            'url': item['url'],
                            'hot_value': hot_val,
                            'rank': item['rank'],
                            'source': result['source_name'],
                            'source_id': result['source_id'],
                            'category': result['category'],
                        }
                        
                        # 全榜特有字段：如果item中有platform字段，保留它
                        if 'platform' in item:
                            news_obj['platform'] = item['platform']
                            logger.info(f"✓ 添加platform: {item['platform']}, item.keys={list(item.keys())}")
                        else:
                            logger.info(f"✗ 无platform字段, item.keys={list(item.keys())}")
                        
                        all_news.append(news_obj)
            
            # 打印统计信息
            logger.info("=" * 80)
            logger.info(f"📈 收集统计:")
            logger.info(f"   总榜单数: {len(results)}")
            logger.info(f"   成功数: {successful_sources}")
            logger.info(f"   总新闻数: {total_news}")
            logger.info(f"   已整理: {len(all_news)}")
            logger.info("=" * 80)
            
            result_data = {
                'success': True,
                'news_list': all_news,
                'raw_results': results,
                'successful_sources': successful_sources,
                'total_sources': len(results),
                'total_news': total_news,
                'collection_time': datetime.now().isoformat(),
                'from_cache': False,
            }
            
            # 保存到缓存
            if self.use_cache and self.cache_service:
                self.cache_service.save_to_cache(result_data)
            
            return result_data
            
        except Exception as e:
            logger.exception(f"❌ 收集新闻失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'news_list': [],
                'total_news': 0
            }


# 全局实例
tophub_collector = TopHubCollector()
