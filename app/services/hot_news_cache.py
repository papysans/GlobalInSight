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
        
        # 内存缓存
        self._memory_cache: Optional[Dict] = None
        self._cache_time: Optional[datetime] = None
        
        # 缓存过期时间（分钟）
        self.cache_expiry_minutes = 30
    
    def _get_cache_file_path(self) -> Path:
        """获取缓存文件路径（按日期）"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.cache_dir / f"hot_news_{today}.json"
    
    def is_cache_expired(self) -> bool:
        """检查缓存是否过期"""
        if self._cache_time is None:
            return True
        
        expiry_time = self._cache_time + timedelta(minutes=self.cache_expiry_minutes)
        return datetime.now() > expiry_time
    
    def get_cached_data(self) -> Optional[Dict]:
        """
        获取缓存数据
        
        Returns:
            缓存的新闻数据，如果缓存不存在或已过期则返回None
        """
        # 优先从内存读取
        if self._memory_cache and not self.is_cache_expired():
            logger.info(f"✓ 从内存缓存加载数据（缓存时间: {self._cache_time.strftime('%H:%M:%S')}）")
            return self._memory_cache
        
        # 尝试从文件读取
        cache_file = self._get_cache_file_path()
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查文件缓存是否过期
                cache_time = datetime.fromisoformat(data.get('collection_time', ''))
                expiry_time = cache_time + timedelta(minutes=self.cache_expiry_minutes)
                
                if datetime.now() < expiry_time:
                    self._memory_cache = data
                    self._cache_time = cache_time
                    logger.info(f"✓ 从文件缓存加载数据（缓存时间: {cache_time.strftime('%H:%M:%S')}）")
                    return data
                else:
                    logger.info(f"⚠ 文件缓存已过期（缓存时间: {cache_time.strftime('%H:%M:%S')}）")
                    
            except Exception as e:
                logger.error(f"读取缓存文件失败: {e}")
        
        return None
    
    def save_to_cache(self, data: Dict) -> bool:
        """
        保存数据到缓存
        
        Args:
            data: 要缓存的新闻数据
            
        Returns:
            是否保存成功
        """
        try:
            # 保存到内存
            self._memory_cache = data
            self._cache_time = datetime.now()
            
            # 保存到文件
            cache_file = self._get_cache_file_path()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ 数据已缓存到内存和文件: {cache_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    def clear_cache(self):
        """清除所有缓存"""
        self._memory_cache = None
        self._cache_time = None
        logger.info("✓ 内存缓存已清除")
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            'has_cache': self._memory_cache is not None,
            'cache_time': self._cache_time.isoformat() if self._cache_time else None,
            'is_expired': self.is_cache_expired(),
            'cache_file': str(self._get_cache_file_path()),
            'expiry_minutes': self.cache_expiry_minutes,
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
