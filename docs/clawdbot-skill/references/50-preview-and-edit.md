# Atomic Step: Preview And Edit

## Purpose

在分析完成后准备完整预览，并在需要时支持文案修改。

## Entry Criteria

- 分析任务已完成
- 已有 `job_id`

## Action

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

## Exit Criteria

- 用户看到完整预览
- 用户要么确认发布，要么明确结束，要么提出修改

## Forbidden

- 不要跳过 `generate_topic_cards`
- 不要只展示标题就进入发布
- 不要未预览就调用 `publish_to_xhs`
