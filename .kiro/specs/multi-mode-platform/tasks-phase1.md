> 本文件是 tasks.md 拆分后的子文件。完整实现计划包含：
> - [tasks-phase1.md](tasks-phase1.md)  阶段一：后端基础（数据模型、爬虫、API、推演）任务 1-7
> - [tasks-phase2.md](tasks-phase2.md)  阶段二：社交内容、合规、前端、清理旧代码 任务 8-19
> - [tasks-phase3.md](tasks-phase3.md)  阶段三：散户情绪分析全链路 任务 20-29

# 实现计划：股票资讯与行情推演平台

## 概述

将现有舆论分析系统改造为股票资讯与行情推演平台。后端使用 Python FastAPI，前端使用 Vue 3。复用现有的缓存、LLM 集成和 SSE 流式架构，替换业务逻辑层。

## 任务

- [x] 1. 后端：股票资讯数据模型与配置
  - [x] 1.1 在 `app/schemas.py` 中新增 StockNewsItem、StockNewsCollectResponse、StockAnalysisRequest、StockAnalysisStep、StockAnalysisResult 等数据模型
    - StockNewsItem 包含：is_ai_translated 字段（布尔值，标记是否为 AI 翻译的摘要，供前端展示"AI 翻译摘要"标签）
    - StockAnalysisRequest 包含：topic（推演主题字符串）、debate_rounds（辩论轮数，默认2）、news_items（可选关联资讯）
    - StockAnalysisResult 包含：summary、impact_analysis、bull_argument、bear_argument、debate_dialogue、controversial_conclusion、stance、risk_warning
    - 参考现有 HotNewsInterpretRequest/Response 的模式
    - _Requirements: 1.2, 3.2_
  - [x] 1.2 在 `app/config.py` 中新增 STOCK_NEWS_CONFIG 配置项（数据源列表、缓存 TTL、每源最大条目数）
    - 数据源包括：akshare（主要）、sina、10jqka、xueqiu、tushare
    - 新增 INTERNATIONAL_NEWS_CONFIG 配置项（国际财经数据源列表、API Key 引用、缓存 TTL）
    - 国际数据源包括：finnhub、newsapi、alpha_vantage、gdelt、google_rss、marketaux
    - 新增 RESEARCH_REPORT_CONFIG 配置项（投行研报数据源列表、缓存 TTL）
    - 投行研报数据源包括：tipranks、marketbeat、benzinga、seekingalpha、finviz、zacks、yahoo、simplywallst、last10k、wisesheets
    - 新增 API Key 配置（从 .env 读取）：FINNHUB_API_KEY、NEWSAPI_API_KEY、ALPHA_VANTAGE_API_KEY、MARKETAUX_API_KEY、BENZINGA_API_KEY、SEEKING_ALPHA_API_KEY
    - 参考现有 HOT_NEWS_CONFIG 的模式
    - _Requirements: 1.1, 1.2, 1.7, 1.8_
  - [x] 1.3 更新 `requirements.txt`，新增所有新依赖
    - akshare、tushare、pypinyin、finnhub-python、newsapi-python、alpha_vantage、feedparser、yfinance
    - sqlalchemy、aiosqlite、alembic（数据库持久化和迁移）
    - apscheduler（定时任务调度）
    - httpx[socks]（SOCKS5 代理支持，用于情绪爬虫代理池）
    - _Requirements: 1.1, 1.7, 1.8, 3.11, 9.5_
  - [x] 1.4 更新 `.env.example`，新增所有 API Key 配置项模板
    - FINNHUB_API_KEY、NEWSAPI_API_KEY、ALPHA_VANTAGE_API_KEY、MARKETAUX_API_KEY、BENZINGA_API_KEY、SEEKING_ALPHA_API_KEY
    - 每项附带注释说明用途和获取方式
    - _Requirements: 1.7, 1.8, 8.2_
  - [x] 1.5 在 `app/schemas.py` 中新增 DataSourceConfig、DataSourceStatus、DataSourceConfigResponse 数据模型
    - DataSourceConfig：source_id、display_name、category、requires_api_key、enabled、api_key、status、last_tested
    - DataSourceStatus 枚举：NOT_CONFIGURED、CONFIGURED、CONNECTED、FAILED、FREE
    - _Requirements: 8.1, 8.3_
  - [x] 1.6 创建数据库模型和迁移配置
    - 创建 `app/database.py`：SQLAlchemy 异步引擎配置（SQLite + aiosqlite），使用 `async_sessionmaker`（SQLAlchemy 2.0+），`get_db` 依赖注入（请求级 Session）
    - 后台任务/定时任务使用 `async_session_factory()` 创建独立 Session（不依赖请求上下文）
    - 创建 `app/models.py`：定义 StockAnalysisResultDB、SocialContentDB、StockSectorMappingDB 三个 ORM 模型
    - 初始化 Alembic 迁移目录（`alembic init alembic`），配置 `alembic.ini` 和 `alembic/env.py`
    - 生成初始迁移脚本（`alembic revision --autogenerate -m "initial"`）
    - Schema 设计遵循关系型数据库规范，便于未来迁移到 `PostgreSQL`/MySQL（仅需修改 DATABASE_URL）
    - _Requirements: 3.11_

- [x] 2. 后端：股票资讯爬虫服务
  - [x] 2.1 创建 `app/services/stock_news_collector.py`，实现 StockNewsCollector 类
    - 参考 `app/services/tophub_collector.py` 的设计模式
    - 实现 RateLimiter 类：基于 asyncio.Semaphore 的全局并发控制 + 每源独立 cooldown 配置（SourceRateLimitConfig），替代硬编码 sleep
    - 实现 RateLimiter.handle_failure() 高风险源指数退避策略：第一次失败等待 5s 重试，第二次失败等待 15s 重试，第三次失败跳过该源
    - 为所有数据源配置 DEFAULT_RATE_LIMIT_CONFIGS（含 max_concurrent、cooldown_seconds、is_high_risk 参数）
    - 实现 AKShare 数据源采集（主要）：使用 `asyncio.to_thread()` 包装所有 AKShare 同步调用（`stock_news_em()`、`stock_hot_rank_em()` 等），避免阻塞事件循环
    - 实现新浪财经 API 采集
    - 实现同花顺热股排行采集
    - 实现雪球热帖采集（需处理反爬机制）
    - 实现 Tushare 免费层采集（可选，需 token）
    - 所有数据源采集方法通过 RateLimiter.acquire()/release() 控制请求速率
    - 实现 `collect_news(source_ids, force_refresh)` 方法，支持缓存检查、并发采集、结果合并
    - 集成 HotNewsCacheService，使用 `stock_` 前缀的 cache_key
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.12, 1.13_
  - [x] 2.2 为 StockNewsCollector 编写属性测试
    - **Property 1: 股票资讯条目数据完整性**
    - **Validates: Requirements 1.2**
  - [x] 2.3 为缓存逻辑编写属性测试
    - **Property 2: 股票资讯缓存往返一致性**
    - **Property 4: 强制刷新绕过缓存**
    - **Validates: Requirements 1.3, 1.5**
  - [x] 2.4 为 RateLimiter 编写属性测试
    - **Property 29: 高风险源指数退避行为**（连续失败时 5s→15s→跳过）
    - **Property 30: RateLimiter 每源 cooldown 隔离性**（不同源的 cooldown 互不影响）
    - **Validates: Requirements 1.12, 1.13**

- [x] 2A. 后端：国际财经新闻采集服务
  - [x] 2A.1 创建 `app/services/international_news_service.py`，实现 InternationalNewsService 类
    - 实现 Finnhub 新闻采集（`fetch_finnhub_news`）：使用 finnhub-python SDK，`/api/v1/news` 和 `/api/v1/company-news` 端点
    - 实现 NewsAPI 新闻采集（`fetch_newsapi_news`）：使用 newsapi-python 客户端，按金融/股票关键词筛选
    - 实现 Alpha Vantage 新闻采集（`fetch_alpha_vantage_news`）：使用 alpha_vantage 库，`NEWS_SENTIMENT` 端点，提取情绪分析评分
    - 实现 GDELT 新闻采集（`fetch_gdelt_news`）：通过 HTTP 请求 GDELT GKG/DOC API，按 ECON_STOCKMARKET 主题过滤
    - 实现 Google News RSS 采集（`fetch_google_news_rss`）：使用 feedparser 解析 RSS feed
    - 实现 Marketaux 新闻采集（`fetch_marketaux_news`）：通过 HTTP API，提取情绪标签
    - 实现 `batch_translate_to_chinese(news_items, max_items=20)` 方法：批量调用 LLM 将多条英文新闻翻译为中文摘要（合并为一次 LLM 调用，每批最多 20 条）；LLM prompt 中强调"严格基于原文翻译，不添加任何原文没有的信息"；翻译后标记 is_ai_translated=True
    - 实现 `collect_international_news(source_ids, force_refresh)` 方法：并发采集所有启用的国际源，英文内容通过 batch_translate_to_chinese() 批量翻译，结果合并去重
    - API Key 从 .env 读取，未配置的数据源自动跳过
    - 集成 HotNewsCacheService，使用 `intl_news_` 前缀的 cache_key
    - _Requirements: 1.7, 1.9, 1.14_
  - [x] 2A.2 为国际财经新闻服务编写属性测试
    - **Property 24: 国际财经新闻中文摘要完整性**
    - **Property 28: 国际新闻源失败不影响国内数据**
    - **Property 31: AI 翻译摘要标记一致性**
    - **Validates: Requirements 1.9, 1.5, 1.14**

- [x] 2B. 后端：投行研报与分析师评级服务
  - [x] 2B.1 在 `app/schemas.py` 中新增 AnalystRating、ConsensusRating 数据模型
    - AnalystRating：analyst_name、firm、rating、rating_normalized、target_price、previous_target、currency、date、stock_symbol、stock_name、action、summary
    - ConsensusRating：stock_symbol、stock_name、buy_count、hold_count、sell_count、consensus、avg_target_price、high_target、low_target、total_analysts、last_updated
    - 更新 StockNewsItem 模型：新增 original_language、sentiment、analyst_rating 字段
    - _Requirements: 1.10_
  - [x] 2B.2 创建 `app/services/research_report_service.py`，实现 ResearchReportService 类
    - 按分层优先级实现数据源采集，支持降级策略（Tier 1 → Tier 2 → Tier 3 → Tier 4）
    - **Tier 1（核心免费源，始终启用）：**
      - 实现 Finnhub 分析师推荐采集（`fetch_finnhub_recommendations`）：`/stock/recommendation` 端点获取 buy/hold/sell/strongBuy/strongSell 结构化计数，`/stock/earnings` 获取盈利惊喜，**首选数据源**
      - 实现 Yahoo Finance 评级采集（`fetch_yahoo_finance_ratings`）：使用 yfinance 库，ticker.recommendations 和 ticker.analyst_price_targets，完全免费无需 API Key
    - **Tier 2（免费层可用，良好补充）：**
      - 实现 Finviz 评级采集（`fetch_finviz_ratings`）：免费 HTML 抓取，分析师目标价和评级概览
      - 实现 Zacks 评级采集（`fetch_zacks_ratings`）：免费层基本评级信息（Zacks Rank 1-5）
    - **Tier 3（需付费 API Key，可选）：**
      - 实现 Benzinga 评级采集（`fetch_benzinga_ratings`）：需付费 API Key
      - 实现 Seeking Alpha 评级采集（`fetch_seeking_alpha_ratings`）：部分免费
    - **Tier 4（高反爬风险，尽力而为）：**
      - 实现 TipRanks（`fetch_tipranks_ratings`）、MarketBeat（`fetch_marketbeat_ratings`）、Simply Wall St（`fetch_simply_wall_st`）、Last10K（`fetch_last10k_summaries`）、Wisesheets（`fetch_wisesheets_reports`）：均为 HTTP 抓取，失败时静默跳过
    - 实现降级逻辑：按 Tier 顺序采集，每层内并发，所有层均失败时返回空结果并附带 tier_status 信息
    - 实现 `normalize_rating(raw_rating)` 方法：将各平台评级标准化为 buy/hold/sell
    - 实现 `collect_research_reports(symbols, source_ids, force_refresh)` 方法：分层并发采集
    - 实现 `get_consensus_rating(symbol)` 方法：计算共识评级和平均目标价
    - 实现 `convert_to_news_items(ratings)` 方法：将 AnalystRating 转换为 StockNewsItem 格式
    - 集成 HotNewsCacheService，使用 `research_` 前缀的 cache_key
    - _Requirements: 1.8, 1.10_
  - [x] 2B.3 为投行研报服务编写属性测试
    - **Property 25: 投行研报结构化数据完整性**
    - **Property 26: 资讯类别筛选一致性**
    - **Property 27: 共识评级计算一致性**
    - **Validates: Requirements 1.10, 1.11**
  - [x] 2B.4 更新 `app/services/stock_news_collector.py`，集成 InternationalNewsService 和 ResearchReportService
    - 在 StockNewsCollector.__init__ 中初始化 intl_news_service 和 research_service
    - 更新 collect_news 方法：新增 include_international 和 include_research 参数
    - 并发采集国内源 + 国际源 + 投行研报，合并结果
    - 返回结果中以 category 字段区分 domestic/international/research_report
    - 在 StockNewsCollectResponse 中新增 category_stats 字段
    - _Requirements: 1.7, 1.8, 1.11_

- [x] 3. 后端：股票资讯 API 端点
  - [x] 3.1 创建 `app/api/stock_endpoints.py`，实现股票资讯相关路由
    - GET `/api/stock/news`：获取资讯列表，支持 limit/source/category/force_refresh 参数；category 支持 domestic/international/research_report
    - GET `/api/stock/sources`：获取数据源列表及状态（含国内、国际、研报三类）
    - GET `/api/stock/research/consensus/{symbol}`：获取指定股票的共识评级
    - GET `/api/stock/research/ratings/{symbol}`：获取指定股票的分析师评级列表
    - GET `/api/stock/datasource/config`：获取所有数据源的配置状态
    - PUT `/api/stock/datasource/config`：保存数据源配置（API Key、启用/禁用状态）
    - POST `/api/stock/datasource/test/{source_id}`：测试指定数据源的 API Key 连通性
    - 参数校验和错误处理
    - _Requirements: 2.1, 2.3, 2.4, 1.11, 7.1, 7.4, 8.3, 8.4, 8.6_
  - [x] 3.2 在 `app/main.py` 中注册股票资讯路由（`/api/stock/` 前缀）
    - _Requirements: 7.1_
  - [x] 3.3 为股票资讯 API 编写属性测试
    - **Property 5: 股票资讯按排名排序**
    - **Property 6: 平台筛选结果一致性**
    - **Property 11: 无效参数返回 400 错误**
    - **Property 26: 资讯类别筛选一致性**
    - **Validates: Requirements 2.1, 2.4, 1.11, 7.4**

- [x] 4. Checkpoint - 确保股票资讯采集和 API 正常工作
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 5. 后端：行情推演服务
  - [x] 5.1 创建 `app/services/stock_analysis_service.py`，实现 StockAnalysisService 类
    - 创建 `app/services/stock_workflow_status.py`，复用现有 `workflow_status.py` 的 WorkflowStatusManager 模式实现 StockWorkflowStatusManager（步骤追踪、进度更新、SSE 流式状态）
    - 实现九步推演流程（情绪数据获取 → 资讯汇总 → 影响分析 → 多头激辩 → 空头激辩 → 多空交锋 → 争议性结论 → 文案生成 → 配图生成）
    - **Step 0 情绪数据获取（核心引擎输入）**：调用 SentimentAnalyzer.get_sentiment_context(stock_code) 获取最新情绪数据（综合指数、各分项得分、趋势方向、样本量、数据源可用性），作为后续所有 Agent 的共享上下文；情绪数据不可用时记录日志并继续推演（降级为无情绪数据模式）
    - 接受 topic 字符串作为主要输入（用户直接输入的推演主题），可选附带 news_items
    - 多头激辩 Agent：坚定看多立场，激进有说服力，引用数据、历史类比和情绪数据佐证
    - 空头激辩 Agent：坚定看空立场，犀利有冲击力，揭示风险反驳多头，引用情绪数据佐证
    - 多空交锋 Agent：对话体呈现直接交锋，轮数由 debate_rounds 参数控制（默认 2 轮），逐步升级争议
    - 争议性结论 Agent：选择偏多或偏空立场，标题党风格输出核心观点
    - 文案生成 Agent（Writer）：根据推演结果生成社交平台文案（TITLE + CONTENT 格式），融入情绪数据亮点
    - 配图生成 Agent（Image Generator）：调用火山引擎文生图生成金融风格配图
    - 使用 `get_agent_llm()` 获取 LLM 实例
    - 以 async generator 方式 yield StockAnalysisStep 事件
    - 推演结果缓存（60 分钟，以 topic 哈希为 key）
    - 结果持久化到 SQLite 数据库（`stock_analysis_results` 表），历史查询支持分页
    - StockAnalysisResult 包含 sentiment_context 字段（推演时引用的情绪数据快照）
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.11, 3.12, 5.1, 5.2, 5.6, 9.25, 9.26, 9.27_
  - [x] 5.2 为行情推演结果编写属性测试
    - **Property 8: 行情推演结果完整性**（含 bull_argument、bear_argument、debate_dialogue、controversial_conclusion、stance）
    - **Property 16: 多空交锋对话轮次**（轮数与 debate_rounds 参数一致，默认 2 轮）
    - **Property 17: 争议性结论立场一致性**（stance 与 conclusion 方向一致）
    - **Validates: Requirements 3.2, 3.5, 3.6**

- [x] 6. 后端：行情推演 API 端点
  - [x] 6.1 在 `app/api/stock_endpoints.py` 中新增行情推演路由
    - POST `/api/stock/analyze`：触发推演，SSE 流式返回
    - GET `/api/stock/analyze/history`：获取历史记录列表
    - GET `/api/stock/analyze/{analysis_id}`：获取单条结果详情
    - _Requirements: 3.1, 3.6, 7.2, 7.4_
  - [x] 6.2 为行情推演 API 编写属性测试
    - **Property 10: 历史推演记录按时间倒序**
    - **Validates: Requirements 3.6**

- [ ] 7. Checkpoint - 确保后端全部功能正常
  - 确保所有测试通过，如有问题请向用户确认。
