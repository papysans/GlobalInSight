#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点新闻缓存存储服务
支持定时爬取、缓存管理、数据持久化
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger


class HotNewsCacheService:
    """热点新闻缓存服务"""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初始化缓存服务
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存 - 改为字典，支持多个缓存键
        self._memory_caches: Dict[str, Dict] = {}  # key -> cached_data
        self._cache_times: Dict[str, datetime] = {}  # key -> cache_time
        
        # 缓存过期时间（分钟）- 从配置读取，默认 4 小时
        from app.config import settings
        self.cache_expiry_minutes = settings.HOT_NEWS_CONFIG.get("cache_ttl_minutes", 240)
    
    def _get_cache_file_path(self, cache_key: str = "default") -> Path:
        """获取缓存文件路径（按日期和缓存键）"""
        today = datetime.now().strftime("%Y-%m-%d")
        if cache_key == "default":
            return self.cache_dir / f"hot_news_{today}.json"
        return self.cache_dir / f"hot_news_{cache_key}_{today}.json"
    
    def is_cache_expired(self, cache_key: str = "default") -> bool:
        """检查缓存是否过期"""
        if cache_key not in self._cache_times:
            return True
        
        cache_time = self._cache_times[cache_key]
        expiry_time = cache_time + timedelta(minutes=self.cache_expiry_minutes)
        return datetime.now() > expiry_time
    
    def get_cached_data(self, cache_key: str = "default") -> Optional[Dict]:
        """
        获取缓存数据
        
        Args:
            cache_key: 缓存键（如 'tophub', 'hn'）
        
        Returns:
            缓存的新闻数据，如果缓存不存在或已过期则返回None
        """
        # 优先从内存读取
        if cache_key in self._memory_caches and not self.is_cache_expired(cache_key):
            cache_time = self._cache_times[cache_key]
            logger.info(f"✓ 从内存缓存加载数据 [{cache_key}]（缓存时间: {cache_time.strftime('%H:%M:%S')}）")
            return self._memory_caches[cache_key]
        
        # 尝试从文件读取
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查文件缓存是否过期
                cache_time = datetime.fromisoformat(data.get('collection_time', ''))
                expiry_time = cache_time + timedelta(minutes=self.cache_expiry_minutes)
                
                if datetime.now() < expiry_time:
                    self._memory_caches[cache_key] = data
                    self._cache_times[cache_key] = cache_time
                    logger.info(f"✓ 从文件缓存加载数据 [{cache_key}]（缓存时间: {cache_time.strftime('%H:%M:%S')}）")
                    return data
                else:
                    logger.info(f"⚠ 文件缓存已过期 [{cache_key}]（缓存时间: {cache_time.strftime('%H:%M:%S')}）")
                    
            except Exception as e:
                logger.error(f"读取缓存文件失败 [{cache_key}]: {e}")
        
        return None
    
    def save_to_cache(self, data: Dict, cache_key: str = "default") -> bool:
        """
        保存数据到缓存
        
        Args:
            data: 要缓存的新闻数据
            cache_key: 缓存键（如 'tophub', 'hn'）
            
        Returns:
            是否保存成功
        """
        try:
            # 保存到内存
            self._memory_caches[cache_key] = data
            self._cache_times[cache_key] = datetime.now()
            
            # 保存到文件
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ 数据已缓存到内存和文件 [{cache_key}]: {cache_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败 [{cache_key}]: {e}")
            return False
    
    def clear_cache(self, cache_key: Optional[str] = None):
        """
        清除缓存
        
        Args:
            cache_key: 要清除的缓存键，None表示清除所有
        """
        if cache_key:
            # 清除指定缓存
            self._memory_caches.pop(cache_key, None)
            self._cache_times.pop(cache_key, None)
            logger.info(f"✓ 已清除缓存 [{cache_key}]")
        else:
            # 清除所有缓存
            self._memory_caches.clear()
            self._cache_times.clear()
            logger.info("✓ 已清除所有缓存")
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        keys = sorted(list(self._memory_caches.keys()))
        latest_time = None
        if self._cache_times:
            latest_time = max(self._cache_times.values())
        return {
            "has_cache": bool(self._memory_caches),
            "cache_keys": keys,
            "latest_cache_time": latest_time.isoformat() if latest_time else None,
            "expiry_minutes": self.cache_expiry_minutes,
        }
    
    def cleanup_old_caches(self, keep_days: int = 7):
        """
        清理旧的缓存文件
        
        Args:
            keep_days: 保留最近几天的缓存
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for cache_file in self.cache_dir.glob("hot_news_*.json"):
                try:
                    # 从文件名提取日期
                    date_str = cache_file.stem.replace("hot_news_", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        cache_file.unlink()
                        logger.info(f"✓ 删除旧缓存文件: {cache_file.name}")
                        
                except Exception as e:
                    logger.warning(f"处理缓存文件失败 {cache_file}: {e}")
            
        except Exception as e:
            logger.error(f"清理旧缓存失败: {e}")


# 全局缓存服务实例
hot_news_cache = HotNewsCacheService()
