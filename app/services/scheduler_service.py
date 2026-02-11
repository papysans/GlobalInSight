"""
定时任务调度服务 - SchedulerService

基于 APScheduler AsyncIOScheduler 实现：
1. 每日速报定时生成（默认 18:00 收盘后，可配置）
2. 每小时增量新闻检查（检测重大变化时触发速报更新）
3. 支持从设置页面动态修改定时配置

后台任务使用独立 Session（通过 async_session_factory()），不依赖请求上下文。

Requirements: 5.9
"""

from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger


class SchedulerService:
    """定时任务调度服务"""

    # 任务 ID 常量
    JOB_DAILY_REPORT = "daily_report_generation"
    JOB_NEWS_CHECK = "hourly_news_check"
    JOB_SENTIMENT_ANALYSIS = "sentiment_analysis"

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False

        # 配置
        self._daily_hour = 18
        self._daily_minute = 0
        self._incremental_check_enabled = True
        self._sentiment_interval_hours = 2

        # 状态
        self.last_daily_report_time: Optional[datetime] = None
        self.last_news_check_time: Optional[datetime] = None
        self.last_sentiment_analysis_time: Optional[datetime] = None
        self.last_daily_report_error: Optional[str] = None
        self.last_news_check_error: Optional[str] = None
        self.last_sentiment_analysis_error: Optional[str] = None

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------

    def start(self, daily_hour: int = 18, daily_minute: int = 0):
        """启动调度器，注册定时任务。

        Args:
            daily_hour: 每日速报生成时间（小时，0-23，默认 18）
            daily_minute: 每日速报生成时间（分钟，0-59，默认 0）
        """
        if self.is_running:
            logger.warning("SchedulerService: 调度器已在运行中")
            return

        self._daily_hour = daily_hour
        self._daily_minute = daily_minute

        self.scheduler = AsyncIOScheduler()

        # 任务 1: 每日速报定时生成
        self.scheduler.add_job(
            self._daily_report_job,
            trigger=CronTrigger(hour=daily_hour, minute=daily_minute),
            id=self.JOB_DAILY_REPORT,
            name="每日速报定时生成",
            replace_existing=True,
        )

        # 任务 2: 每小时增量新闻检查
        if self._incremental_check_enabled:
            self.scheduler.add_job(
                self._hourly_news_check_job,
                trigger=IntervalTrigger(hours=1),
                id=self.JOB_NEWS_CHECK,
                name="每小时增量新闻检查",
                replace_existing=True,
            )

        # 任务 3: 散户情绪采集与分析（默认每 2 小时）
        self.scheduler.add_job(
            self._sentiment_analysis_job,
            trigger=IntervalTrigger(hours=self._sentiment_interval_hours),
            id=self.JOB_SENTIMENT_ANALYSIS,
            name="散户情绪采集与分析",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        logger.info(
            f"SchedulerService: 调度器已启动 — "
            f"每日速报 {daily_hour:02d}:{daily_minute:02d}, "
            f"增量检查 {'开启' if self._incremental_check_enabled else '关闭'}, "
            f"情绪采集 每{self._sentiment_interval_hours}小时"
        )

    def stop(self):
        """停止调度器"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("SchedulerService: 调度器已停止")

    # ------------------------------------------------------------------
    # 动态配置更新
    # ------------------------------------------------------------------

    def update_schedule(self, hour: int, minute: int):
        """动态修改每日速报生成时间。

        Args:
            hour: 新的小时（0-23）
            minute: 新的分钟（0-59）
        """
        self._daily_hour = hour
        self._daily_minute = minute

        if self.scheduler and self.is_running:
            self.scheduler.reschedule_job(
                self.JOB_DAILY_REPORT,
                trigger=CronTrigger(hour=hour, minute=minute),
            )
            logger.info(
                f"SchedulerService: 每日速报时间已更新为 {hour:02d}:{minute:02d}"
            )

    def set_incremental_check_enabled(self, enabled: bool):
        """启用或禁用每小时增量检查。"""
        self._incremental_check_enabled = enabled

        if not self.scheduler or not self.is_running:
            return

        if enabled:
            # 添加或恢复任务
            existing = self.scheduler.get_job(self.JOB_NEWS_CHECK)
            if not existing:
                self.scheduler.add_job(
                    self._hourly_news_check_job,
                    trigger=IntervalTrigger(hours=1),
                    id=self.JOB_NEWS_CHECK,
                    name="每小时增量新闻检查",
                    replace_existing=True,
                )
            else:
                self.scheduler.resume_job(self.JOB_NEWS_CHECK)
            logger.info("SchedulerService: 增量新闻检查已启用")
        else:
            existing = self.scheduler.get_job(self.JOB_NEWS_CHECK)
            if existing:
                self.scheduler.pause_job(self.JOB_NEWS_CHECK)
            logger.info("SchedulerService: 增量新闻检查已暂停")

    def update_sentiment_schedule(self, interval_hours: int = 2):
        """动态修改情绪采集频率。

        Args:
            interval_hours: 采集间隔（小时，1-24，默认2）
        """
        if interval_hours < 1:
            interval_hours = 1
        if interval_hours > 24:
            interval_hours = 24

        self._sentiment_interval_hours = interval_hours

        if self.scheduler and self.is_running:
            self.scheduler.reschedule_job(
                self.JOB_SENTIMENT_ANALYSIS,
                trigger=IntervalTrigger(hours=interval_hours),
            )
            logger.info(
                f"SchedulerService: 情绪采集频率已更新为每 {interval_hours} 小时"
            )

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """获取调度器当前状态"""
        next_daily = None
        next_check = None
        next_sentiment = None

        if self.scheduler and self.is_running:
            daily_job = self.scheduler.get_job(self.JOB_DAILY_REPORT)
            if daily_job and daily_job.next_run_time:
                next_daily = daily_job.next_run_time.isoformat()

            check_job = self.scheduler.get_job(self.JOB_NEWS_CHECK)
            if check_job and check_job.next_run_time:
                next_check = check_job.next_run_time.isoformat()

            sentiment_job = self.scheduler.get_job(self.JOB_SENTIMENT_ANALYSIS)
            if sentiment_job and sentiment_job.next_run_time:
                next_sentiment = sentiment_job.next_run_time.isoformat()

        return {
            "is_running": self.is_running,
            "daily_report_time": f"{self._daily_hour:02d}:{self._daily_minute:02d}",
            "incremental_check_enabled": self._incremental_check_enabled,
            "sentiment_interval_hours": self._sentiment_interval_hours,
            "next_daily_report": next_daily,
            "next_news_check": next_check,
            "next_sentiment_analysis": next_sentiment,
            "last_daily_report_time": (
                self.last_daily_report_time.isoformat()
                if self.last_daily_report_time
                else None
            ),
            "last_news_check_time": (
                self.last_news_check_time.isoformat()
                if self.last_news_check_time
                else None
            ),
            "last_sentiment_analysis_time": (
                self.last_sentiment_analysis_time.isoformat()
                if self.last_sentiment_analysis_time
                else None
            ),
            "last_daily_report_error": self.last_daily_report_error,
            "last_news_check_error": self.last_news_check_error,
            "last_sentiment_analysis_error": self.last_sentiment_analysis_error,
        }

    # ------------------------------------------------------------------
    # 定时任务实现
    # ------------------------------------------------------------------

    async def _daily_report_job(self):
        """每日速报定时生成任务"""
        logger.info("=" * 60)
        logger.info("SchedulerService: 开始执行每日速报定时生成...")
        logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            from app.services.stock_news_collector import stock_news_collector
            from app.services.social_content_generator import social_content_generator

            # 1. 采集最新资讯
            news_result = await stock_news_collector.collect_news(force_refresh=True)
            news_items = news_result.items[:20] if news_result.items else []

            if not news_items:
                logger.warning("SchedulerService: 无资讯数据，跳过速报生成")
                self.last_daily_report_time = datetime.now()
                return

            # 2. 生成各平台速报
            reports = await social_content_generator.generate_daily_report(news_items)

            # 3. 持久化到数据库
            for content in reports.values():
                await social_content_generator._persist_content(content)

            self.last_daily_report_time = datetime.now()
            self.last_daily_report_error = None

            logger.info(
                f"✅ 每日速报生成完成，共 {len(reports)} 个平台: "
                f"{', '.join(reports.keys())}"
            )

        except Exception as e:
            self.last_daily_report_error = str(e)
            self.last_daily_report_time = datetime.now()
            logger.error(f"❌ 每日速报生成失败: {e}")

    async def _hourly_news_check_job(self):
        """每小时增量新闻检查任务

        采集最新资讯，通过 NewsChangeDetector 检测是否发生重大变化，
        若检测到变化则自动触发速报更新。
        """
        logger.info("SchedulerService: 执行增量新闻检查...")

        try:
            from app.services.stock_news_collector import stock_news_collector
            from app.services.news_change_detector import news_change_detector
            from app.services.social_content_generator import social_content_generator

            # 1. 采集最新资讯（强制刷新以获取最新数据并更新缓存）
            news_result = await stock_news_collector.collect_news(force_refresh=True)
            news_items = news_result.items if news_result.items else []

            # 1b. 同时刷新热榜聚类数据
            try:
                await stock_news_collector.collect_hot_news(force_refresh=True)
            except Exception as hot_err:
                logger.warning(f"SchedulerService: 热榜聚类刷新失败: {hot_err}")

            if not news_items:
                logger.info("SchedulerService: 增量检查 — 无资讯数据")
                self.last_news_check_time = datetime.now()
                return

            # 2. 检测变化
            detection = news_change_detector.detect_changes(news_items)
            self.last_news_check_time = datetime.now()
            self.last_news_check_error = None

            if not detection.has_significant_change:
                logger.info("SchedulerService: 增量检查 — 无重大变化")
                return

            # 3. 检测到重大变化，自动更新速报
            logger.info(
                f"SchedulerService: 检测到重大变化，触发速报更新 — "
                f"规则: {', '.join(detection.triggered_rules)}"
            )

            reports = await social_content_generator.generate_daily_report(
                news_items[:20]
            )
            # 持久化到数据库
            for content in reports.values():
                await social_content_generator._persist_content(content)
            logger.info(
                f"✅ 增量速报更新完成，共 {len(reports)} 个平台"
            )

        except Exception as e:
            self.last_news_check_error = str(e)
            self.last_news_check_time = datetime.now()
            logger.error(f"❌ 增量新闻检查失败: {e}")

    async def _sentiment_analysis_job(self):
        """定时执行散户情绪采集和分析。

        采集大盘综合讨论区评论 → LLM 分析 → 采集聚合指标 → 计算综合指数 → 持久化快照。
        """
        logger.info("=" * 60)
        logger.info("SchedulerService: 开始执行散户情绪采集与分析...")
        logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            from app.services.sentiment_analyzer import SentimentAnalyzer

            analyzer = SentimentAnalyzer()

            # 执行大盘情绪分析
            snapshot = await analyzer.run_analysis_cycle(
                stock_code=None,
                time_window_hours=24,
            )

            self.last_sentiment_analysis_time = datetime.now()
            self.last_sentiment_analysis_error = None

            if snapshot:
                logger.info(
                    f"✅ 情绪分析完成 — 综合指数: {snapshot.index_value:.1f} "
                    f"({snapshot.label}), 样本量: {snapshot.sample_count}"
                )
            else:
                logger.warning("SchedulerService: 情绪分析返回空结果")

        except Exception as e:
            self.last_sentiment_analysis_error = str(e)
            self.last_sentiment_analysis_time = datetime.now()
            logger.error(f"❌ 情绪采集与分析失败: {e}")


# ---------------------------------------------------------------------------
# 全局实例
# ---------------------------------------------------------------------------

scheduler_service = SchedulerService()
