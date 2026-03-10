---
name: opinion-topic-analysis
description: 分析明确给定的话题、生成小红书文案、数据卡片和 AI 配图时使用。适用于“分析一下 XXX”“做舆情分析”“分析这个话题并生成发布内容”。先询问配置，再启动分析、轮询、生成卡片、预览，最后才允许发布。
metadata: { "clawdbot": { "emoji": "🔍", "os": ["darwin", "linux", "win32"] } }
---

# Opinion Topic Analysis

这是“具体话题分析”入口 skill。它是单文件自包含版本，不依赖 `references/`。

## MCP Binding

- 这个 skill 依赖本地 Opinion MCP 工具。
- 运行时绑定必须满足以下其一：
  - ClawdBot / mcporter: server name=`opinion-analyzer`, base URL=`http://localhost:18061`
  - 原生 MCP SSE: transport=`sse`, URL=`http://localhost:18061/sse`
- 必须优先使用这些工具，而不是转成手工分析：
  - `analyze_topic`
  - `get_analysis_status`
  - `generate_topic_cards`
  - `get_analysis_result`
  - `update_copywriting`
  - `publish_to_xhs`
- 只有当 MCP 工具调用明确失败时，才告诉用户当前 MCP 不可用。
- 不要在未调用 `analyze_topic` 前就说“没有可用的舆情分析工具接口”。
- 如果当前会话里根本看不到 `analyze_topic` / `get_analysis_status` 等工具，优先判断是 MCP 绑定缺失，而不是分析能力缺失。

## Intent Rules

- 只有“分析一个明确给定的话题”才用本 skill。
- 用户如果只是要看热榜，改走 `opinion-hot-news`。
- 用户如果只是要发布已有结果，改走 `xhs-publisher`。

## Critical Rules

- 在调用 `analyze_topic` 之前，必须先询问分析配置。
- 默认配置固定为 `platforms=["wb","dy","ks","bili"]`、`image_count=2`、`debate_rounds=2`。
- 调用 `analyze_topic` 成功后，必须每 60 秒调用一次 `get_analysis_status`。
- 轮询等待期间只允许等待；不要额外调用其他工具，不要猜测任务卡住。
- `status=completed` 之前不要调用 `get_analysis_result`。
- 完成后先 `generate_topic_cards(job_id=...)`，再 `get_analysis_result(job_id=...)`。
- 展示完整预览后，只有用户明确确认“OK”“发布”“确认”“可以”时，才能调用 `publish_to_xhs`。
- 发布失败时不要重新调用 `analyze_topic`。

## State Bus

| State | Entry Condition | Allowed Action | Exit Criteria | Next State |
|---|---|---|---|---|
| `collect_config` | 用户要分析新话题 | 询问并解析配置 | 已得到 `platforms/image_count/debate_rounds` | `start_analysis` |
| `start_analysis` | 配置已齐 | 调 `analyze_topic` | 已拿到 `job_id` | `poll_analysis` |
| `poll_analysis` | 任务运行中 | 每 60 秒调 `get_analysis_status` | `status=completed` 或 `failed` | `prepare_preview` / `failed` |
| `prepare_preview` | 分析已完成 | 调 `generate_topic_cards` + `get_analysis_result` | 预览数据完整 | `preview` |
| `preview` | 结果已可预览 | 展示完整预览 | 用户确认发布或要求修改 | `edit_existing` / `publish_existing` / `done` |
| `edit_existing` | 用户要求修改文案 | 调 `update_copywriting` + 重新预览 | 修改已反映到预览 | `preview` |
| `publish_existing` | 用户明确要发布 | 调 `publish_to_xhs` | 成功、超时、失败、already_published | `done` / `retry_publish` / `failed` |
| `retry_publish` | 发布失败但不需重分析 | 补卡片或重试发布 | 发布成功或用户停止 | `done` / `failed` |

## Atomic Step: Analysis Config

### Entry Criteria

- 用户已给出明确话题
- 当前意图为分析新话题

### Action

1. 收集 3 个参数：
   - `platforms`
   - `image_count`
   - `debate_rounds`
2. 默认值：
   - `platforms=["wb","dy","ks","bili"]`
   - `image_count=2`
   - `debate_rounds=2`
3. 支持解析：
   - “默认”
   - “全部”
   - “1,2,6 + 3张图 + 3轮”
4. 平台数字映射：
   - `1=wb`
   - `2=dy`
   - `3=ks`
   - `4=bili`
   - `5=tieba`
   - `6=zhihu`
   - `7=xhs`
   - `8=hn`
   - `9=reddit`
5. 向用户复述配置
6. 用户明确说“开始分析”后，进入下一步

### Exit Criteria

- 3 个参数都已确定
- 用户已确认开始分析

### Forbidden

- 不要在配置未确定前调用 `analyze_topic`
- 不要把 `image_count=0` 解释为“不能发布”
- 不要在用户确认开始后退回手工分析

## Atomic Step: Analysis Run And Poll

### Entry Criteria

- 配置已确认
- 已有 `topic/platforms/image_count/debate_rounds`

### Action

1. 调用 `analyze_topic(...)`
2. 成功后记录 `job_id`
3. 每 60 秒调用一次 `get_analysis_status(job_id=...)`
4. 每次轮询只读取：
   - `progress`
   - `current_step_name`
   - `current_platform`
5. 每次轮询只发送一条简短进度消息
6. 当 `status=completed` 时退出轮询
7. 当 `status=failed` 时报告失败节点并停止

### Exit Criteria

- 得到 `status=completed`
- 或明确得到 `status=failed`

### Forbidden

- 不要在等待期查询健康状态
- 不要在等待期调用 `get_analysis_result`
- 不要在等待期触发新分析
- 不要主观猜测“卡住了”
- 在 `analyze_topic` 明确失败前，不要说“没有可用的分析接口”

## Atomic Step: Preview And Edit

### Entry Criteria

- 分析任务已完成
- 已有 `job_id`

### Action

1. 先调用 `generate_topic_cards(job_id=...)`
2. 再调用 `get_analysis_result(job_id=...)`
3. 预览必须包含：
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
- 用户要么确认发布，要么明确结束，要么提出修改

### Forbidden

- 不要跳过 `generate_topic_cards`
- 不要只展示标题就进入发布
- 不要在未调 `get_analysis_result` 前声称“没有结果可预览”

## Atomic Step: Publish Flow

### Entry Criteria

- 用户已经明确确认要发布
- 已有完成任务或 `job_id`

### Action

1. 确认目标任务已完成
2. 发布前检查：
   - `ai_images` 是否可用
   - 如不可用，调用 `generate_topic_cards(job_id=...)`
   - 只把 `cards` / `cards_meta` 当作资源就绪信息
3. 调用 `publish_to_xhs(job_id=...)`

### Exit Criteria

- 发布成功
- 或明确失败并给出当前节点允许的恢复动作

### Forbidden

- 不要因为发布失败重跑 `analyze_topic`
- 不要自己打开或解析本地卡片路径
- 不要在 `publish_to_xhs` 明确返回失败前自己判定“无法发布”

## Response Discipline

- 配置询问要结构化，参数名明确。
- 用户确认开始后，下一步就是调 `analyze_topic`。
- 轮询期间每个周期只发一条简短进度消息。
- 预览必须包含标题、副标题、正文、标签、配图数量、卡片就绪情况。
- 报错时说明当前失败节点和下一步有效动作，不要泛化成“重新来一遍”。
