---
name: opinion-hot-news
description: 查看今日热点、热榜、榜单、多平台热门话题时使用。适用于“今日热点”“看看热榜”“今天有什么值得关注的话题”这类请求。直接调用 get_hot_news，不要询问 analyze_topic 的平台、配图或辩论参数。
metadata: { "clawdbot": { "emoji": "📰", "os": ["darwin", "linux", "win32"] } }
---

# Opinion Hot News

这是热榜入口 skill。它是单文件自包含版本，不依赖 `references/`。

## MCP Binding

- 这个 skill 依赖本地 Opinion MCP 工具。
- 运行时绑定必须满足以下其一：
  - ClawdBot / mcporter: server name=`opinion-analyzer`, base URL=`http://localhost:18061`
  - 原生 MCP SSE: transport=`sse`, URL=`http://localhost:18061/sse`
- 进入本 skill 后，优先直接调用 `get_hot_news`。
- 不要用“我没有数据源”“我没有接口”这类话术跳过工具调用。
- 只有当 `get_hot_news` 明确返回连接失败、超时或不可用时，才告诉用户当前 MCP 不可用。
- 如果 MCP 不可用，明确说“Opinion MCP 未连接或工具调用失败”，不要泛化成“没有热榜来源”。
- 如果当前会话里根本看不到 `get_hot_news`，优先判断是 MCP 绑定缺失，而不是热榜能力缺失。

## Intent Rules

- 用户要看今日热点、热榜、榜单、平台热门话题时，使用本 skill。
- 用户已经点名某个具体话题要做分析时，不用本 skill。
- 用户要发布已有结果时，不用本 skill。

## State Bus

| State | Entry Condition | Allowed Action | Exit Criteria | Next State |
|---|---|---|---|---|
| `hot_news` | 用户要看热榜 | 调 `get_hot_news` | 已返回热榜并总结 | `done` |

## Atomic Step: Hot News

### Entry Criteria

- 当前意图为“今日热点 / 热榜 / 榜单”

### Action

1. 默认参数：
   - `limit=20`
   - `include_hn=true`
   - `platforms` 留空
2. 用户明确指定平台时，再传 `platforms`
3. 直接调用 `get_hot_news`
4. 输出时按平台和整体热度做简短归纳
5. 可选地问一句“要不要挑一个话题继续分析”

### Exit Criteria

- 热榜数据已返回
- 用户已得到简洁总结

### Forbidden

- 不要询问 `image_count`
- 不要询问 `debate_rounds`
- 不要启动 `analyze_topic`
- 不要说“分析任务已启动”
- 不要在未调用 `get_hot_news` 前就说“取不到热点”

## Response Discipline

- 输出以“热榜摘要 + 可继续分析的话题建议”为主。
- 不要把热榜请求包装成分析或发布流程。
