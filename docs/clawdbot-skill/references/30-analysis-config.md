# Atomic Step: Analysis Config

## Purpose

在启动分析前收集最小必要配置，并保持默认值可预测。

## Entry Criteria

- 当前意图为 `analyze_topic`
- 用户已给出明确话题

## Required Questions

必须收集这 3 项：

- `platforms`
- `image_count`
- `debate_rounds`

## Defaults

- `platforms=["wb","dy","ks","bili"]`
- `image_count=2`
- `debate_rounds=2`

## Supported Shortcuts

- “默认” -> 默认值
- “全部” -> `["wb","dy","ks","bili","tieba","zhihu","xhs","hn","reddit"]`
- “1,2,6 + 3张图 + 3轮” -> 数字平台映射 + 指定图片数 + 指定轮数

平台数字映射：

- `1=wb`
- `2=dy`
- `3=ks`
- `4=bili`
- `5=tieba`
- `6=zhihu`
- `7=xhs`
- `8=hn`
- `9=reddit`

## Exit Criteria

- 3 个参数都已确定
- 已向用户复述配置

## Forbidden

- 不要在配置未确定前调用 `analyze_topic`
- 不要把 `image_count=0` 解释为“不能发布”
- 不要对“热榜”请求进入本步骤
