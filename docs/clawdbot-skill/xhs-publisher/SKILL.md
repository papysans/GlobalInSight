---
name: xhs-publisher
description: 发布已有分析结果到小红书，或在发布前微调标题、正文、标签时使用。适用于“把刚才那个发到小红书”“发布最近完成的任务”“改下标题再发”。先预览和确认，再补卡片或重试发布，不要重新启动 analyze_topic。
metadata: { "clawdbot": { "emoji": "📕", "os": ["darwin", "linux", "win32"] } }
---

# XHS Publisher

这是发布入口 skill。它是单文件自包含版本，不依赖 `references/`。

## MCP Binding

- 这个 skill 依赖本地 Opinion MCP 工具。
- 运行时绑定必须满足以下其一：
  - ClawdBot / mcporter: server name=`opinion-analyzer`, base URL=`http://localhost:18061`
  - 原生 MCP SSE: transport=`sse`, URL=`http://localhost:18061/sse`
- 必须优先使用这些工具：
  - `get_analysis_result`
  - `generate_topic_cards`
  - `update_copywriting`
  - `publish_to_xhs`
- 只有当 MCP 工具调用明确失败时，才告诉用户当前 MCP 不可用。
- 不要在未调用 `publish_to_xhs` 前就说“无法发布”。
- 如果当前会话里根本看不到 `publish_to_xhs` / `get_analysis_result`，优先判断是 MCP 绑定缺失，而不是发布能力缺失。

## Intent Rules

- 用户只想看今日热榜，改走 `opinion-hot-news`。
- 用户要重新做某个具体话题的分析，改走 `opinion-topic-analysis`。
- 用户要基于现有结果发布、重试发布、改文案后再发，继续执行本 skill。

## Critical Rules

- 这是发布 skill，不是分析 skill。
- 不要在这里调用 `analyze_topic`。
- 发布对象必须是已完成任务；未完成任务不能发布。
- 发布前如果用户还没确认，必须先给预览。
- 发布失败时只能重试发布、补齐卡片或修改文案；不要重做分析。
- 如果返回 `already_published=true`，立即停止，不要再次发布。
- `image_count=0` 时仍可以依赖本地渲染卡片发布。

## State Bus

| State | Entry Condition | Allowed Action | Exit Criteria | Next State |
|---|---|---|---|---|
| `resolve_target` | 用户要发布已有结果 | 确定 `job_id` 或最近完成任务 | 已拿到可发布目标 | `prepare_preview` |
| `prepare_preview` | 已有完成任务 | 调 `generate_topic_cards` + `get_analysis_result` | 预览数据完整 | `preview` |
| `preview` | 结果已可预览 | 展示预览并等待确认 | 用户确认发布或要求修改 | `edit_existing` / `publish_existing` / `done` |
| `edit_existing` | 用户要求修改文案 | 调 `update_copywriting` + 重新预览 | 修改已反映到预览 | `preview` |
| `publish_existing` | 用户明确要发布 | 调 `publish_to_xhs` | 成功、超时、失败、already_published | `done` / `retry_publish` / `failed` |
| `retry_publish` | 发布失败但不需重分析 | 补卡片或重试发布 | 发布成功或用户停止 | `done` / `failed` |

## Atomic Step: Resolve Target

### Entry Criteria

- 用户要发布已有结果

### Action

1. 优先使用用户提供的 `job_id`
2. 否则使用当前上下文中最近一次已完成的分析任务
3. 如果任务尚未完成，明确告知不能发布未完成任务

### Exit Criteria

- 已拿到明确可发布的任务目标

### Forbidden

- 不要在这里调用 `analyze_topic`

## Atomic Step: Preview And Edit

### Entry Criteria

- 已有完成任务

### Action

1. 先调用 `generate_topic_cards(job_id=...)`
2. 再调用 `get_analysis_result(job_id=...)`
3. 展示完整预览：
   - `title`
   - `subtitle`
   - `content`
   - `tags`
   - `ai_images` 数量
   - `cards` / `cards_meta` 就绪情况
4. 用户要求修改时：
   - 调 `update_copywriting`
   - 重新调用 `get_analysis_result`
   - 再次展示预览

### Exit Criteria

- 用户看到完整预览
- 用户要么确认发布，要么提出修改

### Forbidden

- 不要跳过预览直接发布
- 不要在未调工具前说“当前没有可发布内容”

## Atomic Step: Publish Flow

### Entry Criteria

- 用户已经明确确认要发布
- 已有可发布任务

### Action

1. 发布前检查：
   - `ai_images` 是否可用
   - 如不可用，调用 `generate_topic_cards(job_id=...)`
   - 只把 `cards` / `cards_meta` 当作资源就绪信息
2. 调用 `publish_to_xhs(job_id=...)`
3. 如果失败：
   - `already_published=true` -> 告知已发布过，立即停止
   - 普通失败或超时 -> 建议直接重试发布
   - 素材不足 -> 先补卡片，再重试发布

### Exit Criteria

- 发布成功
- 或明确失败并给出当前节点允许的恢复动作

### Forbidden

- 不要因为发布失败重跑 `analyze_topic`
- 不要自己打开或解析本地卡片路径
- 不要在 `publish_to_xhs` 明确返回失败前自己判定“无法发布”

## Response Discipline

- 先说明当前要发布的是哪个任务。
- 失败时指出是“目标解析失败 / 预览失败 / 发布失败”中的哪一类。
- 恢复建议只给当前节点允许的动作，不要建议重跑整条分析链。
