# 设计文档：股票资讯与行情推演平台（索引）

> ⚠️ 本文件已拆分为多个子文件以减少上下文占用。请按需查阅对应模块：

## 文件索引

| 文件 | 内容 | 行数 |
|------|------|------|
| [design-overview.md](design-overview.md) | 概述、新增依赖、异步策略、架构图、数据库 Schema、定时任务 | ~730 |
| [design-frontend.md](design-frontend.md) | 前端组件（StockHotView、StockAnalysisView、DailyReportView、多平台预览组件）、路由、状态管理、SettingsView | ~450 |
| [design-backend-services.md](design-backend-services.md) | 后端 API 路由、爬虫服务、国际新闻服务、投行研报服务、推演服务、内容生成服务、合规脱敏服务 | ~690 |
| [design-sentiment.md](design-sentiment.md) | 散户情绪爬虫（代理池/Cookie池/自适应降速）、混合数据源服务、情绪分析服务、情绪 API、前端情绪组件 | ~500 |
| [design-data-models.md](design-data-models.md) | 全部数据模型定义、正确性属性（Property 1-46）、错误处理表、测试策略 | ~750 |

## 快速导航

- 想了解整体架构和技术选型 → [design-overview.md](design-overview.md)
- 想了解前端页面和组件设计 → [design-frontend.md](design-frontend.md)
- 想了解后端服务和 API 接口 → [design-backend-services.md](design-backend-services.md)
- 想了解情绪分析核心引擎 → [design-sentiment.md](design-sentiment.md)
- 想查看数据模型或测试属性 → [design-data-models.md](design-data-models.md)
