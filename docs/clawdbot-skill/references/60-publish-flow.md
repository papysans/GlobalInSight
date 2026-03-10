# Atomic Step: Publish Flow

## Purpose

把已有完成任务发布到小红书，不重新分析。

## Entry Criteria

- 当前意图为 `publish_existing`
- 已有完成任务或已知 `job_id`

## Action

1. 确认目标任务已完成
2. 如果当前对话还没有完成预览，先补预览
3. 如果用户尚未明确确认，先等待确认
4. 发布前检查：
   - `ai_images` 是否可用
   - 如不可用，调用 `generate_topic_cards(job_id=...)`
   - 只把 `cards` / `cards_meta` 当作资源就绪信息
5. 调用 `publish_to_xhs(job_id=...)`

## Success Handling

- 发布成功 -> 返回链接或成功结果，结束

## Failure Handling

- `already_published=true` -> 告知已发布过，立即停止
- 超时或普通失败 -> 建议直接重试发布
- 素材不足 -> 先补卡片，再重试发布

## Exit Criteria

- 发布成功
- 或明确失败并给出当前节点允许的恢复动作

## Forbidden

- 不要因为发布失败重跑 `analyze_topic`
- 不要自己打开或解析本地卡片路径
- 不要跳过用户确认
