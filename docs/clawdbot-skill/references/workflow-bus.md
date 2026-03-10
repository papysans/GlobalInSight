# Workflow Bus

这是 `opinion-analyzer` 的状态总线。修改工作流时，先改这里，再改对应原子步骤。

## States

| State | Entry Condition | Allowed Action | Exit Criteria | Next State |
|---|---|---|---|---|
| `classify_intent` | 收到用户请求 | 识别意图 | 确定为 4 类之一 | `hot_news` / `collect_config` / `edit_existing` / `publish_existing` |
| `hot_news` | 用户要看热榜 | 调 `get_hot_news` | 已返回热榜并总结 | `done` |
| `collect_config` | 用户要分析新话题 | 询问并解析配置 | 已得到 `platforms/image_count/debate_rounds` | `start_analysis` |
| `start_analysis` | 配置已齐 | 调 `analyze_topic` | 已拿到 `job_id` | `poll_analysis` |
| `poll_analysis` | 任务运行中 | 每 60 秒调 `get_analysis_status` | `status=completed` 或 `failed` | `prepare_preview` / `failed` |
| `prepare_preview` | 分析已完成 | 调 `generate_topic_cards` + `get_analysis_result` | 预览数据完整 | `preview` |
| `preview` | 结果已可预览 | 展示完整预览 | 用户确认发布或要求修改 | `edit_existing` / `publish_existing` / `done` |
| `edit_existing` | 用户要求修改文案 | 调 `update_copywriting` + 重新预览 | 修改已反映到预览 | `preview` |
| `publish_existing` | 用户明确要发布 | 调 `publish_to_xhs` | 成功、超时、失败、already_published | `done` / `retry_publish` / `failed` |
| `retry_publish` | 发布失败但不需重分析 | 补卡片或重试发布 | 发布成功或用户停止 | `done` / `failed` |

## Invariants

- 任一时刻只能处于一个状态。
- 不允许从 `classify_intent` 直接跳到 `publish_existing`，除非当前上下文已有完成任务。
- 不允许从 `poll_analysis` 直接跳到 `publish_existing`；必须先 `prepare_preview` 和 `preview`。
- `publish_existing` 失败时，不允许回到 `start_analysis`。
- `hot_news` 是独立支路，不进入分析状态机。

## Required Context

在状态之间至少保留这些上下文字段：

- `intent`
- `topic`
- `job_id`
- `platforms`
- `image_count`
- `debate_rounds`
- `analysis_status`
- `cards_ready`
- `preview_ready`
- `publish_confirmed`
- `published`

## Failure Policy

- 当前状态失败时，先报告失败节点，再给出该节点允许的恢复动作。
- 恢复动作必须局限于当前分支；不能跨分支重置整个任务。
- 只有用户明确要求重新分析时，才允许重新进入 `collect_config`。
