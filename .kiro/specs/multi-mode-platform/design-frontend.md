# 设计文档：前端组件与界面

> 本文件是 design.md 拆分后的子文件。完整设计文档包含：
> - [design-overview.md](design-overview.md)  概述、依赖、策略、架构、数据库
> - [design-frontend.md](design-frontend.md)  前端组件、路由、状态管理
> - [design-backend-services.md](design-backend-services.md)  后端服务（爬虫、推演、内容生成、合规脱敏）
> - [design-sentiment.md](design-sentiment.md) — 散户情绪分析全链路
> - [design-data-models.md](design-data-models.md)  数据模型、正确性属性、错误处理、测试策略

## UI 一致性原则

> **核心原则**：新页面必须最大化复用现有 HotView 和 HomeView 的 UI 交互模式、视觉风格和组件结构。差异仅限于业务内容的替换（舆情→股票），不改变用户已熟悉的操作习惯和视觉体验。

**必须保持一致的视觉元素：**
- **glass-card 容器样式**：所有卡片统一使用 `glass-card rounded-xl/2xl` + `shadow-lg` + `border border-slate-100`
- **12 列栅格布局**：主内容区统一使用 `grid grid-cols-1 lg:grid-cols-12 gap-6 items-start`，左侧 `lg:col-span-7`，右侧 `lg:col-span-5`
- **排名徽章渐变**：Top 1 金色 `bg-gradient-to-br from-amber-400 via-orange-500 to-amber-600`，Top 2 银色 `from-slate-300 via-slate-400 to-slate-500`，Top 3 铜色 `from-amber-200 via-orange-200 to-amber-300`，其余蓝色 `from-blue-50 via-indigo-50 to-blue-100`
- **选中高亮**：蓝色左边框 `border-l-4 border-l-blue-600 bg-blue-50 shadow-lg`，未选中 `border-l-slate-200 hover:border-l-blue-400`
- **筛选按钮**：圆角 pill `px-3 py-1 rounded-full border text-xs font-semibold`，选中态 `bg-blue-50 border-blue-300 text-blue-600`
- **热度标签**：橙色 pill `text-xs font-bold text-orange-600 bg-orange-50 px-3 py-1 rounded-full`
- **Header 渐变文字**：`gradient-text` 类（蓝色到靛蓝渐变）
- **输入框光晕**：`bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl blur opacity-25`
- **进度条**：`sticky top-16 z-40`，蓝色渐变 `bg-gradient-to-r from-blue-500 to-indigo-600`
- **辩论气泡**：`glass-card rounded-xl border-t-4 border-t-blue-500 h-[450px] shadow-lg`
- **手机模拟器**：`rounded-[3rem] w-full max-w-[320px] h-[680px]`，`border: 8px solid #000000`
- **文案区**：`border-t-4 border-t-emerald-500` 绿色顶部边框
- **导航栏**：`rounded-full` pill 按钮，暗色模式切换，设置图标按钮

## 组件与接口

### 前端组件

#### 1. App.vue 改造

替换现有导航栏内容，改为股票平台的四个导航项：
- 股票热榜（默认页，路由 `/`）
- 行情推演（路由 `/analysis`）
- 每日速报（路由 `/daily-report`）
- 设置（路由 `/settings`）

使用 `<router-view>` 渲染当前路由对应的视图组件，NavigationBar 使用 `<router-link>` 实现导航切换和高亮。移除 HotView、HomeView、DataView、ArchView、VisionView 的引用。

#### 2. StockHotView（`src/views/StockHotView.vue`）

股票热榜主视图，**直接复制 HotView.vue 的完整 HTML 结构和 CSS 类名**，仅替换业务数据绑定（舆情热点→股票资讯）。

> **UI 一致性要求**：StockHotView 的布局、交互和视觉必须与现有 HotView 保持像素级一致。以下标注了必须保留的具体 CSS 类名和组件结构，开发时应直接从 HotView.vue 复制模板代码再修改数据绑定。

- 顶部 Header（**复制 HotView header 结构**）：
  - 外层 `<header class="relative bg-white border-b border-slate-100 pt-10 pb-6 px-4">`
  - 左侧标题区：橙色 pill 标签 `inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-semibold`（图标改为股票相关）+ 大标题 `text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight` + 副标题 `text-slate-500 text-sm`
  - 右侧按钮区：与 HotView 相同的"刷新热榜"按钮样式 + "进入推演"蓝色按钮样式
  - 新增：大盘情绪仪表盘（SentimentGauge full 模式），作为页面第一视觉焦点
- 筛选面板（**复制 HotView glass-card 筛选面板结构**）：
  - 外层 `glass-card rounded-2xl p-4 shadow-lg`
  - 平台筛选按钮组：与 HotView 相同的 `px-3 py-1 rounded-full border text-xs font-semibold` pill 按钮，选中态 `bg-blue-50 border-blue-300 text-blue-600`（平台列表改为股票数据源）
  - 类别筛选按钮组：全部 / 国内资讯 / 国际财经 / 投行研报（与 HotView 分区筛选相同样式）
  - 排序选择器 + 搜索框：与 HotView 相同的 `select` 和 `input` 样式
- 左侧列表区（**复制 HotView 列表卡片结构**，`lg:col-span-7`）：
  - 资讯卡片：与 HotView 相同的 `glass-card rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg border-l-4` 结构
  - 排名徽章：与 HotView 相同的金/银/铜渐变样式（Top 1/2/3）和蓝色默认样式
  - 选中高亮：与 HotView 相同的 `border-l-blue-600 bg-blue-50 shadow-lg`
  - 热度标签：与 HotView 相同的 `text-xs font-bold text-orange-600 bg-orange-50 px-3 py-1 rounded-full`
  - 投行研报条目额外显示评级标签（买入/持有/卖出，绿/黄/红色）和目标价
  - 国际新闻条目显示原始语言标签和情绪标签（若有）
  - LLM 翻译的中文摘要条目显示"AI 翻译摘要"标签，并提供原文链接
- 右侧详情面板（**复制 HotView 详情面板结构**，`lg:col-span-5`，sticky）：
  - 外层 `glass-card rounded-2xl p-5 shadow-lg border border-slate-100 sticky top-24`
  - 标题 + 热度 pill + "一键推演"蓝色圆角按钮：与 HotView 相同样式
  - 新增：个股情绪迷你仪表盘（若资讯关联个股）
  - 详情内容区：与 HotView 相同的 `rounded-xl border border-slate-100 bg-slate-50 p-3` 卡片样式
  - 未选中时显示占位提示（与 HotView 相同的 AlertCircle 图标 + 提示文字）
- "一键推演"按钮通过 sessionStorage 缓存选中资讯数据，然后 `router.push` 跳转到行情推演页面

#### 3. StockAnalysisView（`src/views/StockAnalysisView.vue`）

行情推演视图，**直接复制 HomeView.vue 的完整 HTML 结构和 CSS 类名**，仅替换业务数据绑定（舆情推演→行情推演）。

> **UI 一致性要求**：StockAnalysisView 的布局、交互和视觉必须与现有 HomeView 保持像素级一致。以下标注了必须保留的具体 CSS 类名和组件结构，开发时应直接从 HomeView.vue 复制模板代码再修改数据绑定。

**顶部输入区（复制 HomeView header 结构）：**
- 外层 `<header class="relative bg-white border-b border-slate-100 pt-12 pb-8 px-4">`
- 居中容器 `max-w-4xl mx-auto text-center`
- 系统标题：与 HomeView 相同的 `text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight` + `gradient-text` 渐变效果（文案改为"股票行情推演与内容创作引擎"）
- 搜索输入框（**复制 HomeView 输入框完整结构**）：
  - 蓝色渐变光晕 `absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl blur opacity-25 group-hover:opacity-50`
  - 白色圆角输入框 `relative flex items-center bg-white rounded-xl shadow-xl border border-slate-200 p-1`
  - 左侧 Search 图标 + input + 分隔线 + 辩论轮数选择器 + 启动/停止按钮（与 HomeView 完全相同的样式和布局）
  - 新增：输入框右侧大盘情绪迷你仪表盘（SentimentGauge mini 模式）
- 热搜标签行（**复制 HomeView 热搜标签结构**）：
  - 与 HomeView 相同的 `flex flex-nowrap justify-center items-center gap-2 text-xs text-slate-500` 布局
  - 红色"热搜"标签 `font-bold text-red-500` + TrendingUp 图标
  - pill 标签按钮 `px-3 py-1 bg-white border border-slate-200 rounded-full hover:border-blue-300 hover:text-blue-600`（数据源改为股票热榜 API）
  - 刷新按钮 `hover:bg-slate-100 rounded-full`
- 从热榜"一键推演"跳转过来时，自动从 sessionStorage 读取资讯标题填入输入框

**工作流进度条（复制 HomeView 进度条结构）：**
- 与 HomeView 相同的 `sticky top-16 z-40 bg-white border-b border-slate-200 shadow-sm` 定位
- 进度条 `bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full`
- 步骤卡片网格：与 HomeView 相同的 `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2` 布局（步骤名称改为：情绪数据获取 → 资讯汇总 → 影响分析 → 多头激辩 → 空头激辩 → 多空交锋 → 争议性结论 → 文案生成 → 配图生成）

**主内容区（复制 HomeView 左右分栏结构）：**
- 外层 `grid grid-cols-1 lg:grid-cols-12 gap-6 items-start`
- 左侧（`lg:col-span-7`）：
  - Agent 协作面板（**复制 HomeView 辩论面板结构**）：与 HomeView 相同的 `glass-card rounded-xl border-t-4 border-t-blue-500 h-[450px] shadow-lg` 容器，流式展示辩论气泡（多头绿色/空头红色/分析师紫色/系统灰色）
  - 核心洞察面板（**复制 HomeView Grand Insight 结构**）：与 HomeView 相同的 `glass-card rounded-xl p-5 shadow-md border-l-4 border-l-yellow-400` 容器，展示争议性结论
- 右侧（`lg:col-span-5`）：
  - 多平台预览区（PlatformPreview 组件）：平台选择器 Tab + 对应平台的排版预览（默认小红书），实时预览生成的社交内容；支持左右滑动切换图片（小红书/微博模式）

**底部文案生成区（复制 HomeView 文案区结构，集成多平台预览）：**
- 与 HomeView 相同的 `border-t-4 border-t-emerald-500` 绿色顶部边框容器
- 文案文本框：与 HomeView 相同的 textarea 样式
- 多平台预览区（PlatformPreview 组件）：平台选择器 Tab（小红书/微博/雪球/知乎）+ 对应平台的排版预览
- 操作按钮：与 HomeView 相同的编辑、复制全文、导出全部图片按钮样式
- 小红书 MCP 状态指示 + 发布到小红书按钮（仅小红书格式时显示）
- 非小红书平台显示"一键复制到剪贴板"按钮（微博/雪球/知乎采用半自动方案）
- 编辑面板（CopywritingEditor 组件模式）：支持修改标题、正文、选择/排序配图，编辑仅影响当前平台的内容副本

**历史记录：**
- 页面底部或侧边展示历史推演记录列表，点击可查看详情

#### 4A. DailyReportView（`src/views/DailyReportView.vue`）

每日速报独立视图，作为专属导航 Tab 页面，提供速报生成、多平台预览、编辑和一键发布全平台功能。

> **UI 一致性要求**：DailyReportView 的整体布局必须遵循与 HotView/HomeView 相同的视觉风格。左右分栏使用相同的 12 列栅格（7+5），卡片使用相同的 glass-card 样式，按钮和标签使用相同的配色和圆角。

**顶部 Header（遵循 HotView header 风格）：**
- 外层 `<header class="relative bg-white border-b border-slate-100 pt-10 pb-6 px-4">`（与 HotView 一致）
- 页面标题"每日股市速报" + 当前日期（使用与 HotView 相同的标题字号和样式）
- 大盘情绪迷你仪表盘（SentimentGauge mini 模式）
- "手动生成速报"按钮（与 HotView "刷新热榜"按钮相同样式）
- 速报定时状态指示（如"下次自动生成：18:00"）

**速报内容区（主体，左右分栏，遵循 HotView/HomeView 栅格布局）：**
- 外层 `grid grid-cols-1 lg:grid-cols-12 gap-6 items-start`（与 HotView/HomeView 一致）
- 左侧（`lg:col-span-7`）：当日速报原始内容预览卡片（`glass-card rounded-xl` 样式，与 HotView 卡片一致）：
  - 情绪概况板块：综合恐慌/贪婪指数、各分项得分变化、趋势方向
  - 大盘概况板块：主要指数涨跌、成交量
  - 板块异动板块：涨幅/跌幅前列板块
  - 热点事件解读板块：当日最具争议话题
  - 速报生成中时显示加载动画和进度提示
  - 速报未生成时显示占位提示和"立即生成"引导（与 HotView 未选中时的占位提示风格一致）
- 右侧（`lg:col-span-5`）：多平台预览区（PlatformPreview 组件）：
  - 平台选择器 Tab 栏（小红书 / 微博 / 雪球 / 知乎），切换后展示对应平台的排版预览
  - 预览区域根据当前选中平台渲染对应的预览组件（详见 PlatformPreview 组件设计）
  - 预览区下方显示"编辑"按钮，点击进入编辑模式（CopywritingEditor 组件模式），编辑仅影响当前平台的内容副本

**平台发布区（底部）：**
- "一键发布全平台"按钮（醒目样式）：点击后依次向所有已启用平台发布
  - 当前已启用平台：小红书（全自动，通过 XHS MCP）
  - 后续新增平台时自动纳入发布流程
- 各平台发布状态卡片（横向排列）：显示平台图标 + 状态（待发布/发布中/已发布/发布失败）+ 单平台重试按钮
- 非小红书平台额外显示"复制到剪贴板"按钮（半自动方案）

**历史速报列表（底部折叠区）：**
- 按日期倒序展示历史速报列表
- 每条显示日期、情绪指数摘要、发布状态
- 点击展开查看完整速报内容

#### 4B. PlatformPreview 多平台预览组件（`src/components/PlatformPreview.vue`）

多平台预览包装组件，提供平台选择器 Tab 和对应平台的预览渲染。被 DailyReportView 和 StockAnalysisView 底部文案区共同使用：

**Props：**
- `platformContents`: `Dict[string, PlatformContent]` — 各平台的内容数据（title、body、images、tags），key 为平台 ID（xhs/weibo/xueqiu/zhihu）
- `selectedPlatform`: `string` — 当前选中的平台 ID
- `isEditing`: `boolean` — 是否处于编辑模式
- `editableContent`: `object` — 当前平台的可编辑内容

**Events：**
- `@update:selectedPlatform` — 平台切换事件
- `@startEditing` — 进入编辑模式
- `@updateContent(platform, updates)` — 更新指定平台的内容

**内部结构：**
- 顶部平台选择器 Tab 栏：四个 Tab 按钮（小红书/微博/雪球/知乎），当前选中 Tab 高亮，每个 Tab 显示平台图标和名称
- 预览区域：根据 `selectedPlatform` 动态渲染对应的预览组件：
  - `xhs` → XiaohongshuPreview（手机模拟器，复用现有 XiaohongshuCard + 手机框架）
  - `weibo` → WeiboCard（手机模拟器）
  - `xueqiu` → XueqiuCard（桌面卡片）
  - `zhihu` → ZhihuCard（桌面卡片）
- 预览区下方操作栏：编辑按钮 + 复制全文按钮 + 平台特有操作（小红书显示发布按钮，其他平台显示"复制到剪贴板"）

#### 4C. XiaohongshuPreview 小红书预览组件（`src/components/XiaohongshuPreview.vue`）

从现有 HomeView.vue 中的手机模拟器预览区提取为独立组件，复用现有 XiaohongshuCard 组件：

**Props：**
- `title`: `string` — 标题
- `body`: `string` — 正文内容
- `images`: `string[]` — 配图 URL 列表
- `tags`: `string[]` — 话题标签
- `titleEmoji`: `string` — 标题卡 emoji
- `titleTheme`: `string` — 标题卡主题色

**内部结构（复用现有 HomeView 手机模拟器布局）：**
- 手机外框（320×680px，圆角 3rem，黑色边框 8px）
- 状态栏（时间 09:41 + 灵动岛 + WiFi 图标）
- App Header（头像 + 昵称 + 已关注按钮 + 分享图标）
- 可滚动内容区：
  - 图片区域（3:4 比例）：标题卡（XiaohongshuCard 组件）+ AI 配图，支持左右滑动切换，底部圆点指示器和页码
  - 文案区域：标题（粗体）+ 正文（Markdown 渲染）+ 话题标签
- 底部固定互动栏：输入框 + 点赞/收藏/评论计数

#### 4D. WeiboCard 微博预览组件（`src/components/WeiboCard.vue`）

模拟微博 App 排版的手机模拟器预览：

**Props：**
- `title`: `string` — 标题（微博不单独显示标题，融入正文）
- `body`: `string` — 正文内容（140 字限制提示）
- `images`: `string[]` — 配图 URL 列表
- `tags`: `string[]` — 话题标签

**内部结构：**
- 手机外框（同小红书尺寸 320×680px，圆角 3rem，黑色边框 8px）
- 状态栏（时间 + 灵动岛 + WiFi/信号图标）
- 微博 App Header（微博 logo + "首页" 标题 + 搜索图标）
- 可滚动内容区：
  - 用户信息栏：头像（圆形）+ 昵称 + 认证标识（V）+ 发布时间 + "关注"按钮
  - 正文区域：正文内容（超过 140 字时显示红色字数提示"已超出 140 字限制"）
  - 话题标签：以 `#话题#` 格式显示，蓝色文字
  - 配图区域：九宫格布局（1 图全宽、2-3 图横排、4 图 2×2、5-9 图 3×3），图片点击可预览
- 底部固定互动栏：转发 / 评论 / 点赞（带计数）

#### 4E. XueqiuCard 雪球预览组件（`src/components/XueqiuCard.vue`）

模拟雪球长文排版的桌面卡片预览：

**Props：**
- `title`: `string` — 文章标题
- `body`: `string` — 正文内容（Markdown 格式）
- `images`: `string[]` — 配图 URL 列表
- `tags`: `string[]` — 话题标签

**内部结构：**
- 桌面卡片容器（max-width: 680px，白色背景，圆角 12px，阴影）
- 雪球 Header 栏：雪球 logo + "长文" 标签
- 用户信息栏：头像 + 昵称 + 认证标识 + 发布时间 + "关注" 按钮
- 文章标题：大号粗体
- 正文区域（Markdown 渲染）：
  - 支持标题层级（h2/h3）、加粗、列表、引用块
  - 数据引用高亮：包含数字和百分比的段落以浅蓝色背景高亮显示
  - 配图穿插在正文中（居中显示，带圆角）
- 免责声明区域：灰色背景条，显示免责声明文本
- 底部互动栏：赞同 / 评论 / 转发 / 收藏（带计数）

#### 4F. ZhihuCard 知乎预览组件（`src/components/ZhihuCard.vue`）

模拟知乎回答排版的桌面卡片预览：

**Props：**
- `title`: `string` — 问题标题
- `body`: `string` — 回答正文（Markdown 格式）
- `images`: `string[]` — 配图 URL 列表
- `tags`: `string[]` — 话题标签

**内部结构：**
- 桌面卡片容器（max-width: 680px，白色背景，圆角 12px，阴影）
- 知乎 Header 栏：知乎 logo + "回答" 标签
- 问题标题区域：大号粗体，蓝色文字，模拟知乎问题标题样式
- 回答者信息栏：头像 + 昵称 + 认证标识 + "关注" 按钮
- 回答正文区域（Markdown 渲染）：
  - 支持标题层级、加粗、列表、引用块、代码块
  - 数据引用高亮：包含数字和百分比的段落以浅蓝色背景高亮显示
  - 配图穿插在正文中（居中显示，带圆角和图注）
- 免责声明区域：灰色分隔线 + 免责声明文本
- 底部互动栏：赞同（蓝色按钮）/ 反对 / 评论 / 收藏 / 分享（带计数）

#### 5. 前端 API 层（`src/api/index.js`）

新增股票相关 API 方法：

```javascript
// 股票资讯（含国内、国际、投行研报）
async getStockNews(limit, source, category, forceRefresh) { ... }
async getStockSources() { ... }

// 行情推演（SSE 流式）
async analyzeStock(payload, onMessage) { ... }
async getStockAnalysisHistory(limit, offset) { ... }
async getStockAnalysisDetail(analysisId) { ... }

// 投行研报专用
async getConsensusRating(symbol) { ... }
async getAnalystRatings(symbol, source) { ... }

// 社交内容生成与发布
async generateSocialContent(analysisId, platform) { ... }
async generateDailyReport() { ... }
async getDailyReportLatest() { ... }
async getDailyReportHistory(limit, offset) { ... }
async publishDailyReportAllPlatforms(contentId) { ... }
async publishToXiaohongshu(contentId) { ... }
async getSocialContentHistory(limit, offset) { ... }

// 数据源 API Key 管理
async getDataSourceConfig() { ... }
async saveDataSourceConfig(config) { ... }
async testDataSourceConnection(sourceId) { ... }
```

#### 6. 前端路由配置（`src/router/index.js`）

使用 Vue Router 实现 SPA 路由，支持浏览器前进/后退和 URL 直接访问：

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { 
    path: '/', 
    name: 'stock-hot',
    component: () => import('@/views/StockHotView.vue'),
    meta: { label: '股票热榜' }
  },
  { 
    path: '/analysis', 
    name: 'stock-analysis',
    component: () => import('@/views/StockAnalysisView.vue'),
    meta: { label: '行情推演' }
  },
  { 
    path: '/daily-report', 
    name: 'daily-report',
    component: () => import('@/views/DailyReportView.vue'),
    meta: { label: '每日速报' }
  },
  { 
    path: '/settings', 
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { label: '设置' }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
```

所有路由使用懒加载（`() => import(...)`）以优化首屏加载。使用 `createWebHistory()` 的 history 模式，生产环境需配合 FastAPI catch-all 路由（详见"Vue Router + FastAPI SPA 部署方案"章节）。

StockHotView 中点击"一键推演"时，通过 `sessionStorage.setItem('stock_topic_draft', JSON.stringify(selectedTopic))` 缓存选中资讯，然后 `router.push({ name: 'stock-analysis' })` 跳转。StockAnalysisView 在 `onMounted` 时检查 sessionStorage 并自动填入输入框（复用现有 HomeView 的 `hydrateHotTopicDraft` 模式）。

App.vue 使用 `<router-view>` 替代动态组件，NavigationBar 使用 `<router-link>` 实现导航高亮。导航项为四个 Tab：股票热榜、行情推演、每日速报、设置。

#### 7. 前端状态管理（`src/stores/`）

替换现有的 analysis.js、workflow.js、outputs.js，新建以下 Pinia stores：

**`src/stores/stockNews.js`** — 股票资讯状态：

```javascript
export const useStockNewsStore = defineStore('stockNews', {
  state: () => ({
    newsList: [],              // StockNewsItem 列表
    sourceStats: {},           // 各平台采集数量
    categoryStats: {},         // 各类别数量（domestic/international/research_report）
    collectionTime: '',        // 采集时间
    fromCache: false,          // 是否来自缓存
    loading: false,            // 加载状态
    error: null,               // 错误信息
    selectedCategory: 'all',   // 当前类别筛选（all/domestic/international/research_report）
    selectedSource: 'all',     // 当前平台筛选
    selectedTopic: null,       // 当前选中的热点（用于右侧详情面板）
  }),
  getters: {
    filteredNews: (state) => { /* 按 category 和 source 筛选 */ },
    availableSources: (state) => { /* 当前类别下可用的数据源列表 */ },
    trendingTopics: (state) => { /* 取前 N 条热点用于推演页面的热搜标签 */ },
  },
  actions: {
    async fetchNews(forceRefresh = false) { /* 调用 API 获取资讯 */ },
    selectTopic(topic) { /* 选中某条热点 */ },
  },
})
```

**`src/stores/stockAnalysis.js`** — 行情推演与内容生成状态（合并推演 + 社交内容，因为内容生成集成在推演页面中）：

```javascript
export const useStockAnalysisStore = defineStore('stockAnalysis', {
  state: () => ({
    // 推演相关
    currentAnalysis: null,     // 当前推演结果 StockAnalysisResult
    analysisSteps: [],         // SSE 流式步骤列表 StockAnalysisStep[]（辩论日志）
    isAnalyzing: false,        // 是否正在推演
    history: [],               // 历史推演记录列表
    error: null,
    // 内容生成相关（集成在推演页面底部）
    finalCopy: { title: '', body: '' },  // 最终文案（标题 + 正文）
    selectedPlatform: 'xhs',   // 当前选择的平台格式
    imageUrls: [],             // AI 生成的配图 URL 列表
    titleEmoji: '',            // 标题卡 emoji
    titleTheme: '',            // 标题卡主题色
    isEditing: false,          // 是否正在编辑文案
    editableContent: { title: '', body: '', selectedImageIndices: [], imageOrder: [] },
    // 多平台内容管理：每个平台独立的内容副本
    platformContents: {
      xhs: { title: '', body: '', images: [], tags: [], titleEmoji: '', titleTheme: '' },
      weibo: { title: '', body: '', images: [], tags: [] },
      xueqiu: { title: '', body: '', images: [], tags: [] },
      zhihu: { title: '', body: '', images: [], tags: [] },
    },
    // 发布相关
    isPublishing: false,       // 是否正在发布
    contentHistory: [],        // 历史生成/发布记录
  }),
  getters: {
    currentPlatformContent: (state) => state.platformContents[state.selectedPlatform] || {},
  },
  actions: {
    async startAnalysis(payload) { /* SSE 流式推演，payload 包含 topic 和 debate_rounds */ },
    stopAnalysis() { /* 停止推演 */ },
    async fetchHistory(limit, offset) { /* 获取历史记录 */ },
    async fetchDetail(analysisId) { /* 获取单条详情 */ },
    // 内容生成
    async generateContent(analysisId, platform) { /* 生成社交内容，结果存入 platformContents[platform] */ },
    async generateDailyReport(platform) { /* 生成每日速报 */ },
    async publishToXhs(contentId) { /* 发布到小红书 */ },
    // 多平台预览
    switchPlatform(platform) { /* 切换预览平台，加载对应平台的内容副本 */ },
    initPlatformContents(baseContent) { /* 从推演结果为每个平台生成初始内容副本 */ },
    // 编辑（仅影响当前平台）
    startEditing() { /* 进入编辑模式，加载当前平台的内容到 editableContent */ },
    updateContent(updates) { /* 更新当前平台的内容副本，不影响其他平台 */ },
  },
})
```

保留现有 `src/stores/config.js`（LLM 配置、主题等通用设置），在其中扩展合规脱敏设置和数据源 API Key 配置。不再需要独立的 `socialContent.js` store，内容生成状态合并到 `stockAnalysis.js` 中。

**`src/stores/dailyReport.js`** — 每日速报状态管理：

```javascript
export const useDailyReportStore = defineStore('dailyReport', {
  state: () => ({
    currentReport: null,       // 当日速报 SocialContent
    reportHistory: [],         // 历史速报列表
    isGenerating: false,       // 是否正在生成
    isPublishing: false,       // 是否正在发布
    platformStatuses: {},      // 各平台发布状态 {xhs: 'idle'|'publishing'|'published'|'failed'}
    selectedPlatform: 'xhs',   // 当前预览的平台格式
    // 多平台内容管理：每个平台独立的内容副本
    platformContents: {
      xhs: { title: '', body: '', images: [], tags: [], titleEmoji: '', titleTheme: '' },
      weibo: { title: '', body: '', images: [], tags: [] },
      xueqiu: { title: '', body: '', images: [], tags: [] },
      zhihu: { title: '', body: '', images: [], tags: [] },
    },
    isEditing: false,          // 是否正在编辑
    editableContent: { title: '', body: '', selectedImageIndices: [], imageOrder: [] },
    error: null,
  }),
  getters: {
    currentPlatformContent: (state) => state.platformContents[state.selectedPlatform] || {},
  },
  actions: {
    async generateReport() { /* 手动触发速报生成，生成后为每个平台初始化内容副本 */ },
    async fetchLatest() { /* 获取当日最新速报 */ },
    async fetchHistory(limit, offset) { /* 获取历史速报 */ },
    async publishAllPlatforms(contentId) { /* 一键发布全平台 */ },
    async publishToSinglePlatform(contentId, platform) { /* 单平台发布/重试 */ },
    switchPlatform(platform) { /* 切换预览平台，加载对应平台的内容副本 */ },
    startEditing() { /* 进入编辑模式，加载当前平台的内容到 editableContent */ },
    updateContent(updates) { /* 更新当前平台的内容副本，不影响其他平台 */ },
    initPlatformContents(baseContent) {
      /* 从速报基础内容为每个平台生成初始内容副本
         - xhs: 小红书风格（争议性标题 + emoji + 互动引导）
         - weibo: 微博风格（140 字精简 + 反问句）
         - xueqiu: 雪球风格（完整长文 + Markdown + 数据引用）
         - zhihu: 知乎风格（问题标题 + 回答体裁 + 逻辑推理）
      */
    },
  },
})
```

#### 8. SettingsView 合规脱敏与数据源管理 UI（`src/views/SettingsView.vue`）

在现有设置页面中新增三个配置区域：

**合规脱敏设置区域：**
- 全局默认脱敏级别选择器（四级单选：轻度脱敏/拼音缩写、中度脱敏/行业描述、重度脱敏/纯行业、不脱敏）
- 各平台脱敏级别覆盖：三个平台（小红书、微博、雪球、知乎）各一个下拉选择器，显示"使用默认"选项和推荐默认值标签
- 自定义脱敏规则管理：表格式界面，每行包含"敏感词"输入框和"替换词"输入框，支持添加/删除行
- 选择"不脱敏"时弹出风险警告对话框，需用户二次确认

**数据源 API Key 配置区域：**
- 分组展示：国际财经新闻（Finnhub、NewsAPI、Alpha Vantage、Marketaux）和投行研报（Benzinga、Seeking Alpha）
- 每个数据源一行：名称 + API Key 输入框（密码模式） + 启用/禁用开关 + 测试连通性按钮 + 状态指示灯（未配置/已配置/连通/失败）
- 无需 API Key 的数据源（GDELT、Google RSS、Yahoo Finance 等）显示"免费，无需配置"标签，仅提供启用/禁用开关

**每日速报定时配置区域：**
- 速报生成时间配置（小时:分钟选择器，默认 18:00）
- 增量检查开关（默认开启，每小时检查一次）
- 提示用户可在"每日速报"页面查看速报内容和发布操作

**情绪采集 Cookie 管理区域：**
- 数据源 Cookie 导入面板（雪球、同花顺等需要登录态 Cookie 的数据源）
- 每个数据源一行：名称 + Cookie 状态指示灯（未导入/有效/已失效）+ "导入 Cookie"按钮 + "清除"按钮
- "导入 Cookie"按钮点击后弹出文本框对话框，用户粘贴从浏览器开发者工具复制的 Cookie 字符串
- 支持批量导入多组 Cookie（每行一组），系统自动解析为 Cookie 池
- 导入后自动验证 Cookie 有效性（调用后端 `/api/sentiment/cookie/validate` 端点）
- 操作说明提示："请在浏览器中登录对应平台，打开开发者工具 → Network → 复制 Cookie 请求头内容粘贴到此处"

> **说明**：Cookie 获取为纯手动操作（用户从浏览器复制），不通过 Playwright 自动登录。这是因为雪球/同花顺的登录流程涉及短信验证码、滑块验证等，自动化成本高且易触发风控。

## 组件复用矩阵

以下矩阵展示各组件被哪些页面使用，以及 Props 差异：

| 组件 | StockHotView | StockAnalysisView | DailyReportView | SettingsView | Props 差异说明 |
|------|:---:|:---:|:---:|:---:|------|
| SentimentGauge | ✅ full 模式 | ✅ mini 模式 | ✅ mini 模式 | - | `size` prop 控制展示模式：full（完整仪表盘+分项得分）vs mini（仅指数值+标签） |
| SentimentChart | ✅ 详情面板 | - | ✅ 速报内容区 | - | StockHotView 传入个股 `stockCode`；DailyReportView 传入 `null`（大盘） |
| PlatformPreview | - | ✅ 底部文案区 | ✅ 右侧预览区 | - | Props 相同（`platformContents`、`selectedPlatform`、`isEditing`），数据来源不同：StockAnalysisView 来自 stockAnalysis store，DailyReportView 来自 dailyReport store |
| XiaohongshuPreview | - | ✅ 通过 PlatformPreview | ✅ 通过 PlatformPreview | - | Props 相同，由 PlatformPreview 统一传递 |
| WeiboCard | - | ✅ 通过 PlatformPreview | ✅ 通过 PlatformPreview | - | Props 相同 |
| XueqiuCard | - | ✅ 通过 PlatformPreview | ✅ 通过 PlatformPreview | - | Props 相同 |
| ZhihuCard | - | ✅ 通过 PlatformPreview | ✅ 通过 PlatformPreview | - | Props 相同 |
| CopywritingEditor | - | ✅ 编辑模式 | ✅ 编辑模式 | - | Props 相同（`editableContent`），编辑结果写入各自 store 的 `platformContents[selectedPlatform]` |
| NavigationBar | ✅ | ✅ | ✅ | ✅ | 无差异，通过 `router-link` 高亮当前路由 |
