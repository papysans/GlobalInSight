#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点新闻定时任务调度器
负责定时执行热点新闻收集任务
"""

import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.services.tophub_collector import tophub_collector


class HotNewsScheduler:
    """热点新闻定时任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.last_run_time: Optional[datetime] = None
        self.last_result: Optional[dict] = None
    
    def start(self, interval_hours: Optional[int] = None):
        """
        启动定时任务
        
        Args:
            interval_hours: 刷新间隔（小时），None 则从配置读取
        """
        if self.is_running:
            logger.warning("定时任务已经在运行中")
            return
        
        # 从配置读取刷新间隔
        if interval_hours is None:
            from app.config import settings
            interval_hours = settings.HOT_NEWS_CONFIG.get("fetch_interval_hours", 4)
        
        self.scheduler = AsyncIOScheduler()
        
        # 每隔指定小时数执行一次
        self.scheduler.add_job(
            self._collect_news_job,
            trigger='interval',
            hours=interval_hours,
            id='hot_news_collection',
            name=f'热点新闻收集任务（每{interval_hours}小时）',
            replace_existing=True,
            next_run_time=None,  # 立即执行第一次
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"热点新闻定时任务已启动，将每 {interval_hours} 小时执行一次")
        logger.info(f"首次执行将在启动后立即开始")
    
    def stop(self):
        """停止定时任务"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("热点新闻定时任务已停止")
    
    async def _collect_news_job(self):
        """定时任务执行函数"""
        logger.info("=" * 80)
        logger.info("开始执行定时热点新闻收集任务...")
        logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            result = await tophub_collector.collect_news()
            self.last_run_time = datetime.now()
            self.last_result = result
            
            if result['success']:
                logger.info(f"✅ 热点新闻收集完成！共获取 {result['total_news']} 条新闻")
                logger.info(f"   成功源数: {result['successful_sources']}/{result['total_sources']}")
            else:
                logger.error(f"❌ 热点新闻收集失败: {result.get('error', '未知错误')}")
        except Exception as e:
            logger.exception(f"定时任务执行出错: {e}")
            self.last_result = {
                'success': False,
                'error': str(e)
            }
        
        logger.info("=" * 80)
    
    async def run_once(self):
        """立即执行一次收集任务（用于测试或手动触发）"""
        logger.info("手动触发热点新闻收集任务...")
        await self._collect_news_job()
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            'is_running': self.is_running,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_result': self.last_result
        }


# 全局实例
hot_news_scheduler = HotNewsScheduler()
