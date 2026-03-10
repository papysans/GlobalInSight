---
name: opinion-analyzer
description: 兼容旧入口的总控技能。用于查看今日热点、分析明确给定的话题、修改已生成文案，或将已完成分析结果发布到小红书。先把请求归类为 hot_news、analyze_topic、edit_existing、publish_existing 之一，再按原子步骤执行。不要把热榜请求带入分析配置，也不要因为发布失败而重新分析。
homepage: https://github.com/user/GlobalInSight
metadata: { "clawdbot": { "emoji": "🧭", "os": ["darwin", "linux", "win32"] } }
---

# Opinion Analyzer Router

这是兼容旧命令 `/opinion-analyzer` 的强约束总控 skill。它不直接“自由发挥”，而是先判定意图，再沿着固定状态总线执行原子步骤。

## Read Order

1. 先读 `references/workflow-bus.md`，确定状态机。
2. 先做意图分类，再读取下一份需要的原子步骤文档。
3. 一次只执行当前状态允许的动作；不要跨步骤跳转。
4. 当前步骤达到 exit criteria 之前，不要进入下一步。

## Intent Classification

先把用户请求归入以下 4 类之一：

- `hot_news`
  - 例子：“今日热点”“看看热榜”“今天有什么值得关注的话题”
- `analyze_topic`
  - 例子：“分析一下 GPT-5.4 发布”“做这个话题的舆情分析”
- `edit_existing`
  - 例子：“把刚才标题改一下”“正文改短一点”
- `publish_existing`
  - 例子：“发到小红书”“把最近完成的任务发布”

如果无法分类，先追问用户是“看热榜 / 分析新话题 / 修改已有文案 / 发布已有结果”中的哪一种。

## Global Rules

- 不要在意图分类之前调用任何高成本工具。
- `hot_news` 直接走 `get_hot_news`；不要先问分析配置。
- `analyze_topic` 必须先询问 `platforms`、`image_count`、`debate_rounds`。
- `publish_existing` 和 `edit_existing` 不要重新调用 `analyze_topic`。
- `status=completed` 之前不要调用 `get_analysis_result`。
- 发布前必须先完成预览，并获得用户明确确认。
- 发布失败时，只允许重试发布、补卡片或修改文案；不要重做分析。

## Atomic Execution Map

- `hot_news`
  - 读 `references/20-hot-news-flow.md`
- `analyze_topic`
  - 依次读：
    - `references/30-analysis-config.md`
    - `references/40-analysis-run-and-poll.md`
    - `references/50-preview-and-edit.md`
    - `references/60-publish-flow.md`
- `edit_existing`
  - 读 `references/50-preview-and-edit.md`
- `publish_existing`
  - 读 `references/60-publish-flow.md`

## Response Discipline

- 配置询问要结构化，参数名明确。
- 轮询期间每个周期只发一条简短进度消息。
- 预览必须包含标题、副标题、正文、标签、配图数量、卡片就绪情况。
- 报错时说明当前失败节点和下一步有效动作，不要泛化成“重新来一遍”。
