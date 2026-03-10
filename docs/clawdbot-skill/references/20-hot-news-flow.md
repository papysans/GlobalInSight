# Atomic Step: Hot News

## Purpose

为“今日热点 / 热榜 / 榜单”类请求返回热榜，不启动分析任务。

## Entry Criteria

- 当前意图为 `hot_news`

## Action

1. 默认参数：
   - `limit=20`
   - `include_hn=true`
   - `platforms` 留空
2. 用户明确指定平台时，再传 `platforms`。
3. 直接调用 `get_hot_news`。
4. 输出时按平台和整体热度做简短归纳。
5. 可选地问一句“要不要挑一个话题继续分析”。

## Exit Criteria

- 热榜数据已返回
- 用户已得到简洁总结

## Forbidden

- 不要询问 `image_count`
- 不要询问 `debate_rounds`
- 不要启动 `analyze_topic`
- 不要说“任务已启动”
