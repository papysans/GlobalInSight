# 需求文档：股票资讯与行情推演平台

## 简介

将现有的"观潮 GlobalInSight"系统改造为 AI 股票内容创作平台。系统的核心能力包括三大支柱：（1）股票热点资讯的多源采集与展示；（2）基于散户情绪数据和资讯的 LLM 行情推演分析——散户情绪分析是系统的核心引擎，通过混合数据源（东方财富/雪球/同花顺评论爬虫 + AKShare 聚合指标 + 百度投票 + 新闻情绪指数 + 融资融券数据）构建综合恐慌/贪婪指数，为行情推演和内容创作提供数据支撑；（3）将分析结果自动转化为适合社交平台发布的内容（小红书图文、微博短文、雪球长文、知乎长文、每日速报等），内容中融入情绪数据洞察以增强说服力和传播力。核心定位从"信息聚合工具"转向"情绪驱动的 AI 股票内容创作助手"。现有的舆论分析功能不再保留，系统专注于股票领域。

系统以 A 股（沪深两市）和港股为主要覆盖市场。投行研报数据源虽然部分来自国际平台，但优先筛选与中国市场相关的内容（A 股、港股、中概股）。国际财经新闻采集同样侧重与中国市场相关的全球动态。当前版本不考虑 API 鉴权，后续版本可按需添加。

## 术语表

- **Platform（平台）**：股票资讯与行情推演系统整体
- **Stock_Crawler（股票爬虫）**：负责从股票资讯平台采集数据的后端服务
- **Stock_Source（股票数据源）**：提供股票资讯的外部平台（如东方财富、雪球等）
- **Stock_News_Item（股票资讯条目）**：从股票数据源采集到的单条资讯数据
- **Stock_Analysis_Agent（行情推演Agent）**：基于股票资讯数据，利用 LLM 对相关股票进行多角度推演分析的智能体
- **Stock_Analysis_Result（行情推演结果）**：行情推演Agent输出的分析报告，包含资讯摘要、影响分析、多空观点和风险提示
- **International_News_Source（国际财经数据源）**：提供国际财经新闻的外部 API 服务（如 Finnhub、NewsAPI、Alpha Vantage 等）
- **Research_Report_Source（投行研报数据源）**：提供投行分析师评级和研报数据的外部平台（如 TipRanks、MarketBeat、Benzinga 等）
- **Analyst_Rating（分析师评级）**：投行分析师对个股的评级信息，包含评级（买入/持有/卖出）、目标价、分析师和机构信息
- **Navigation_Bar（导航栏）**：页面顶部的功能切换导航组件
- **Sentiment_Crawler（情绪爬虫）**：负责从股票讨论社区采集散户评论/帖子数据的后端服务
- **Sentiment_Source（情绪数据源）**：提供散户讨论内容的外部平台（如东方财富股吧、雪球社区、同花顺社区等）
- **Sentiment_Comment（情绪评论条目）**：从情绪数据源采集到的单条散户评论或帖子数据
- **Sentiment_Index（情绪指数）**：基于散户评论情绪分析计算得出的恐慌/贪婪指数，数值范围 0-100（0 为极度恐慌，100 为极度贪婪）
- **Sentiment_Analyzer（情绪分析器）**：利用 LLM 对散户评论进行情绪分类和打分的分析服务
- **Sentiment_Snapshot（情绪快照）**：某一时间点的综合情绪指数及其各分项得分数据，用于时序图表展示
- **Mixed_Sentiment_Source（混合情绪数据源）**：除散户评论外的其他情绪量化数据来源，包括 AKShare 聚合指标、百度股市通投票、新闻情绪指数、融资融券数据等
- **Sentiment_Weight_Model（情绪加权模型）**：将多个数据源的情绪信号按权重合并计算综合情绪指数的算法模型

## 需求

### 需求 1：股票资讯数据采集

**用户故事：** 作为用户，我希望系统能够从国内外主流股票资讯平台和投行研报渠道采集热点数据，以便获取最新的全球股票市场动态和专业机构观点。

#### 验收标准

1. THE Stock_Crawler SHALL 支持从至少三个 Stock_Source 采集股票资讯数据，优先使用免费 API 和开源库（如 AKShare）
2. THE Stock_Crawler SHALL 支持以下国内数据源：AKShare（主要，通过 `stock_news_em()`、`stock_hot_rank_em()` 等接口获取东方财富数据）、新浪财经（API 接口）、同花顺（热股排行）、雪球（热帖/话题）、Tushare（免费层）
3. WHEN Stock_Crawler 执行采集任务, THE Stock_Crawler SHALL 返回包含标题、摘要、来源平台、发布时间和原文链接的 Stock_News_Item 列表
4. WHEN Stock_Crawler 采集完成, THE Platform SHALL 将采集结果缓存到本地存储，缓存有效期为 30 分钟
5. IF Stock_Source 请求失败, THEN THE Stock_Crawler SHALL 记录错误日志并返回已缓存的数据（若存在）
6. WHEN 用户请求刷新数据, THE Stock_Crawler SHALL 跳过缓存并重新执行采集任务
12. THE Stock_Crawler SHALL 使用全局 RateLimiter 控制并发请求速率，基于 asyncio.Semaphore 实现全局并发上限，并为每个 Stock_Source 配置独立的 cooldown 间隔（秒），而非硬编码 sleep
13. WHEN 高风险 Stock_Source（Tier 4 或标记为高反爬风险的数据源）请求失败, THEN THE Stock_Crawler SHALL 执行指数退避策略：第一次失败等待 5 秒重试，第二次失败等待 15 秒重试，第三次失败跳过该数据源并记录日志
7. THE Stock_Crawler SHALL 支持以下国际财经媒体数据源：Finnhub（免费层，聚合 Reuters/CNBC 等主流财经媒体新闻，`/api/v1/news` 和 `/api/v1/company-news` 端点）、NewsAPI（免费开发者层，覆盖 Bloomberg/Reuters/CNBC/Financial Times/WSJ 等）、Alpha Vantage（免费层，`NEWS_SENTIMENT` 端点提供新闻及情绪分析）、GDELT Project（完全免费，全球新闻监控，通过 GKG/DOC API 获取金融相关新闻）、Google News RSS（免费，通过 RSS feed 按金融/股票主题过滤）、Marketaux（免费层，金融新闻 API 带情绪分析标签）
8. THE Stock_Crawler SHALL 支持以下投行研报与分析师评级数据源，按优先级分层采集并支持降级策略：**Tier 1（核心免费源，始终启用）**：Finnhub（免费层 `/stock/recommendation` 端点提供 buy/hold/sell/strongBuy/strongSell 计数的分析师推荐趋势，`/stock/earnings` 提供盈利惊喜数据，60 calls/min 免费，需 API Key）、Yahoo Finance（完全免费 yfinance 库，`ticker.recommendations`、`ticker.analyst_price_targets`、`ticker.recommendations_summary`，无需 API Key）；**Tier 2（免费层可用，良好补充）**：Finviz（免费 HTML 抓取，分析师目标价和评级概览）、Zacks（免费层基本评级信息，Zacks Rank 1-5）；**Tier 3（需付费 API Key，可选）**：Benzinga（分析师评级 API，实时升降级，需付费 API Key）、Seeking Alpha（分析师文章和评级，部分免费）；**Tier 4（高反爬风险，尽力而为）**：TipRanks、MarketBeat、Simply Wall St、Last10K、Wisesheets（均需 HTML 抓取且反爬风险高，失败时静默跳过）。采集时按 Tier 1 → Tier 2 → Tier 3 → Tier 4 顺序执行，高优先级源失败时自动降级到下一层，所有层均失败时返回空结果并附带状态信息
9. WHEN Stock_Crawler 采集国际财经新闻, THE Stock_Crawler SHALL 对英文内容批量调用 LLM 生成中文摘要（将多条新闻合并为一次 LLM 调用，默认每批最多 20 条），保留原文链接；LLM 翻译 prompt 中 SHALL 强调"严格基于原文翻译，不添加任何原文没有的信息"
14. WHEN 展示 LLM 翻译的中文摘要, THE Platform SHALL 在前端标注"AI 翻译摘要"标签，并提供原文链接供用户查看原始内容
10. WHEN Stock_Crawler 采集投行研报数据, THE Stock_Crawler SHALL 提取分析师姓名、所属机构、评级（买入/持有/卖出）、目标价和评级日期等结构化信息
11. THE Platform SHALL 在股票热榜中以标签区分国内资讯、国际财经和投行研报三类数据，支持按类别筛选

### 需求 2：股票热榜展示

**用户故事：** 作为用户，我希望看到清晰的股票热点列表、市场情绪全景和详情，以便快速了解市场动态和散户情绪状态。

#### 验收标准

1. WHEN 用户进入股票热榜页面, THE Platform SHALL 在页面顶部展示大盘情绪仪表盘（综合恐慌/贪婪指数、情绪标签、各分项得分概览），作为市场情绪的第一视觉焦点；仪表盘下方展示按热度排序的 Stock_News_Item 列表，每条包含标题、来源平台标识、发布时间和热度值；页面布局复用现有 HotView 的左右分栏模式（左侧列表 + 右侧详情面板）
2. WHEN 用户点击某条 Stock_News_Item, THE Platform SHALL 在右侧详情面板中展示该条目的详情信息，包括摘要内容和跳转原文的链接
3. WHEN 股票热榜页面加载时, THE Platform SHALL 显示数据的采集时间和来源平台统计信息（含国内/国际/研报分类统计）
4. THE Platform SHALL 支持按数据源平台筛选 Stock_News_Item 列表
5. THE Platform SHALL 提供手动刷新按钮，触发后重新采集数据并更新列表
6. THE Platform SHALL 提供类别筛选功能（全部/国内资讯/国际财经/投行研报），在类别内支持按具体数据源进一步筛选
7. WHEN 展示投行研报类别的条目, THE Platform SHALL 显示分析师评级标签（买入/持有/卖出，分别用绿/黄/红色区分）和目标价信息；点击展开详情时额外显示分析师姓名和所属机构
8. WHEN 展示国际财经类别的条目, THE Platform SHALL 显示原始语言标签（如"EN"）；若数据源提供情绪分析（如 Alpha Vantage/Marketaux），则额外显示情绪标签（看多/看空/中性）
9. THE Platform SHALL 在右侧详情面板中提供"一键推演"按钮，点击后跳转到行情推演页面并将选中资讯标题自动填入输入框

### 需求 3：行情推演分析

**用户故事：** 作为用户，我希望系统能基于采集到的股票资讯和散户情绪数据，对相关股票进行多角度推演分析，以便辅助我理解资讯和市场情绪对行情的潜在影响。

#### 验收标准

1. WHEN 用户在行情推演页面输入推演主题（股票名称、事件描述等）或从热搜标签中选择热点资讯, THE Stock_Analysis_Agent SHALL 自动获取相关的散户情绪数据（综合情绪指数及各分项得分），并基于资讯内容和情绪数据共同生成包含多空激辩的行情推演报告
2. WHEN Stock_Analysis_Agent 生成推演报告, THE Stock_Analysis_Result SHALL 包含情绪概况、资讯摘要、影响分析、多头激辩观点、空头激辩观点、多空交锋对话、争议性结论和风险提示八个部分
2A. THE 情绪概况部分 SHALL 展示当前综合情绪指数值、情绪标签（极度恐慌/恐慌/中性/贪婪/极度贪婪）、各分项得分（评论情绪/百度投票/AKShare 聚合/新闻情绪/融资融券）和趋势方向，作为后续分析的数据基础
3. THE 多头激辩 Agent SHALL 以坚定看多的立场，用激进有说服力的语言论证买入理由，引用具体数据、历史类比和当前散户情绪数据（如"当前情绪指数仅 25，处于恐慌区间，正是别人恐惧我贪婪的时候"）
4. THE 空头激辩 Agent SHALL 以坚定看空的立场，用犀利有冲击力的语言论证风险，揭示隐患并反驳多头论点，引用情绪数据佐证（如"情绪指数已达 85，散户极度贪婪，历史上每次到这个位置都是见顶信号"）
5. THE 多空交锋 Agent SHALL 以对话体呈现多空双方的直接交锋，轮数由用户设置的 debate_rounds 参数控制（默认 2 轮，范围 1-5），逐步升级争议强度
6. THE 争议性结论 Agent SHALL 选择一个有争议性的立场（偏多或偏空），用标题党风格输出能引发讨论的核心观点，而非给出"客观中立"的结论
7. WHILE 行情推演正在执行, THE Platform SHALL 以流式方式展示推演过程中各步骤的输出，包括当前执行的 Agent 名称和步骤内容
8. WHEN 行情推演完成, THE Platform SHALL 将推演结果缓存，相同资讯组合在 60 分钟内再次请求时直接返回缓存结果
9. IF Stock_Analysis_Agent 调用 LLM 失败, THEN THE Platform SHALL 返回错误信息并提示用户稍后重试
10. WHEN 用户进入行情推演页面, THE Platform SHALL 展示历史推演记录列表，按时间倒序排列
11. THE Platform SHALL 使用 PostgreSQL 数据库（通过 SQLAlchemy + asyncpg）持久化行情推演历史、社交内容历史和个股板块映射数据，数据库连接通过 DATABASE_URL 环境变量配置；历史查询接口支持分页（limit/offset 参数）
12. THE 行情推演页面 SHALL 提供输入框供用户直接输入推演主题（股票名称、事件描述等），支持回车键或按钮触发推演
13. THE 行情推演页面 SHALL 在输入框下方展示热搜标签（从股票热榜拉取热点资讯），点击标签自动填入输入框
14. THE 行情推演页面 SHALL 支持从股票热榜页面"一键推演"跳转过来时，自动将选中的资讯标题填入输入框

### 需求 4：前端界面改造（最大化复用现有 UI）

**用户故事：** 作为用户，我希望系统界面围绕股票资讯功能设计，同时最大化保留现有舆情分析系统的 UI 交互模式、视觉风格和组件结构，以便获得熟悉且专注的使用体验。

> **核心原则：UI 一致性优先**。新页面的布局、交互模式、视觉风格（glass-card、配色、字体、间距、动画）必须与现有 HotView 和 HomeView 保持高度一致。差异仅限于业务内容的替换（舆情→股票），不改变用户已熟悉的操作习惯和视觉体验。

#### 验收标准

1. THE Navigation_Bar SHALL 展示股票平台的功能菜单项，包括"股票热榜"、"行情推演"、"每日速报"和"设置"；导航栏的视觉样式（圆角 pill 按钮组、hover/active 状态、深色模式适配）SHALL 与现有 App.vue 导航栏保持一致
2. THE Platform SHALL 将系统名称和品牌标识更新为股票资讯相关的主题
3. WHEN 用户首次访问系统, THE Platform SHALL 默认进入股票热榜页面
4. THE Platform SHALL 保留现有的设置页面功能（LLM API 配置、主题切换等），并在此基础上扩展新配置项
5. THE 行情推演页面（StockAnalysisView）SHALL 最大化复用现有 HomeView 的完整 UI 结构和交互模式，具体包括：
   - 顶部 Header 区域：与 HomeView 相同的白色背景 + 底部边框 + 居中布局，标题使用相同的 `text-3xl md:text-5xl font-extrabold` 样式和 `gradient-text` 渐变效果
   - 搜索输入框：与 HomeView 相同的蓝色渐变光晕效果（`bg-gradient-to-r from-blue-600 to-indigo-600 blur`）、白色圆角输入框、左侧搜索图标、右侧辩论轮数选择器和启动/停止按钮
   - 热搜标签行：与 HomeView 相同的 pill 标签样式（`px-3 py-1 bg-white border border-slate-200 rounded-full`）、红色"热搜"标识、刷新按钮
   - 工作流进度条：与 HomeView 相同的 sticky 进度条（蓝色渐变进度条 + 步骤卡片网格）
   - 左侧 Agent 协作面板（lg:col-span-7）：与 HomeView 相同的 glass-card 容器、蓝色顶部边框（`border-t-4 border-t-blue-500`）、固定高度 450px、辩论气泡样式（多头绿色/空头红色/分析师紫色/系统灰色）
   - 左侧核心洞察面板：与 HomeView 相同的黄色左边框（`border-l-4 border-l-yellow-400`）、渐变背景（`from-yellow-50 to-orange-50`）
   - 右侧预览区（lg:col-span-5）：与 HomeView 相同的手机模拟器外框（320×680px、圆角 3rem、黑色边框 8px）和内部布局（状态栏 + App Header + 可滚动内容区 + 底部互动栏）
   - 底部文案生成区：与 HomeView 相同的绿色顶部边框（`border-t-4 border-t-emerald-500`）、textarea 样式、编辑/复制/导出图片/发布按钮布局
   - 从热榜"一键推演"跳转时，自动从 sessionStorage 读取资讯标题填入输入框（复用 hydrateHotTopicDraft 模式）
6. THE 股票热榜页面（StockHotView）SHALL 最大化复用现有 HotView 的完整 UI 结构和交互模式，具体包括：
   - 顶部 Header 区域：与 HotView 相同的白色背景 + 底部边框 + 左侧标题区（橙色 pill 标签 + 大标题 + 副标题）+ 右侧按钮区（刷新热榜 + 进入推演）
   - 筛选面板：与 HotView 相同的 glass-card 容器、平台筛选按钮组（圆角 pill、选中蓝色高亮）、类别筛选按钮组、排序选择器、搜索框
   - 左侧列表区（lg:col-span-7）：与 HotView 相同的卡片样式（glass-card 圆角 + 左边框 4px + 选中蓝色高亮 + hover 阴影）、排名序号样式（前三名金/银/铜渐变背景）、标题 + 来源 + 热度值布局
   - 右侧详情面板（lg:col-span-5，sticky top-24）：与 HotView 相同的 glass-card 容器、标题 + 热度 + "一键推演"按钮布局、详情内容区域（跨平台对齐、演化解读、来源链接等信息块的样式）
   - 点击卡片选中高亮（蓝色左边框 + 蓝色背景）的交互行为与 HotView 完全一致
   - 加载状态（旋转动画）和空状态（AlertCircle 图标 + 提示文字）与 HotView 一致
7. THE 股票热榜页面的"一键推演"按钮 SHALL 通过 sessionStorage 缓存选中资讯数据，然后跳转到行情推演页面，推演页面加载时自动读取并填入输入框
8. ALL 新页面 SHALL 保持与现有系统一致的视觉风格：glass-card 毛玻璃效果（`background: rgba(255,255,255,0.95); backdrop-filter: blur(10px)`）、animate-fade-in 入场动画、深色模式适配（通过 isDark computed 属性控制）、Tailwind CSS 配色方案（slate/blue/orange/emerald 色系）
9. THE 每日速报页面（DailyReportView）SHALL 采用与 HotView 一致的左右分栏布局模式（左侧内容区 lg:col-span-7 + 右侧预览区 lg:col-span-5），视觉风格与其他页面保持统一

### 需求 5：社交媒体内容生成与发布

**用户故事：** 作为用户，我希望系统能将行情推演结果自动包装为适合社交平台发布的内容（图文卡片、短文等），以便我能快速发布到小红书、微博、雪球等平台并获得关注。

#### 验收标准

1. WHEN 行情推演完成, THE Platform SHALL 在推演页面底部的文案生成区提供内容预览，用户可选择目标平台格式（小红书图文、微博短文、雪球长文、知乎长文）；所有平台格式的内容生成均应融入情绪数据洞察（综合情绪指数、关键分项得分、趋势方向），使内容更具数据说服力和传播力
2. WHEN 用户选择小红书格式, THE Platform SHALL 调用 LLM 将推演结果转化为小红书风格的争议性图文内容，标题采用争议性立场句式，正文呈现多空双方核心论点并融入情绪数据亮点（如"散户恐慌指数已飙到 85，你还敢抄底吗？"），结尾用互动引导（如"你怎么看？评论区见"）
3. WHEN 用户选择微博格式, THE Platform SHALL 从争议性结论中提取最尖锐的观点，结合情绪指数数据生成 140 字以内的短文（如"恐慌指数跌破 20，散户都在割肉，但聪明钱在进场"），用反问句收尾引发讨论
4. WHEN 用户选择雪球格式, THE Platform SHALL 生成以争议性标题开头的深度长文，完整呈现多空交锋对话，引用具体数据和情绪指数各分项得分（评论情绪、百度投票、融资融券等），结尾带免责声明
5. WHEN 用户选择知乎格式, THE Platform SHALL 生成以争议性问题为标题的深度分析长文，以"回答"体裁呈现多空双方论证，引用情绪数据作为量化论据（如"从数据看，当前综合情绪指数 72，其中散户评论贪婪度 82、融资净买入持续增加，这些信号意味着什么？"），强调逻辑推理和数据引用（而非情绪渲染），结尾带免责声明和互动引导（如"欢迎在评论区讨论你的看法"）
6. THE Platform SHALL 支持为小红书内容自动生成配图（复用现有火山引擎文生图能力），配图风格为金融/商务/数据可视化风格
7. WHEN 社交内容生成完成, THE Platform SHALL 在推演页面底部的文案生成区提供内容预览和编辑功能，用户可在发布前修改；同时在右侧小红书预览区实时展示小红书格式的内容效果
8. THE Platform SHALL 优先支持一键发布到小红书（复用现有 XHS MCP 发布能力），作为初始版本唯一的全自动发布渠道
12. WHEN 用户选择微博、雪球或知乎格式的内容, THE Platform SHALL 提供"一键复制到剪贴板"功能，用户手动粘贴到对应平台发布（半自动方案）
13. THE Platform SHALL 在初始版本中不实现微博、雪球、知乎的全自动发布功能；后续版本可通过 Playwright 浏览器自动化逐个平台补齐发布能力，但全自动发布的维护成本较高（平台 UI 改版需跟进适配），不建议初期铺开过多平台
9. THE Platform SHALL 支持每日自动生成"今日股市速报"内容，汇总当日热点资讯和关键分析；支持定时生成（默认每日 18:00 收盘后）和每小时增量检查（检测重大新闻变化时自动更新速报），定时策略可在设置中配置
10. WHEN 生成每日速报, THE Platform SHALL 输出包含大盘情绪概况（综合恐慌/贪婪指数、各分项得分变化、情绪趋势方向）、大盘概况、板块异动、热点事件解读的结构化内容；情绪概况作为速报的首要板块，为后续板块分析提供情绪背景
14. THE Platform SHALL 提供独立的"每日速报"导航 Tab 页面（路由 `/daily-report`），作为速报内容的专属入口，与行情推演页面分离
15. THE 每日速报页面 SHALL 展示当日速报内容预览、历史速报列表、速报生成状态和定时配置信息
16. THE 每日速报页面 SHALL 提供"手动生成速报"按钮，点击后立即触发速报生成流程
17. THE 每日速报页面 SHALL 提供"一键发布全平台"按钮，点击后将速报内容自动发布到所有已启用的社交平台（当前全平台 = 小红书）；发布前支持预览和编辑
18. THE 每日速报页面 SHALL 展示各平台发布状态（待发布/发布中/已发布/发布失败），支持单平台重试
19. WHEN 用户点击"一键发布全平台", THE Platform SHALL 依次向所有已启用平台发布速报内容，当前已启用平台为小红书（通过 XHS MCP 全自动发布）；后续新增平台时自动纳入全平台发布流程
20. THE 每日速报页面 SHALL 提供平台选择器（Tab 或按钮组），用户可切换查看不同平台的内容预览效果；每个平台的预览 SHALL 模拟该平台的真实排版样式（参考现有小红书手机模拟器预览模式）
21. WHEN 用户切换平台预览, THE Platform SHALL 展示该平台特有的排版预览：
    - 小红书：手机模拟器，含标题卡（emoji + 标题 + 渐变背景）、AI 配图（支持滑动切换）、正文、话题标签、底部互动栏（点赞/收藏/评论），复用现有 XiaohongshuCard 组件和手机模拟器布局
    - 微博：手机模拟器，模拟微博 App 排版，含用户头像/昵称、正文（140 字限制提示）、配图九宫格、话题标签、底部互动栏（转发/评论/点赞）
    - 雪球：桌面卡片预览，模拟雪球长文排版，含标题、正文（Markdown 渲染）、数据引用高亮、免责声明、底部互动栏
    - 知乎：桌面卡片预览，模拟知乎回答排版，含问题标题、回答正文（Markdown 渲染）、数据引用高亮、免责声明、底部互动栏（赞同/评论/收藏）
22. THE 每日速报页面的预览区 SHALL 支持内容编辑功能（复用现有 CopywritingEditor 组件模式），用户可在预览状态下修改标题、正文和配图选择/排序，编辑结果实时同步到预览
23. WHEN 用户在某个平台预览下编辑内容, THE Platform SHALL 仅修改该平台的内容副本，不影响其他平台的内容
11. ALL 社交内容在生成时 SHALL 经过合规脱敏处理（参见需求 5A）

### 需求 5A：社交内容合规与脱敏

**用户故事：** 作为用户，我希望系统在生成社交平台内容时自动对个股信息进行脱敏处理，以避免荐股合规风险，同时在系统内部保留完整信息供我参考。

#### 验收标准

1. THE Platform SHALL 提供四级脱敏策略：轻度脱敏（拼音缩写，如"贵州茅台"→"GZMT"）、中度脱敏（行业描述，如"贵州茅台"→"某白酒龙头"）、重度脱敏（纯行业，如"贵州茅台"→"白酒板块"）和不脱敏（保留原始内容，用户自行承担风险）；系统内部（行情推演页面）始终保留完整的个股名称和代码
2. WHEN 生成社交内容, THE Platform SHALL 根据当前脱敏级别自动替换个股名称：轻度脱敏时替换为拼音缩写（如"贵州茅台"→"GZMT"、"宁德时代"→"NDSD"），中度脱敏时替换为行业描述（如"贵州茅台"→"某白酒龙头"），重度脱敏时替换为纯行业板块（如"贵州茅台"→"白酒板块"）
3. WHEN 生成社交内容, THE Platform SHALL 自动将股票代码（如 600519、300750）替换为行业描述或移除
4. THE Platform SHALL 维护一个个股到板块/行业的映射表，用于脱敏替换（可通过 AKShare 的板块数据自动构建）
5. ALL 社交内容 SHALL 强制附带免责声明："以上内容仅为市场观点讨论，不构成任何投资建议"
6. WHEN 社交内容生成完成进入编辑阶段, THE Platform SHALL 允许用户手动修改脱敏后的内容（包括恢复个股名称），显示合规风险提示，但不拦截发布操作，用户自行承担风险
7. THE Platform SHALL 在设置页面提供脱敏级别选择器（四级：轻度/中度/重度/不脱敏），支持为每个社交平台单独设置脱敏级别覆盖默认值；选择"不脱敏"时显示风险警告
8. THE Platform SHALL 支持自定义脱敏规则，用户可添加额外的敏感词和替换词
9. THE Platform SHALL 为每个社交平台配置推荐的默认脱敏级别（小红书：中度/行业描述，微博：轻度/拼音缩写，雪球：轻度/拼音缩写，知乎：轻度/拼音缩写），用户可在设置中覆盖

### 需求 6：清理旧舆论分析代码

**用户故事：** 作为开发者，我希望移除系统中所有与舆论分析相关的后端和前端代码，以保持代码库整洁，避免维护负担。

#### 验收标准

1. THE Platform SHALL 移除所有舆论分析相关的后端服务文件（如 hotnews_interpreter.py、hotnews_signals.py、hotnews_alignment.py、hotnews_llm_enricher.py、workflow.py、workflow_status.py 等）
2. THE Platform SHALL 移除所有舆论分析相关的前端视图文件（如 HomeView.vue、HotView.vue、DataView.vue、ArchView.vue、VisionView.vue 等）
3. THE Platform SHALL 移除所有舆论分析相关的前端组件（如 DebateTimeline.vue、ThinkingChain.vue、InsightCard.vue、RadarChart.vue 等）
4. THE Platform SHALL 清理 `app/api/endpoints.py` 中舆论分析相关的 API 路由
5. THE Platform SHALL 清理 `src/api/index.js` 中舆论分析相关的 API 方法
6. THE Platform SHALL 清理 stores 中舆论分析相关的状态管理逻辑
7. THE Platform SHALL 移除 `opinion_mcp/` 目录下的舆论分析 MCP 工具代码
8. AFTER 清理完成, THE Platform SHALL 确保系统正常启动且无引用缺失错误

### 需求 7：后端 API

**用户故事：** 作为开发者，我希望后端提供清晰的股票资讯、行情推演和社交内容生成 API，以便前端能够获取数据和触发分析。

#### 验收标准

1. THE Platform SHALL 提供股票资讯相关的 API 端点，包括资讯列表、资讯详情和数据源管理
2. THE Platform SHALL 提供行情推演相关的 API 端点，包括触发推演（SSE 流式）、历史记录和结果详情
3. THE Platform SHALL 提供社交内容生成相关的 API 端点，包括生成内容、预览、编辑和发布
4. WHEN API 接收到请求, THE Platform SHALL 对请求参数进行校验，并在参数无效时返回包含错误描述的 400 状态码响应
5. THE Platform SHALL 保留现有的通用 API 端点（健康检查、用户设置、模型管理等）

### 需求 8：数据源 API Key 管理

**用户故事：** 作为用户，我希望能在设置页面中配置和管理各数据源的 API Key，并测试其连通性，以便灵活控制启用哪些数据源。

#### 验收标准

1. THE Platform SHALL 在设置页面提供数据源 API Key 配置区域，分为"国际财经新闻"和"投行研报"两组
2. THE Platform SHALL 支持配置以下 API Key：Finnhub、NewsAPI、Alpha Vantage、Marketaux（国际财经）；Benzinga、Seeking Alpha（投行研报，可选）
3. THE Platform SHALL 为每个数据源提供启用/禁用开关，禁用的数据源在采集时自动跳过
4. THE Platform SHALL 提供 API Key 连通性测试按钮，点击后向对应数据源发送测试请求并显示成功/失败状态
5. WHEN 用户保存 API Key 配置, THE Platform SHALL 将配置持久化到用户设置中，重启后保留
6. THE Platform SHALL 提供后端 API 端点用于保存、读取和测试数据源 API Key 配置
7. WHEN 某数据源的 API Key 未配置且该数据源需要 API Key, THE Platform SHALL 在设置页面显示"未配置"状态提示，采集时自动跳过该数据源


### 需求 9：散户情绪分析（混合数据源架构）——系统核心引擎

> **重要说明**：散户情绪分析是本系统的核心引擎和第一差异化能力。需求 9 是需求 3（行情推演）和需求 5（社交内容生成）的数据基础——推演分析依赖情绪数据提供市场温度参考，社交内容依赖情绪洞察增强说服力和传播力。虽然在需求编号上排在后面，但在系统架构中，情绪数据采集与分析是与资讯采集（需求 1）同等重要的基础设施层。

**用户故事：** 作为用户，我希望系统能通过混合数据源策略——结合散户评论 LLM 情绪分析、AKShare 聚合指标、百度股市通投票数据、新闻情绪指数和融资融券数据——生成综合恐慌/贪婪指数，以便我能更全面、更准确地了解市场情绪变化趋势，并在行情推演中参考情绪数据。

#### 验收标准

##### 9A：散户评论数据采集

1. THE Sentiment_Crawler SHALL 支持从以下 Sentiment_Source 采集散户评论数据：东方财富股吧（通过 HTTP 抓取股吧帖子列表和评论，AKShare `stock_comment_em()` 仅提供聚合指标不含原始评论文本）、雪球社区（热帖和评论，需 Cookie + User-Agent 轮换，反爬较严格）、同花顺社区（个股讨论区，需 JS 逆向处理 Cookie 加密，维护成本较高）
2. WHEN Sentiment_Crawler 执行采集任务, THE Sentiment_Crawler SHALL 返回包含评论内容、发布时间、来源平台、关联股票代码和作者昵称的 Sentiment_Comment 列表
3. THE Sentiment_Crawler SHALL 采用增量采集策略：基于时间窗口（默认最近 24 小时）采集新增评论，避免全量拉取历史数据
4. THE Sentiment_Crawler SHALL 支持按个股代码采集特定股票的讨论评论，也支持采集综合讨论区的整体市场评论
5. THE Sentiment_Crawler SHALL 通过 IP 代理池轮换机制降低反爬风险，支持配置代理列表（HTTP/SOCKS5），每次请求随机选择代理
6. THE Sentiment_Crawler SHALL 实现请求频率自适应控制：正常状态下按配置的 cooldown 间隔采集，检测到反爬信号（HTTP 403/429、验证码页面、空响应）时自动降速（cooldown 翻倍），连续 3 次正常响应后恢复原速
7. THE Sentiment_Crawler SHALL 实现 Cookie 池管理：维护多组有效 Cookie，请求时轮换使用，Cookie 失效时自动标记并尝试刷新
8. IF Sentiment_Source 触发反爬封禁（连续 3 次请求失败）, THEN THE Sentiment_Crawler SHALL 对该数据源执行降级策略：暂停采集该源 30 分钟，期间使用最近一次成功采集的缓存数据，30 分钟后自动恢复尝试
8A. IF 所有 Sentiment_Source 评论爬虫均触发封禁降级, THEN THE Platform SHALL 仅使用 AKShare 聚合指标（百度投票、千股千评、新闻情绪指数、融资融券数据、雪球热度数据）计算情绪指数，评论情绪分权重（40%）自动按比例重分配给其他可用数据源
9. THE Sentiment_Crawler SHALL 对采集到的评论进行基础清洗：去除纯表情/纯符号评论、去除广告和垃圾内容（基于关键词黑名单过滤）、去除重复评论（基于内容哈希去重）

##### 9B：混合数据源聚合指标采集

10. THE Platform SHALL 通过 AKShare 采集以下聚合情绪指标（无需爬虫，直接调用 Python 库）：
    - `stock_comment_em()`：东方财富千股千评/市场关注度数据（综合评分、关注度排名）
    - `stock_comment_detail_scrd_focus_em()`：用户关注指数（关注度变化趋势）
    - `stock_hot_rank_em()`：个股人气榜排名（人气值、排名变化）
    - `stock_hot_keyword_em()`：热门关键词（市场讨论焦点）
11. THE Platform SHALL 通过 AKShare 采集百度股市通散户投票数据：
    - `stock_zh_vote_baidu(stock_code)`：获取指定个股的看涨/看跌投票比例，作为散户情绪的直接量化指标
12. THE Platform SHALL 通过 AKShare 采集新闻情绪指数：
    - `index_news_sentiment_scope()`：数库 A 股新闻情绪指数，提供基于新闻文本的市场情绪量化数据
13. THE Platform SHALL 通过 AKShare 采集融资融券数据作为机构情绪参考：
    - `stock_margin_detail_szse()` / `stock_margin_detail_sse()`：融资融券余额变化，融资净买入为看多信号，融券净卖出为看空信号
14. THE Platform SHALL 通过 AKShare 采集雪球平台热度数据（替代高风险的雪球评论爬取作为补充）：
    - `stock_hot_follow_xq()`：雪球关注排行（关注人数变化）
    - `stock_hot_tweet_xq()`：雪球讨论排行（讨论热度）

##### 9C：情绪分析与综合指数计算

15. WHEN 一批 Sentiment_Comment 采集完成, THE Sentiment_Analyzer SHALL 批量调用 LLM 对评论进行情绪分类，每条评论标记为"恐慌"、"贪婪"或"中性"三类之一，并给出 0-100 的情绪强度分数
16. THE Sentiment_Analyzer SHALL 将多条评论合并为一次 LLM 调用（默认每批最多 50 条），以减少 API 调用次数和成本
17. THE Sentiment_Analyzer SHALL 基于混合数据源计算综合 Sentiment_Index（0-100），采用加权模型：
    - 评论情绪分（权重 40%）：LLM 分析散户评论的贪婪占比 × 100
    - 百度投票分（权重 20%）：百度股市通看涨比例 × 100
    - AKShare 聚合分（权重 15%）：基于千股千评综合评分和人气排名变化归一化
    - 新闻情绪分（权重 15%）：数库新闻情绪指数归一化到 0-100
    - 融资融券分（权重 10%）：融资净买入变化率归一化到 0-100
    - 当某个数据源不可用时，自动将其权重按比例分配给其他可用数据源
18. THE Platform SHALL 支持两种维度的情绪指数：整体大盘情绪指数（基于综合讨论区评论 + 大盘级聚合指标）和个股情绪指数（基于特定股票讨论区评论 + 个股级聚合指标）
19. WHEN 情绪指数计算完成, THE Platform SHALL 将 Sentiment_Snapshot（含综合指数值、各分项得分、评论样本数、恐慌/贪婪/中性占比、数据源可用性状态、时间戳）持久化到数据库
20. THE Platform SHALL 按可配置的时间间隔（默认每 2 小时）自动执行一轮情绪采集和分析，生成新的 Sentiment_Snapshot

##### 9D：情绪指数可视化

21. THE Platform SHALL 在股票热榜页面顶部展示当前大盘情绪指数仪表盘，包含综合指数数值、情绪标签（极度恐慌/恐慌/中性/贪婪/极度贪婪）和颜色指示（红→黄→绿渐变）
22. THE Platform SHALL 提供情绪指数时序图表（K 线风格），展示过去 30 天的情绪指数变化趋势，X 轴为时间，Y 轴为指数值（0-100），支持缩放和时间范围选择；图表支持切换显示综合指数或各分项指数（评论情绪/百度投票/AKShare 聚合/新闻情绪/融资融券）
23. WHEN 用户查看个股详情, THE Platform SHALL 展示该股票的个股情绪指数及其时序趋势图
24. THE Platform SHALL 在情绪时序图表中标注关键事件节点（如指数突破 80 或跌破 20 时），鼠标悬停显示该时间点的代表性评论摘要和各分项得分

##### 9E：与行情推演集成

25. WHEN 用户在行情推演页面输入推演主题, THE Stock_Analysis_Agent SHALL 自动查询相关股票或大盘的最新情绪指数数据（含综合指数和各分项得分），作为推演分析的参考输入
26. THE Stock_Analysis_Result SHALL 新增 sentiment_context 字段，包含推演时引用的情绪指数数据（综合指数值、各分项得分、趋势方向、样本量、数据源可用性）
27. WHEN 行情推演报告生成时, THE 影响分析 Agent SHALL 在分析中引用当前散户情绪状态（如"当前综合情绪指数为 75（贪婪区间），其中散户评论情绪偏贪婪（82）、百度投票看涨比例 68%、融资净买入持续增加，需警惕追高风险"）
28. THE Platform SHALL 在行情推演页面的输入区域旁展示当前大盘情绪指数的迷你仪表盘，供用户参考

##### 9F：情绪数据管理

29. THE Platform SHALL 在设置页面提供情绪采集配置区域：采集频率设置（默认每 2 小时）、代理池配置（支持添加/删除代理地址）、各情绪数据源的启用/禁用开关（分为"评论采集源"和"聚合指标源"两组）、各分项权重配置（允许用户自定义加权比例）
30. THE Platform SHALL 提供情绪采集状态监控面板，展示各数据源的最近采集时间、成功率、当前状态（正常/降速/暂停），聚合指标源单独展示 AKShare 调用状态
31. THE Platform SHALL 对超过 90 天的 Sentiment_Comment 原始数据执行自动归档清理，仅保留 Sentiment_Snapshot 聚合数据以节省存储空间
