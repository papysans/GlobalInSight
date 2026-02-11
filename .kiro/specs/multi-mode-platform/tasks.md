# 实现计划：股票资讯与行情推演平台（索引）

> ⚠️ 本文件已拆分为多个子文件以减少上下文占用。请按需查阅对应阶段：

## 文件索引

| 文件 | 内容 | 任务范围 | 行数 |
|------|------|---------|------|
| [tasks-phase1.md](tasks-phase1.md) | 后端基础：数据模型、爬虫服务、国际新闻、投行研报、API 端点、推演服务 | 任务 1-7 | ~200 |
| [tasks-phase2.md](tasks-phase2.md) | 社交内容生成、合规脱敏、定时任务、前端视图和组件、清理旧代码 | 任务 8-19 | ~280 |
| [tasks-phase3.md](tasks-phase3.md) | 散户情绪分析全链路：爬虫基础设施、混合数据源、情绪分析、API、前端可视化 | 任务 20-29 | ~230 |

## 执行顺序

1. **阶段一**（[tasks-phase1.md](tasks-phase1.md)）：搭建后端核心 — 数据采集 + 推演引擎
2. **阶段二**（[tasks-phase2.md](tasks-phase2.md)）：内容生成 + 前端改造 + 旧代码清理
3. **阶段三**（[tasks-phase3.md](tasks-phase3.md)）：情绪分析核心引擎（建议尽早启动，为推演和内容生成提供数据支撑）

## 跨阶段依赖说明

> **情绪模块可选依赖（Graceful Degradation）**：情绪分析是系统核心引擎（Phase 3，任务 20-29），但 Phase 1 的推演服务（任务 5.1 Step 0）和 Phase 2 的内容生成（任务 8.2）均引用情绪数据。由于 Phase 1/2 开发时情绪模块尚未实现，所有情绪相关调用必须设计为可选依赖：
> - `SentimentAnalyzer.get_sentiment_context()` 不可用时返回 `None`，推演服务以"无情绪数据降级模式"运行（跳过 Step 0 情绪数据获取，后续 Agent prompt 中不注入情绪数据）
> - `SocialContentGenerator` 的各 `generate_*` 方法在 `sentiment_context` 为 `None` 时跳过情绪数据融入，生成不含情绪洞察的内容
> - Phase 1/2 开发时无需编写 mock/stub，只需在调用点做 `if sentiment_context is not None` 判断
> - Phase 3 完成后，情绪数据自动注入，无需修改 Phase 1/2 代码
