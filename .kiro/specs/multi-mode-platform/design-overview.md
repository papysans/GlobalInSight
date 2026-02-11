> 本文件是 design.md 拆分后的子文件。完整设计文档包含：
> - [design-overview.md](design-overview.md)  概述、依赖、策略、架构、数据库
> - [design-frontend.md](design-frontend.md)  前端组件、路由、状态管理
> - [design-backend-services.md](design-backend-services.md)  后端服务（爬虫、推演、内容生成、合规脱敏）
> - [design-sentiment.md](design-sentiment.md) — 散户情绪分析全链路
> - [design-data-models.md](design-data-models.md)  数据模型、正确性属性、错误处理、测试策略

# 设计文档：股票资讯与行情推演平台

## 概述

将"观潮 GlobalInSight"改造为 AI 股票内容创作平台。核心差异化在于"情绪数据驱动 + 争议性观点驱动"双引擎——系统通过混合数据源（散户评论 LLM 分析 + AKShare 聚合指标 + 百度投票 + 新闻情绪指数 + 融资融券数据）构建综合恐慌/贪婪指数，为行情推演提供市场温度参考；同时通过多头/空头 Agent 激辩生成有立场、有争议的内容，天然适合社交平台传播。情绪数据是系统的核心引擎，贯穿从数据采集到行情推演到内容生成的全链路——推演分析引用情绪指数佐证观点，社交内容融入情绪洞察增强说服力和传播力。移除现有的舆论分析功能，替换为股票热榜采集、散户情绪分析、多空激辩推演和社交内容生成。改造遵循最小改动原则：复用现有的技术架构（FastAPI + Vue 3 + 缓存机制 + LLM 集成 + 图片生成 + 小红书发布），替换业务逻辑层。

## 新增依赖

- **akshare**：免费开源 Python 财经数据接口库，作为主要数据源（pip install akshare）
- **tushare**：可选，免费层需注册获取 token（pip install tushare）
- **pypinyin**：中文拼音转换库，用于轻度脱敏的拼音缩写生成（pip install pypinyin）
- **finnhub-python**：Finnhub 官方 Python SDK，国际财经新闻采集（pip install finnhub-python）
- **newsapi-python**：NewsAPI 官方 Python 客户端，国际财经媒体新闻聚合（pip install newsapi-python）
- **alpha_vantage**：Alpha Vantage Python 封装，新闻情绪分析端点（pip install alpha_vantage）
- **feedparser**：RSS/Atom feed 解析库，用于 Google News RSS 和 GDELT RSS 采集（pip install feedparser）
- **yfinance**：Yahoo Finance 非官方 Python 库，获取分析师推荐和目标价（pip install yfinance）
- **apscheduler**：Python 定时任务调度库，用于每日速报定时生成和增量更新检查（pip install apscheduler）
- **httpx[socks]**：httpx 的 SOCKS 代理支持扩展，用于散户情绪爬虫的代理池轮换（pip install httpx[socks]）
- **echarts / vue-echarts**：前端图表库，用于情绪指数 K 线风格时序图表和仪表盘可视化（npm install echarts vue-echarts）
- **vue-router**：Vue 3 官方路由库，用于前端 SPA 路由（npm install vue-router@4）
- **SQLAlchemy**：Python ORM 库，用于数据库模型定义和查询（pip install sqlalchemy）
- **asyncpg**：PostgreSQL 异步驱动，配合 SQLAlchemy 异步引擎使用（pip install asyncpg）
- **alembic**：数据库迁移工具，管理 schema 变更（pip install alembic）

## 市场范围说明

本系统以 A 股（沪深两市）和港股为主要覆盖市场。投行研报数据源虽然部分来自国际平台（如 Finnhub、Yahoo Finance），但采集时应优先筛选与中国市场相关的内容（A 股、港股、中概股）。国际财经新闻采集同样侧重与中国市场相关的全球动态。

### 港股数据源方案

当前版本的数据源（AKShare、东方财富股吧、同花顺、百度投票等）主要面向 A 股市场。港股数据源在初始版本中采用以下策略：

**资讯采集（Phase 1 可用）：**
- AKShare `stock_hk_spot_em()`：港股实时行情数据
- AKShare `stock_hk_hist()`：港股历史行情
- Finnhub / NewsAPI / Alpha Vantage：国际财经新闻天然覆盖港股（通过 `.HK` 后缀 symbol 筛选）
- Yahoo Finance `yfinance`：港股分析师评级（symbol 格式如 `0700.HK`）

**情绪分析（Phase 3 部分可用）：**
- 雪球社区：天然覆盖港股讨论（雪球用户活跃讨论港股标的）
- AKShare `stock_hot_follow_xq()` / `stock_hot_tweet_xq()`：雪球热度数据包含港股
- 东方财富股吧：部分港股有对应股吧（如"腾讯控股吧"）

**暂不支持（标注为后续版本）：**
- 百度股市通投票（`stock_zh_vote_baidu`）：仅支持 A 股，港股无此数据
- 同花顺社区评论：港股讨论区覆盖有限
- 融资融券数据：港股融资融券机制不同，AKShare 暂无对应接口
- 港股板块映射表：需额外构建港股行业分类映射（AKShare `stock_hk_industry_spot_em()` 可提供基础数据）

> **结论**：初始版本港股以资讯采集和投行研报为主，情绪分析依赖雪球社区数据。港股专属的情绪数据源（百度投票、融资融券等）标注为"后续版本支持"。计算港股个股情绪指数时，不可用的分项数据源权重自动重分配给可用源。

## AKShare 接口可用性监控策略

AKShare 是社区维护的开源库，上游网站改版可能导致接口失效。系统应在启动时和运行时对 AKShare 接口进行可用性探测和监控：

### 启动时接口探测

```python
class AKShareHealthChecker:
    """AKShare 接口可用性探测器，应用启动时自动检测各接口状态"""
    
    # 系统依赖的所有 AKShare 接口清单
    REQUIRED_INTERFACES = {
        "stock_news_em": {"service": "StockNewsCollector", "critical": True},
        "stock_hot_rank_em": {"service": "StockNewsCollector", "critical": False},
        "stock_board_industry_name_em": {"service": "ComplianceService", "critical": True},
        "stock_board_industry_cons_em": {"service": "ComplianceService", "critical": True},
        "stock_zh_a_spot_em": {"service": "ComplianceService", "critical": False},
        "stock_comment_em": {"service": "MixedSentimentDataService", "critical": False},
        "stock_comment_detail_scrd_focus_em": {"service": "MixedSentimentDataService", "critical": False},
        "stock_hot_rank_em": {"service": "MixedSentimentDataService", "critical": False},
        "stock_hot_keyword_em": {"service": "MixedSentimentDataService", "critical": False},
        "stock_zh_vote_baidu": {"service": "MixedSentimentDataService", "critical": False},
        "index_news_sentiment_scope": {"service": "MixedSentimentDataService", "critical": False},
        "stock_margin_detail_szse": {"service": "MixedSentimentDataService", "critical": False},
        "stock_margin_detail_sse": {"service": "MixedSentimentDataService", "critical": False},
        "stock_hot_follow_xq": {"service": "MixedSentimentDataService", "critical": False},
        "stock_hot_tweet_xq": {"service": "MixedSentimentDataService", "critical": False},
    }
    
    async def probe_all(self) -> Dict[str, bool]:
        """启动时探测所有接口，返回 {接口名: 是否可用}"""
        results = {}
        for func_name, meta in self.REQUIRED_INTERFACES.items():
            try:
                func = getattr(ak, func_name)
                await asyncio.to_thread(func)  # 尝试调用（部分接口需要参数，用 try/except 捕获）
                results[func_name] = True
            except Exception as e:
                results[func_name] = False
                level = logging.WARNING if meta["critical"] else logging.INFO
                logger.log(level, f"AKShare 接口 {func_name} 不可用: {e}")
        return results
```

### 运行时独立降级

每个 AKShare 接口调用点必须有独立的 `try/except` + 降级逻辑：
- `StockNewsCollector`：AKShare 接口失败时跳过该数据源，使用其他源数据
- `ComplianceService`：映射表构建失败时使用本地缓存或空映射 + 通用回退描述
- `MixedSentimentDataService`：各聚合指标接口独立 `try/except`，失败返回 `None`，权重自动重分配

## AKShare 异步调用策略

AKShare 是同步阻塞库（内部使用 requests），在 FastAPI 异步环境中直接调用会阻塞事件循环。所有 AKShare 调用必须通过 `asyncio.to_thread()` 包装为异步调用：

```python
import asyncio
import akshare as ak

async def fetch_akshare_data():
    """所有 AKShare 调用统一使用 asyncio.to_thread() 包装"""
    # 正确方式：不阻塞事件循环
    df = await asyncio.to_thread(ak.stock_news_em)
    hot_rank = await asyncio.to_thread(ak.stock_hot_rank_em)
    board_data = await asyncio.to_thread(ak.stock_board_industry_name_em)
    return df, hot_rank, board_data
```

此策略适用于所有使用 AKShare 的服务：StockNewsCollector、ComplianceService（映射表构建）、MixedSentimentDataService（聚合指标采集）等。

## SQLAlchemy 异步 Session 管理策略

### 请求级 Session（API 端点使用）

API 端点通过 FastAPI 依赖注入获取请求级 Session，请求结束自动关闭：

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/platform_db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：请求级 Session，请求结束自动关闭"""
    async with async_session_factory() as session:
        yield session
```

### 独立 Session（后台任务/定时任务使用）

定时任务和后台任务不在请求上下文中，需要创建独立的 Session：

```python
# 在 SchedulerService、SentimentAnalyzer 等后台服务中
async def run_background_task():
    """后台任务使用独立 Session，手动管理生命周期"""
    async with async_session_factory() as session:
        async with session.begin():
            # 执行数据库操作
            result = await session.execute(...)
            session.add(new_record)
        # session.begin() 的 context manager 自动 commit 或 rollback
```

### Session 使用原则

1. API 端点：通过 `Depends(get_db)` 注入，一个请求一个 Session
2. 定时任务（APScheduler）：每次任务执行创建独立 Session，任务结束关闭
3. SSE 流式推演：在推演开始时创建 Session，推演结束时关闭（不跨多个请求）
4. 避免全局共享 Session 实例，防止并发冲突

## 推演重试策略

SSE 流式推演是一个多步骤长流程（9 步），当 SSE 连接断开时（如网络中断、浏览器刷新），系统采用"从头开始"策略：

- **重试 = 从头开始**：前端重新发起 `POST /api/stock/analyze` 请求，后端从 Step 0 重新执行完整推演流程
- **不实现断点续传**：推演各步骤之间存在上下文依赖（如 Step 5 多空交锋依赖 Step 3/4 的多空观点），断点续传需要复杂的中间状态持久化，初始版本不引入此复杂度
- **已完成的推演结果可查看**：如果推演在断开前已完成并持久化到数据库，用户可通过历史记录查看完整结果，无需重新推演
- **缓存命中优化**：相同资讯组合在 60 分钟内重试时，缓存命中直接返回结果（`cache_hit=true`），无需重新调用 LLM

> **后续版本可选优化**：如果用户反馈推演中断体验差，可考虑实现步骤级持久化 + `GET /api/stock/analyze/{analysis_id}/progress` 端点，前端重连后获取已完成步骤并从断点继续。

## 工作流状态追踪（复用现有模式）

新系统保留现有 `WorkflowStatusManager` 的状态追踪模式，用于行情推演的 SSE 流式进度跟踪：

```python
# app/services/stock_workflow_status.py
# 复用现有 workflow_status.py 的设计模式
class StockWorkflowStatusManager:
    """行情推演工作流状态管理器，复用现有 WorkflowStatusManager 模式"""
    
    def __init__(self):
        self._status = {
            "running": False,
            "current_step": None,
            "progress": 0,
            "started_at": None,
            "topic": None,
            "current_agent": None,  # 当前执行的 Agent 名称
        }
        self._lock = asyncio.Lock()
    
    async def start_workflow(self, topic: str): ...
    async def update_step(self, step: str, progress: int = None, current_agent: str = None): ...
    async def finish_workflow(self): ...
    async def get_status(self) -> Dict[str, Any]: ...
    async def reset(self): ...

# 步骤进度映射
STEP_PROGRESS = {
    "sentiment_data": 3,
    "news_summary": 8,
    "impact_analysis": 18,
    "bull_agent": 30,
    "bear_agent": 42,
    "debate_agent": 58,
    "conclusion_agent": 72,
    "writer_agent": 85,
    "image_generator": 95,
}
```

## Vue Router + FastAPI SPA 部署方案

前端使用 Vue Router 的 history 模式（`createWebHistory()`），需要后端配合处理 SPA 路由。采用 FastAPI catch-all 路由方案：

```python
# app/main.py 中，在所有 API 路由注册之后添加
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 先挂载静态资源（JS/CSS/图片等）
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

# catch-all 路由：所有非 /api/ 的请求返回 index.html，由 Vue Router 处理
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("dist/index.html")
```

注意事项：
- 所有 API 路由必须以 `/api/` 前缀开头，避免与 SPA 路由冲突
- catch-all 路由必须在所有 API 路由之后注册
- 开发环境使用 Vite dev server 代理，不需要此配置
- 生产环境 `npm run build` 后将 `dist/` 目录部署到 FastAPI 服务

## 个股板块映射表冷启动策略

映射表通过 AKShare 构建，首次启动时需要处理冷启动问题：

```python
class ComplianceService:
    async def initialize_mapping(self):
        """应用启动时异步初始化映射表"""
        # 1. 优先加载本地缓存（SQLite 或 JSON 文件）
        cached = await self._load_cached_mapping()
        if cached:
            self.desensitizer.mapping = cached
            # 后台异步更新（不阻塞启动）
            asyncio.create_task(self._background_refresh_mapping())
            return
        
        # 2. 无缓存时，使用 asyncio.to_thread 调用 AKShare 构建
        try:
            mapping = await self._build_mapping_from_akshare()
            self.desensitizer.mapping = mapping
            await self._save_mapping_cache(mapping)
        except Exception as e:
            # 3. AKShare 也失败时，使用空映射 + 通用回退描述
            logger.warning(f"映射表构建失败，使用空映射: {e}")
            self.desensitizer.mapping = {}
            # 脱敏时映射表缺失条目将使用"某上市公司"通用描述
    
    async def _build_mapping_from_akshare(self):
        """通过 AKShare 构建完整映射表（使用 asyncio.to_thread）"""
        # 1. 获取行业板块列表
        boards = await asyncio.to_thread(ak.stock_board_industry_name_em)
        # 2. 逐板块获取成分股
        # 3. 获取市值数据用于排名
        # 4. 生成 desensitized_label 和 pinyin_abbr
        ...
    
    async def _background_refresh_mapping(self):
        """后台异步刷新映射表，不影响当前服务"""
        try:
            new_mapping = await self._build_mapping_from_akshare()
            self.desensitizer.mapping = new_mapping
            await self._save_mapping_cache(new_mapping)
        except Exception:
            pass  # 刷新失败不影响服务，继续使用缓存
```

冷启动策略总结：
1. 优先加载本地缓存（毫秒级）
2. 有缓存时后台异步刷新（不阻塞）
3. 无缓存时同步构建（首次启动稍慢，约 30-60 秒）
4. 构建失败时使用空映射 + 通用回退描述（"某上市公司"）

## 重大新闻变化检测规则

每小时增量检查时，使用以下规则判断是否发生"重大新闻变化"，触发速报更新：

```python
class NewsChangeDetector:
    """重大新闻变化检测器"""
    
    # 检测阈值配置
    THRESHOLDS = {
        "new_high_heat_count": 3,        # 新增热度 > 10000 的资讯数量阈值
        "heat_spike_ratio": 2.0,         # 单条资讯热度较上次检查增长倍数阈值
        "top3_change_count": 2,          # 热榜 Top3 变化数量阈值
        "new_sector_movement": True,     # 是否检测新板块异动
        "sector_heat_threshold": 5000,   # 板块异动热度阈值
        "research_upgrade_count": 2,     # 新增投行评级升级数量阈值
    }
    
    async def detect_major_changes(self, current_news, previous_news) -> Dict:
        """检测重大新闻变化，返回变化详情"""
        changes = {
            "is_major": False,
            "triggers": [],  # 触发的规则列表
        }
        
        # 规则 1: 新增高热度资讯
        new_high_heat = [n for n in current_news if n not in previous_news 
                         and n.hot_value > 10000]
        if len(new_high_heat) >= self.THRESHOLDS["new_high_heat_count"]:
            changes["triggers"].append({
                "rule": "new_high_heat",
                "detail": f"新增 {len(new_high_heat)} 条高热度资讯"
            })
        
        # 规则 2: 单条资讯热度暴涨
        for curr in current_news:
            prev = find_matching(previous_news, curr.id)
            if prev and curr.hot_value / max(prev.hot_value, 1) >= self.THRESHOLDS["heat_spike_ratio"]:
                changes["triggers"].append({
                    "rule": "heat_spike",
                    "detail": f"'{curr.title}' 热度暴涨 {curr.hot_value/prev.hot_value:.1f}x"
                })
        
        # 规则 3: 热榜 Top3 变化
        curr_top3 = set(n.id for n in current_news[:3])
        prev_top3 = set(n.id for n in previous_news[:3])
        top3_diff = len(curr_top3 - prev_top3)
        if top3_diff >= self.THRESHOLDS["top3_change_count"]:
            changes["triggers"].append({
                "rule": "top3_change",
                "detail": f"热榜 Top3 中有 {top3_diff} 条新资讯"
            })
        
        # 规则 4: 新板块异动（之前未出现的板块突然上榜）
        curr_sectors = extract_sectors(current_news)
        prev_sectors = extract_sectors(previous_news)
        new_sectors = curr_sectors - prev_sectors
        if new_sectors:
            changes["triggers"].append({
                "rule": "new_sector",
                "detail": f"新板块异动: {', '.join(new_sectors)}"
            })
        
        # 规则 5: 投行评级升级
        new_upgrades = [n for n in current_news 
                        if n.category == "research_report" 
                        and n.analyst_rating and n.analyst_rating.action == "upgrade"
                        and n not in previous_news]
        if len(new_upgrades) >= self.THRESHOLDS["research_upgrade_count"]:
            changes["triggers"].append({
                "rule": "research_upgrade",
                "detail": f"新增 {len(new_upgrades)} 条投行评级升级"
            })
        
        changes["is_major"] = len(changes["triggers"]) > 0
        return changes
```

检测规则总结：
1. 新增高热度资讯（≥3 条热度 > 10000）
2. 单条资讯热度暴涨（≥2 倍增长）
3. 热榜 Top3 大幅变化（≥2 条新上榜）
4. 新板块异动（之前未出现的板块突然上榜）
5. 投行评级升级集中出现（≥2 条新升级）

任一规则触发即视为"重大变化"，自动更新速报。

## 散户情绪爬虫详细架构

### 东方财富股吧爬虫（核心数据源）

```python
class EastMoneyCommentCrawler:
    """东方财富股吧评论爬虫
    
    采集策略：
    - 目标 URL: https://guba.eastmoney.com/list,{stock_code}.html
    - 综合讨论区: https://guba.eastmoney.com/list,zssh000001.html（上证指数吧）
    - 请求方式: HTTP GET + 解析 HTML 或调用内部 API
    - 内部 API: https://guba.eastmoney.com/interface/GetData?type=1&code={stock_code}&ps=30&p={page}
    - 反爬等级: 中等（需 Cookie + User-Agent，频率不宜过高）
    - 数据字段: 帖子标题、内容摘要、作者、发布时间、阅读数、评论数
    """
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 ...",  # 轮换 User-Agent 池
        "Referer": "https://guba.eastmoney.com/",
    }
    
    async def fetch_comments(self, stock_code, time_window_hours=24):
        # 1. 通过代理池获取代理
        # 2. 通过 Cookie 池获取 Cookie
        # 3. 请求股吧帖子列表页（分页）
        # 4. 解析帖子标题、摘要、时间
        # 5. 按时间窗口过滤（增量采集）
        # 6. 通过 AdaptiveRateController 控制频率
        ...
```

### 雪球社区爬虫（高反爬风险）

```python
class XueqiuCommentCrawler:
    """雪球社区评论爬虫
    
    采集策略：
    - 目标 API: https://xueqiu.com/query/v1/symbol/search/status.json
    - 个股讨论: https://xueqiu.com/statuses/stock_timeline.json?symbol_id={stock_id}
    - 反爬等级: 高（强制登录 Cookie、频繁更换 Token、IP 限制）
    - 应对策略:
      1. 维护多组登录 Cookie（手动获取后导入 Cookie 池）
      2. 每次请求轮换 Cookie + User-Agent + 代理 IP
      3. 请求间隔 3-5 秒（AdaptiveRateController 基础 cooldown=3.0）
      4. 检测到 403/验证码时立即降速（cooldown 翻倍）
      5. 连续 3 次失败触发 30 分钟封禁降级
    - 降级方案: 封禁期间使用 AKShare stock_hot_follow_xq() / stock_hot_tweet_xq() 替代
    """
    ...
```

### 同花顺社区爬虫（JS 逆向难度高）

```python
class THSCommentCrawler:
    """同花顺社区评论爬虫
    
    采集策略：
    - 目标 URL: https://t.10jqka.com.cn/circle/stock/{stock_code}/
    - 反爬等级: 高（Cookie 加密、JS 逆向、频率限制）
    - 应对策略:
      1. 需要逆向同花顺的 Cookie 加密算法（hexin-v 参数）
      2. 使用 Playwright/Selenium 获取动态渲染后的 Cookie
      3. 请求间隔 2-3 秒
      4. 维护成本较高，作为补充数据源
    - 降级方案: 采集失败时跳过，不影响综合指数计算（权重自动重分配）
    """
    ...
```

### 降级策略总结

| 数据源 | 反爬等级 | 降级触发条件 | 降级行为 | 恢复策略 |
|--------|----------|-------------|---------|---------|
| 东方财富股吧 | 中 | 连续 3 次失败 | 暂停 30 分钟，使用缓存 | 30 分钟后自动恢复 |
| 雪球社区 | 高 | 连续 3 次失败 | 暂停 30 分钟，切换到 AKShare 雪球热度数据 | 30 分钟后自动恢复 |
| 同花顺社区 | 高 | 连续 3 次失败 | 暂停 30 分钟，跳过该源 | 30 分钟后自动恢复 |
| 所有评论源均失败 | - | 三个源全部封禁 | 仅使用 AKShare 聚合指标计算指数（评论权重 40% 重分配给其他源） | 各源独立恢复 |

## 架构

```mermaid
graph TB
    subgraph 前端 Vue 3
        NB[NavigationBar 导航栏]
        SHV[StockHotView 股票热榜]
        SAV[StockAnalysisView 行情推演]
        DRV[DailyReportView 每日速报]
        SV[SettingsView 设置]
        PP[PlatformPreview 多平台预览]
        XP[XiaohongshuPreview 小红书预览]
        WC[WeiboCard 微博预览]
        XQC[XueqiuCard 雪球预览]
        ZHC[ZhihuCard 知乎预览]
        NB --> SHV
        NB --> SAV
        NB --> DRV
        NB --> SV
        SAV --> PP
        DRV --> PP
        PP --> XP
        PP --> WC
        PP --> XQC
        PP --> ZHC
    end

    subgraph 后端 FastAPI
        subgraph 股票资讯 API
            E1[GET /api/stock/news]
            E2[GET /api/stock/sources]
            E3[POST /api/stock/analyze]
            E4[GET /api/stock/analyze/history]
        end
        subgraph 情绪分析 API（核心引擎）
            E11[GET /api/sentiment/index]
            E12[GET /api/sentiment/index/{stock_code}]
            E13[GET /api/sentiment/history]
            E14[GET /api/sentiment/status]
            E15[PUT /api/sentiment/weights]
        end
        subgraph 社交内容 API
            E8[POST /api/content/generate]
            E9[POST /api/content/publish]
            E10[POST /api/content/daily-report]
        end
        subgraph 通用 API
            E5[GET /api/health]
            E6[GET /api/user-settings]
            E7[GET /api/models]
        end
    end

    subgraph 核心引擎：情绪数据层
        SentCrawler[SentimentCrawler 情绪爬虫]
        SentAnalyzer[SentimentAnalyzer 情绪分析]
        MixedSentData[MixedSentimentDataService 混合情绪数据]
        ProxyPool[ProxyPoolManager 代理池]
        CookiePool[CookiePoolManager Cookie池]
    end

    subgraph 服务层
        SC[StockNewsCollector 股票爬虫]
        INS[InternationalNewsService 国际财经]
        RRS[ResearchReportService 投行研报]
        SAS[StockAnalysisService 行情推演]
        SCG[SocialContentGenerator 内容生成]
        CS[ComplianceService 合规脱敏]
        IMG[ImageGeneratorService 配图生成]
        XHS[XiaohongshuPublisher 小红书发布]
        Cache[HotNewsCacheService 缓存]
        LLM[LLM Agent 链]
    end

    SHV -->|HTTP| E1
    SHV -->|HTTP| E11
    SAV -->|SSE| E3
    SAV -->|HTTP| E8
    SAV -->|HTTP| E9
    SAV -->|HTTP| E12
    DRV -->|HTTP| E10
    DRV -->|HTTP| E9
    DRV -->|HTTP| E11
    SC --> Cache
    SC --> INS
    SC --> RRS
    INS --> LLM
    INS --> Cache
    RRS --> Cache
    SAS --> LLM
    SAS --> Cache
    SAS --> SentAnalyzer
    SCG --> LLM
    SCG --> CS
    SCG --> IMG
    SCG --> XHS
    SCG --> SentAnalyzer
    CS --> Cache
    SentCrawler --> ProxyPool
    SentCrawler --> CookiePool
    SentCrawler --> Cache
    SentAnalyzer --> LLM
    SentAnalyzer --> Cache
    SentAnalyzer --> MixedSentData
    SentAnalyzer --> SentCrawler
    MixedSentData --> Cache
    E1 --> SC
    E3 --> SAS
    E8 --> SCG
    E9 --> SCG
    E10 --> SCG
    E11 --> SentAnalyzer
    E12 --> SentAnalyzer
    E13 --> SentAnalyzer
    E14 --> SentCrawler
    E15 --> MixedSentData
```

## 数据库（PostgreSQL 持久化）

使用 SQLAlchemy + asyncpg 实现 PostgreSQL 数据库持久化，替代 JSON 文件存储。

### 数据库连接配置

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/platform_db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：请求级 Session"""
    async with async_session_factory() as session:
        yield session
```

> 注意：使用 `async_sessionmaker`（SQLAlchemy 2.0+ 推荐）替代旧的 `sessionmaker(class_=AsyncSession)` 模式。后台任务和定时任务使用 `async_session_factory()` 创建独立 Session，详见"SQLAlchemy 异步 Session 管理策略"章节。DATABASE_URL 从 `.env` 文件读取。

### 数据库表

**stock_analysis_results** — 行情推演结果持久化（替代 `outputs/stock_analysis/` JSON 文件）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) PK | 推演结果唯一 ID |
| news_titles | TEXT (JSON) | 输入资讯标题列表 |
| summary | TEXT | 资讯摘要 |
| impact_analysis | TEXT | 影响分析 |
| bull_argument | TEXT | 多头激辩观点 |
| bear_argument | TEXT | 空头激辩观点 |
| debate_dialogue | TEXT | 多空交锋对话 |
| controversial_conclusion | TEXT | 争议性结论 |
| stance | VARCHAR(10) | 立场（bull/bear） |
| risk_warning | TEXT | 风险提示 |
| cache_hit | BOOLEAN | 是否缓存命中 |
| created_at | DATETIME | 创建时间（索引） |

**social_content** — 社交内容持久化（替代 `outputs/social_content/` JSON 文件）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) PK | 内容唯一 ID |
| platform | VARCHAR(20) | 目标平台 |
| title | TEXT | 标题 |
| body | TEXT | 正文内容 |
| tags | TEXT (JSON) | 话题标签列表 |
| image_urls | TEXT (JSON) | 配图 URL 列表 |
| source_analysis_id | VARCHAR(64) FK | 关联推演结果 ID |
| content_type | VARCHAR(20) | analysis / daily_report |
| status | VARCHAR(20) | draft / published |
| published_at | DATETIME | 发布时间 |
| created_at | DATETIME | 创建时间（索引） |
| desensitization_level | VARCHAR(10) | 脱敏级别 |
| original_content | TEXT | 脱敏前原始内容 |
| user_acknowledged_risk | BOOLEAN | 用户是否确认了"不脱敏"风险（选择 none 级别时为 True） |

**stock_sector_mapping** — 个股板块映射表持久化（替代 `outputs/compliance/stock_sector_mapping.json`）：

| 字段 | 类型 | 说明 |
|------|------|------|
| stock_code | VARCHAR(10) PK | 股票代码 |
| stock_name | VARCHAR(50) | 股票名称 |
| sector_name | VARCHAR(50) | 板块名称 |
| industry_name | VARCHAR(50) | 行业名称 |
| desensitized_label | VARCHAR(100) | 中度脱敏描述 |
| pinyin_abbr | VARCHAR(10) | 拼音缩写 |
| market_cap_rank | INTEGER | 行业内市值排名 |
| updated_at | DATETIME | 最后更新时间 |

### SQLAlchemy 模型

```python
# app/models.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, Float, ForeignKey
from app.database import Base
import datetime

class StockAnalysisResultDB(Base):
    __tablename__ = "stock_analysis_results"
    # ... 现有字段保持不变 ...

class SocialContentDB(Base):
    __tablename__ = "social_content"
    # ... 现有字段保持不变 ...

class StockSectorMappingDB(Base):
    __tablename__ = "stock_sector_mapping"
    # ... 现有字段保持不变 ...

class SentimentCommentDB(Base):
    """散户评论原始数据（90 天后自动归档清理）"""
    __tablename__ = "sentiment_comments"
    id = Column(String(64), primary_key=True)
    content = Column(Text)
    source_platform = Column(String(20), index=True)  # eastmoney / xueqiu / 10jqka
    stock_code = Column(String(10), nullable=True, index=True)  # 关联股票代码，NULL 表示综合讨论
    author_nickname = Column(String(100), nullable=True)
    published_time = Column(DateTime, index=True)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    content_hash = Column(String(32), unique=True)  # 内容 MD5 哈希，用于去重
    sentiment_label = Column(String(10), nullable=True)  # fear / greed / neutral
    sentiment_score = Column(Float, nullable=True)  # 0-100 情绪强度分数

class SentimentSnapshotDB(Base):
    """情绪指数快照（长期保留）"""
    __tablename__ = "sentiment_snapshots"
    id = Column(String(64), primary_key=True)
    stock_code = Column(String(10), nullable=True, index=True)  # NULL 表示大盘整体
    index_value = Column(Float)  # 0-100 综合情绪指数
    comment_sentiment_score = Column(Float, nullable=True)  # 评论情绪分项得分
    baidu_vote_score = Column(Float, nullable=True)  # 百度投票分项得分
    akshare_aggregate_score = Column(Float, nullable=True)  # AKShare 聚合分项得分
    news_sentiment_score = Column(Float, nullable=True)  # 新闻情绪分项得分
    margin_trading_score = Column(Float, nullable=True)  # 融资融券分项得分
    fear_ratio = Column(Float)   # 恐慌评论占比
    greed_ratio = Column(Float)  # 贪婪评论占比
    neutral_ratio = Column(Float)  # 中性评论占比
    sample_count = Column(Integer)  # 评论样本数
    data_source_availability = Column(Text, nullable=True)  # JSON: 各数据源可用性状态
    snapshot_time = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

### 迁移管理

使用 Alembic 管理数据库 schema 迁移：
- `alembic init alembic` 初始化迁移目录
- `alembic revision --autogenerate -m "initial"` 生成初始迁移
- `alembic upgrade head` 应用迁移

#### 迁移脚本编写约定

由于系统分阶段开发（Phase 1 部署后 Phase 3 新增 sentiment 表），迁移脚本必须能在已有数据的库上安全执行：

1. **新增表**：使用 `CREATE TABLE IF NOT EXISTS`（Alembic `op.create_table()` 默认行为，但手写 SQL 时需显式添加）
2. **新增字段**：使用 `ALTER TABLE ADD COLUMN`；新增字段必须为 `nullable=True` 或提供 `server_default`
3. **新增索引**：使用 `CREATE INDEX IF NOT EXISTS`
4. **幂等执行**：所有迁移脚本必须支持幂等执行（重复运行不报错），通过 `op.execute()` 中添加 `IF NOT EXISTS` 子句实现
5. **数据迁移**：如需修改已有数据，在迁移脚本中使用 `UPDATE ... WHERE` 而非全表重写

```python
# 示例：Phase 3 新增 sentiment 表的迁移脚本
def upgrade():
    # 新增表（幂等）
    op.create_table(
        'sentiment_comments',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('content', sa.Text),
        # ... 其他字段
    )
    
    # 为已有表新增字段
    op.add_column('stock_analysis_results', sa.Column('sentiment_context', sa.Text, nullable=True))

def downgrade():
    op.drop_table('sentiment_comments')
    op.drop_column('stock_analysis_results', 'sentiment_context')
```

**sentiment_comments** — 散户评论原始数据（90 天后自动归档清理）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) PK | 评论唯一 ID |
| content | TEXT | 评论内容 |
| source_platform | VARCHAR(20) INDEX | 来源平台（eastmoney/xueqiu/10jqka） |
| stock_code | VARCHAR(10) INDEX | 关联股票代码，NULL 表示综合讨论 |
| author_nickname | VARCHAR(100) | 作者昵称 |
| published_time | DATETIME INDEX | 发布时间 |
| collected_at | DATETIME | 采集时间 |
| content_hash | VARCHAR(32) UNIQUE | 内容 MD5 哈希，用于去重 |
| sentiment_label | VARCHAR(10) | 情绪标签（fear/greed/neutral） |
| sentiment_score | FLOAT | 情绪强度分数（0-100） |

**sentiment_snapshots** — 情绪指数快照（长期保留）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) PK | 快照唯一 ID |
| stock_code | VARCHAR(10) INDEX | 股票代码，NULL 表示大盘整体 |
| index_value | FLOAT | 综合情绪指数值（0-100，加权计算） |
| comment_sentiment_score | FLOAT NULL | 评论情绪分项得分（0-100） |
| baidu_vote_score | FLOAT NULL | 百度投票分项得分（0-100） |
| akshare_aggregate_score | FLOAT NULL | AKShare 聚合分项得分（0-100） |
| news_sentiment_score | FLOAT NULL | 新闻情绪分项得分（0-100） |
| margin_trading_score | FLOAT NULL | 融资融券分项得分（0-100） |
| fear_ratio | FLOAT | 恐慌评论占比 |
| greed_ratio | FLOAT | 贪婪评论占比 |
| neutral_ratio | FLOAT | 中性评论占比 |
| sample_count | INTEGER | 评论样本数 |
| data_source_availability | TEXT NULL | JSON: 各数据源可用性状态 |
| snapshot_time | DATETIME INDEX | 快照时间 |
| created_at | DATETIME | 创建时间 |

## 定时任务调度服务

### SchedulerService（`app/services/scheduler_service.py`）

基于 APScheduler 实现定时任务调度，支持每日速报定时生成和增量更新检查：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.content_generator = None  # 延迟初始化
    
    async def start(self):
        """启动调度器，注册定时任务"""
        # 每日速报定时生成（默认 18:00，可在设置中配置）
        self.scheduler.add_job(
            self.generate_daily_report,
            'cron', hour=18, minute=0,
            id='daily_report',
            replace_existing=True
        )
        # 每小时增量检查（检测重大新闻变化）
        self.scheduler.add_job(
            self.check_news_updates,
            'interval', hours=1,
            id='hourly_news_check',
            replace_existing=True
        )
        self.scheduler.start()
    
    async def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
    
    async def generate_daily_report(self):
        """定时生成每日速报"""
        # 采集当日热点资讯 → 生成速报内容 → 持久化到 DB
    
    async def check_news_updates(self):
        """每小时检查重大新闻变化
        - 采集最新资讯，与上次检查对比
        - 若发现重大变化（如新增高热度资讯），触发速报增量更新
        """
    
    def update_schedule(self, daily_report_hour: int = 18, daily_report_minute: int = 0):
        """更新定时任务配置（从设置页面调用）"""
        self.scheduler.reschedule_job(
            'daily_report', 
            trigger='cron', hour=daily_report_hour, minute=daily_report_minute
        )
```

调度器在 FastAPI 应用启动时通过 `lifespan` 事件初始化，关闭时停止。定时配置可通过设置页面修改。

### 定时任务并发安全策略

SchedulerService 有三个定时任务（每日速报 18:00、每小时新闻检查、每 2 小时情绪采集），它们可能同时触发（如 18:00 同时触发速报生成和新闻检查）。为避免并发冲突（如重复采集、缓存竞争），采用全局任务锁：

```python
class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._task_lock = asyncio.Lock()  # 全局任务锁，确保同一时刻只有一个定时任务在执行
    
    async def generate_daily_report(self):
        """定时生成每日速报（加锁）"""
        async with self._task_lock:
            # 采集当日热点资讯 → 生成速报内容 → 持久化到 DB
            ...
    
    async def check_news_updates(self):
        """每小时检查重大新闻变化（加锁）"""
        async with self._task_lock:
            # 采集最新资讯，与上次检查对比
            ...
    
    async def run_sentiment_analysis(self):
        """定时执行情绪采集和分析（加锁）"""
        async with self._task_lock:
            # 采集评论 → 分析 → 生成快照
            ...
```

并发安全策略说明：
- 使用 `asyncio.Lock()` 作为全局任务锁，确保同一时刻只有一个定时任务在执行
- 当多个任务同时触发时（如 18:00），先获取锁的任务执行，其他任务排队等待
- 锁的粒度为整个任务执行周期，避免任务之间共享 StockNewsCollector、缓存等资源时产生竞争
- APScheduler 的 `max_instances=1`（默认值）确保同一个 job 不会并发执行自身

## 外部 API 配额管理

系统同时对接 10+ 个外部数据源，各数据源有不同的 rate limit 和每日配额限制。为避免用户频繁刷新耗尽免费层配额，系统需要跟踪 API 调用次数并提供可视化：

### 配额配置

```python
API_QUOTA_LIMITS = {
    "finnhub": {"rate_limit": "60/min", "daily_limit": None, "tier": "free"},
    "newsapi": {"rate_limit": None, "daily_limit": 100, "tier": "free"},
    "alpha_vantage": {"rate_limit": None, "daily_limit": 25, "tier": "free"},
    "marketaux": {"rate_limit": None, "daily_limit": 100, "tier": "free"},
    "gdelt": {"rate_limit": None, "daily_limit": None, "tier": "free"},
    "google_rss": {"rate_limit": None, "daily_limit": None, "tier": "free"},
    "yahoo": {"rate_limit": None, "daily_limit": None, "tier": "free"},
    "akshare": {"rate_limit": None, "daily_limit": None, "tier": "free"},
}
```

### API 配额追踪器

```python
class APIQuotaTracker:
    """API 配额追踪器，记录每日调用次数和剩余配额"""
    
    def __init__(self):
        self._daily_counts: Dict[str, int] = {}  # source_id -> today's call count
        self._minute_counts: Dict[str, List[float]] = {}  # source_id -> [timestamps]
        self._last_reset_date: str = ""
    
    def record_call(self, source_id: str):
        """记录一次 API 调用"""
        self._auto_reset_daily()
        self._daily_counts[source_id] = self._daily_counts.get(source_id, 0) + 1
        # 记录分钟级时间戳（用于 rate limit 检查）
        if source_id not in self._minute_counts:
            self._minute_counts[source_id] = []
        self._minute_counts[source_id].append(time.time())
    
    def get_remaining(self, source_id: str) -> Optional[int]:
        """获取剩余每日配额，无限制返回 None"""
        limit = API_QUOTA_LIMITS.get(source_id, {}).get("daily_limit")
        if limit is None:
            return None
        return max(0, limit - self._daily_counts.get(source_id, 0))
    
    def is_quota_exhausted(self, source_id: str) -> bool:
        """检查每日配额是否已耗尽"""
        remaining = self.get_remaining(source_id)
        return remaining is not None and remaining <= 0
    
    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有数据源的配额状态，供前端仪表盘展示"""
        # 返回 {source_id: {daily_limit, used_today, remaining, rate_limit, tier}}
```

### 前端配额仪表盘

在 SettingsView 的数据源配置区域下方新增"API 配额使用情况"面板：
- 每个有每日限额的数据源显示进度条（已用/总量）
- 配额低于 20% 时进度条变为橙色警告色
- 配额耗尽时进度条变为红色，并显示"今日配额已用完，明日自动恢复"提示
- 无限制的数据源显示"无限制"标签

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/stock/datasource/quota` | GET | 获取所有数据源的配额使用状态 |

## 数据量估算与存储规划

### 数据量估算

基于每 2 小时采集一次、每次采集 3 个数据源（东方财富/雪球/同花顺）的假设：

| 表 | 单次采集量 | 每日增量 | 90 天累计 | 单条大小（估算） | 90 天存储 |
|---|---|---|---|---|---|
| sentiment_comments | 300-1000 条 | 3600-12000 条 | 32 万-108 万条 | ~500 bytes | 150-500 MB |
| sentiment_snapshots | 1-5 条 | 12-60 条 | 1080-5400 条 | ~300 bytes | < 2 MB |
| stock_analysis_results | - | 5-20 条（用户触发） | 450-1800 条 | ~5 KB | < 10 MB |
| social_content | - | 5-20 条（用户触发） | 450-1800 条 | ~3 KB | < 6 MB |
| stock_sector_mapping | - | 全量更新 ~5000 条 | ~5000 条 | ~200 bytes | < 1 MB |

### SQLite 容量评估

- **sentiment_comments 是主要存储压力来源**：90 天累计可达 150-500 MB
- SQLite 单文件数据库理论上限 281 TB，实际在 1-10 GB 范围内性能良好
- 当前估算的 90 天数据量（~500 MB）在 SQLite 舒适区内
- 90 天自动清理机制确保 sentiment_comments 表不会无限增长
- sentiment_snapshots 永久保留，但数据量极小（一年 < 10 MB），不构成存储压力

### 迁移到 PostgreSQL 的触发条件

以下情况建议考虑迁移到 PostgreSQL：
- sentiment_comments 表超过 500 万条（约 2.5 GB）
- 并发写入频繁导致 SQLite 锁等待超过 1 秒
- 需要多实例部署（SQLite 不支持多进程并发写入）
- 需要全文搜索功能（PostgreSQL 的 `tsvector` 优于 SQLite 的 FTS5）

> **结论**：初始版本使用 SQLite 完全足够。90 天清理策略 + 快照永久保留的设计确保存储可控。Schema 设计已遵循关系型数据库规范，迁移到 PostgreSQL 只需修改 `DATABASE_URL` 连接字符串。
