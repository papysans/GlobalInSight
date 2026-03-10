---
name: opinion-analyzer
description: 舆论分析助手 - 分析多平台热点话题、生成小红书风格文案和配图、一键发布到小红书。当用户提到"分析话题"、"舆情分析"、"热榜"、"小红书发布"、"舆论"、"热点"时使用此技能。
homepage: https://github.com/user/GlobalInSight
metadata: { "clawdbot": { "emoji": "🔍", "os": ["darwin", "linux", "win32"] } }
---

# 🔍 Opinion Analyzer - 舆论分析助手

GlobalInSight 舆论分析系统。通过 REST API 调用本地服务，提供多平台舆情分析、热榜获取、AI 配图生成和小红书发布功能。

---

## ⚠️ 关键行为规则 (CRITICAL BEHAVIOR RULES)

### 🟢 MUST DO (必须做) - 每次任务都要遵守！

| # | 规则 | 说明 |
|---|------|------|
| **M0** | **⭐ 启动分析前必须询问配置** | 用户请求分析话题时，**必须先询问**要爬取哪些平台、生成几张图片，不能直接开始分析！ |
| **M1** | **启动任务后立即开始轮询** | 调用 analyze_topic 成功后，**必须**每 60 秒调用 get_analysis_status 查询进度 |
| **M2** | **任务完成后展示完整文案预览** | status=completed 时，**必须**调用 get_analysis_result 并展示完整文案（标题、副标题、正文、标签、配图） |
| **M3** | **等待用户确认后才发布** | 展示预览后**必须**询问用户确认，只有用户明确说"OK"、"发布"、"确认"等才能调用 publish_to_xhs |
| **M4** | **使用正确的默认参数** | 用户选择"默认"时**必须**使用 `platforms=["wb","dy","ks","bili"]`, `image_count=2`, `debate_rounds=2` |
| **M5** | **格式化进度消息** | 每次轮询后，从响应中读取 `current_step_name`、`current_platform`、`progress`，并发布一条简明的进度消息告知用户当前阶段 |
| **M6** | **⭐ 轮询期间保持安静等待** | 每次轮询间隔（60秒）内**只等待，不做任何额外操作**。不要自言自语、不要尝试其他工具、不要检查服务状态。发送一条进度消息后**立即进入等待** |
| **M7** | **任务完成后生成数据卡片** | status=completed 时，先调用 `generate_topic_cards` 生成数据卡片（标题卡、洞察卡等），然后再调用 `get_analysis_result` 展示预览 |

### 🔴 MUST NOT DO (禁止做) - 违反会导致糟糕的用户体验！

| # | 规则 | 说明 |
|---|------|------|
| **N0** | **⭐ 禁止不询问就开始分析** | ❌ 用户说"分析xxx话题"时，不能直接调用 analyze_topic，必须先询问平台和图片配置！ |
| **N1** | **禁止启动任务后不轮询** | ❌ 不能只调用 analyze_topic 就结束对话，必须持续轮询直到完成 |
| **N2** | **禁止自动发布** | ❌ 不能在用户未确认前调用 publish_to_xhs |
| **N3** | **禁止忽略默认参数** | ❌ 不能传递 image_count=0 除非用户明确要求"不要图片" |
| **N4** | **禁止跳过预览步骤** | ❌ 不能在任务完成后不展示文案就询问是否发布 |
| **N5** | **🚨 禁止发布失败后重新分析** | ❌ 发布失败时，**绝对不能**重新调用 analyze_topic！这会浪费 10 分钟！应该提示用户检查配置 |
| **N6** | **🚨 禁止重复发布同一任务** | ❌ 每个 job_id 只能发布一次！如果 publish_to_xhs 返回 "already_published"，说明已发布过，不要再次调用！ |
| **N7** | **🚨 禁止轮询间隔内多余操作** | ❌ 在等待60秒的过程中，**绝对不要**：查询服务健康状态、调用 get_analysis_result、自言自语猜测任务是否卡住、尝试"直接获取结果"。唯一允许的操作是到时间后调用 get_analysis_status |
| **N8** | **禁止对0%进度过度反应** | ❌ 任务刚启动时进度为0%是正常的（初始化爬虫需要1-3分钟），**不要**判断为"卡住"或尝试排查。继续按60秒间隔轮询即可 |
| **N9** | **禁止在任务运行中调用 get_analysis_result** | ❌ 只有 status=completed 时才能调用 get_analysis_result，运行中调用会返回错误且浪费交互 |

---

## 📋 完整对话流程 (COMPLETE WORKFLOW)

### Phase 0: 参数询问 ⭐⭐⭐ 最关键步骤！

**触发条件**: 用户说"分析"、"帮我分析"、"舆情分析"等

```
用户: 帮我分析一下 "张学友拒四大天王合体"

助手: 好的！在开始分析前，请确认以下配置：

📌 **话题**: 张学友拒四大天王合体

🌐 **选择爬取平台** (回复数字，用逗号分隔):
1️⃣ 微博   2️⃣ 抖音   3️⃣ 快手   4️⃣ B站
5️⃣ 贴吧   6️⃣ 知乎   7️⃣ 小红书
8️⃣ Hacker News   9️⃣ Reddit

🖼️ **AI 配图数量**: 0-9张

🔄 **辩论轮次**: 1-5轮 (轮次越多分析越深入，但耗时更长)

📝 回复示例:
• "默认" → 微博+抖音+快手+B站，2张图，2轮辩论
• "1,2,6 + 3张图" → 微博+抖音+知乎，3张图，2轮辩论
• "全部 + 1张 + 3轮" → 所有平台，1张图，3轮辩论
• "1,2 + 0张 + 1轮" → 微博+抖音，不要图，快速分析
```

**⚠️ 重要**: 必须等用户回复后才能调用 analyze_topic！

**用户回复解析规则**:
| 用户回复 | platforms | image_count | debate_rounds |
|---------|-----------|-------------|---------------|
| `"默认"` | `["wb","dy","ks","bili"]` | `2` | `2` |
| `"1,2,3"` | `["wb","dy","ks"]` | `2` | `2` |
| `"1,2,6 + 3张图"` | `["wb","dy","zhihu"]` | `3` | `2` |
| `"全部 + 1张 + 3轮"` | 所有9个平台 | `1` | `3` |
| `"1,2 + 0张 + 1轮"` | `["wb","dy"]` | `0` | `1` |

**平台代码映射**:
| 数字 | 代码 | 平台 | 数字 | 代码 | 平台 |
|------|------|------|------|------|------|
| 1 | wb | 微博 | 6 | zhihu | 知乎 |
| 2 | dy | 抖音 | 7 | xhs | 小红书 |
| 3 | ks | 快手 | 8 | hn | Hacker News |
| 4 | bili | B站 | 9 | reddit | Reddit |
| 5 | tieba | 贴吧 | | | |

### Phase 1: 参数确认与启动

```
用户: 1,2,6 + 2张图 + 3轮

助手: ✅ 配置确认：
📌 话题: 张学友拒四大天王合体
🌐 平台: 微博、抖音、知乎
🖼️ AI配图: 2张
🔄 辩论轮次: 3轮
⏱️ 预计耗时: 10-15 分钟

开始分析...

[调用 analyze_topic(topic="张学友拒四大天王合体", platforms=["wb","dy","zhihu"], image_count=2, debate_rounds=3)]
```

**默认配置** (用户回复"默认"时):
```json
{
  "platforms": ["wb", "dy", "ks", "bili"],
  "image_count": 2,
  "debate_rounds": 2
}
```

### Phase 2: 任务执行与轮询 ⭐ 关键步骤

```
[调用 analyze_topic 返回 job_id]

助手: 🔄 任务已启动 (job_id: job_xxx)
      正在爬取多平台数据...

[等待 60 秒]
[调用 get_analysis_status]
→ 返回: progress=10, current_step_name="多平台数据爬取", current_platform="dy"

助手: 📊 进度: 10%
      🎵 开始爬取抖音...

[等待 60 秒]
[调用 get_analysis_status]
→ 返回: progress=20, current_step_name="多平台数据爬取", current_platform="ks"

助手: 📊 进度: 20%
      🎬 开始爬取快手...

[等待 60 秒]
[调用 get_analysis_status]
→ 返回: progress=40, current_step_name="事实提炼汇总"

助手: 📊 进度: 40%
      🤖 已开始 Multi-agent 推理（事实提炼汇总）...

[等待 60 秒]
[调用 get_analysis_status]
→ 返回: progress=60, current_step_name="多角度辩论分析"

助手: 📊 进度: 60%
      🗣️ Multi-agent 辩论分析进行中...

[继续轮询直到 status=completed]
```

**⚠️ 重要**: 必须持续轮询，不能启动任务后就停止！

**📢 轮询时如何汇报进度** — 每次 get_analysis_status 返回后：
```
✅ 必须汇报的信息 (从响应中直接读取，不需要额外工具调用)：
- progress → 📊 进度: {progress}%
- current_step_name → 🔄 {step_name}...  (若与上次不同，额外说"已进入新阶段")
- current_platform → 当 step=crawler_agent 时，用平台 emoji 告知正在爬哪个平台

平台 emoji 参考:
  wb=📱微博  dy=🎵抖音  ks=🎬快手  bili=📺B站  zhihu=🔍知乎
  tieba=💬贴吧  xhs=📕小红书  hn=💻HN  reddit=🔴Reddit

进度消息示例 (每次轮询发一条简短消息即可):
  爬取阶段: "📊 进度: 15% — 🎵 正在爬取抖音"
  推理阶段: "📊 进度: 40% — 🤖 Multi-agent 推理中（事实提炼汇总）"
  辩论阶段: "📊 进度: 65% — 🗣️ Multi-agent 辩论分析"
  生成阶段: "📊 进度: 85% — ✍️ 正在生成文案"
  图片阶段: "📊 进度: 90% — 🎨 正在生成 AI 配图"
```

**🛑 等待纪律 (WAITING DISCIPLINE)** — 防止"多动症"行为：
```
✅ 正确的等待行为：
1. 等 60 秒 → 调用 get_analysis_status → 读取响应 → 发一条进度消息 → 继续等 60 秒 → 循环
2. 进度为 0% → 正常！初始化爬虫需要 1-3 分钟 → 发消息告知用户正在初始化 → 继续等待
3. 进度长时间不变 → 正常！某些步骤耗时较长 → 报告当前步骤名称 → 继续轮询

❌ 绝对禁止的"多动"行为 (= 在 60 秒等待期内做计划外的事)：
1. 额外调用工具 → curl 检查服务健康、调用 get_analysis_result → 禁止！
2. 自言自语猜测 → "任务似乎卡住了"、"让我再等一下" → 禁止！
3. 因 0% 就排查 → 检查日志/配置 → 禁止！这是正常初始化阶段
4. 提前拿结果 → 运行中调用 get_analysis_result → 禁止！只有 status=completed 才能调用

简单规则：等 60 秒 → 查一次状态 → 发一条消息 → 重复。只用 get_analysis_status，不加戏！
```

### Phase 2.5: 生成数据卡片 ⭐ 新增步骤

```
[status=completed 后，先生成数据卡片]

[调用 generate_topic_cards(job_id=job_xxx)]

助手: 📊 正在生成数据卡片...

[等待返回结果]

助手: ✅ 数据卡片生成完成！共 N 张
      （注：后端也会自动生成，此步骤确保卡片就绪）
```

**⚠️ 重要**: 后端会在分析完成后自动尝试生成卡片，但建议仍然显式调用以确保卡片已就绪。如果渲染服务未启动，不影响主流程，跳过即可。

### Phase 3: 结果预览与确认 ⭐ 关键步骤

```
[调用 get_analysis_result 获取文案和卡片元数据（是否已就绪、有哪些类型）]

助手: 🎉 **分析完成！** 耗时 12 分钟

      📱 **小红书文案预览**
      
      **标题**: DeepSeek R1 开源：中国AI的里程碑时刻
      **副标题**: 全网热议，技术圈沸腾
      
      ---
      [完整正文内容]
      ---
      
      🏷️ **标签**: #DeepSeek #AI开源 #人工智能
      
      🖼️ **配图**: 2 张 AI 生成图片
      📊 **数据卡片**: 4 张已就绪（标题卡、辩论时间线、趋势分析、平台雷达图）
      
      ---
      有什么要修改的吗？没有的话回复"OK"我就发布了~
```

**⚠️ 重要**: 必须展示完整预览并等待用户确认！

**卡片元数据规则**:
- MUST: OpenClaw 只把 `cards` / `cards_meta` 视为“可发布资源元数据”
- MUST NOT: OpenClaw 不尝试打开、下载、解析、推断任何本地卡片路径
- 发布时只需要确认卡片是否已就绪，然后调用 `publish_to_xhs(job_id=...)`

### Phase 4: 发布

```
用户: OK，发布吧

助手: 🚀 正在发布到小红书...
      
      [调用 publish_to_xhs]
      
      ✅ 发布成功！
      📝 笔记链接: https://www.xiaohongshu.com/...
```

**用户确认词**: "OK", "好", "发布", "确认", "可以", "没问题", "行"
**用户修改词**: "改", "修改", "标题改成", "内容改成"

---

## 🔧 API 调用方式

### 基础 URL
```
http://localhost:18061
```

### 1. 启动分析任务 (analyze_topic)

```bash
curl -X POST http://localhost:18061/analyze_topic \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "话题内容",
    "platforms": ["wb", "dy", "ks", "bili"],
    "debate_rounds": 2,
    "image_count": 2
  }'
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | ✅ | - | 要分析的话题 |
| platforms | string[] | ❌ | `["wb", "dy", "ks", "bili"]` | 平台代码列表 |
| debate_rounds | int | ❌ | `2` | 辩论轮数 (1-5) |
| image_count | int | ❌ | `2` | **配图数量 (0-9)，默认 2 张** |

**返回**:
```json
{
  "success": true,
  "job_id": "job_20260128_xxx",
  "message": "分析任务已启动"
}
```

### 2. 查询任务状态 (get_analysis_status) ⭐ 轮询用

```bash
curl http://localhost:18061/get_analysis_status/job_xxx
```

**返回**:
```json
{
  "success": true,
  "status": "running",
  "progress": 45,
  "current_step_name": "多角度辩论分析"
}
```

**状态值**: `pending` → `running` → `completed` / `failed`

### 3. 获取分析结果 (get_analysis_result) ⭐ 完成后调用

```bash
curl http://localhost:18061/get_analysis_result/job_xxx
```

**返回内容**:
- `copywriting`: 小红书文案 (title, subtitle, content, tags)
- `cards` / `cards_meta`: 数据卡片元数据（卡片类型、显示名称、是否已就绪）
- `ai_images`: AI 配图 URL 列表
- `summary`: 核心观点摘要
- `insight`: 深度洞察

### 4. 获取热榜 (get_hot_news)

```bash
curl -X POST http://localhost:18061/get_hot_news \
  -H "Content-Type: application/json" \
  -d '{"limit": 20, "include_hn": true}'
```

### 5. 修改文案 (update_copywriting)

```bash
curl -X POST http://localhost:18061/update_copywriting \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job_xxx",
    "title": "新标题",
    "content": "新内容"
  }'
```

### 6. 发布到小红书 (publish_to_xhs)

```bash
curl -X POST http://localhost:18061/publish_to_xhs \
  -H "Content-Type: application/json" \
  -d '{"job_id": "job_xxx"}'
```

### 7. 获取配置 (get_settings)

```bash
curl http://localhost:18061/get_settings
```

### 8. 生成数据卡片 (generate_topic_cards) 🆕

为已完成的分析任务生成数据卡片图片。需要先启动渲染服务。

```bash
curl -X POST http://localhost:18061/generate_topic_cards \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job_xxx",
    "card_types": ["title", "insight", "debate_timeline"]
  }'
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| job_id | string | ❌ | 最近任务 | 分析任务 ID |
| card_types | string[] | ❌ | 全部 | 指定卡片类型，留空生成所有 |

**可用卡片类型**: `title`(标题卡), `insight`(洞察卡), `debate_timeline`(辩论时间线), `trend`(趋势图), `radar`(雷达图), `key_findings`(核心发现), `platform_heat`(平台热度)

**返回**:
```json
{
  "success": true,
  "cards": {
    "title": "/path/to/outputs/cards/title.png",
    "insight": "/path/to/outputs/cards/insight.png"
  },
  "failed": [],
  "message": "✅ 成功生成 7 张卡片"
}
```

**前置条件**: 需要先启动卡片渲染服务：
```bash
./scripts/start-renderer.sh    # 卡片渲染 (端口 3001)
```

---

## 📊 默认参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **image_count** | **2** | AI 配图数量，不指定时生成 2 张 |
| **debate_rounds** | **2** | 辩论轮数，影响分析深度 |
| **platforms** | `["wb", "dy", "ks", "bili"]` | 默认爬取微博、抖音、快手、B站 |
| **polling_interval** | 60 秒 | 状态轮询间隔 |

---

## 🌐 平台代码对照表

⚠️ **必须使用英文代码，不能用中文！**

| 代码 | 平台 | Emoji |
|------|------|-------|
| wb | 微博 | 📱 |
| dy | 抖音 | 🎵 |
| ks | 快手 | 🎬 |
| bili | B站 | 📺 |
| tieba | 贴吧 | 💬 |
| zhihu | 知乎 | 🔍 |
| xhs | 小红书 | 📕 |
| hn | Hacker News | 💻 |
| reddit | Reddit | 🔴 |

✅ 正确: `["wb", "dy", "bili"]`  
❌ 错误: `["微博", "抖音"]`

---

## 📝 消息模板

### 进度消息
```
🔄 任务已启动，正在爬取多平台数据...
📊 进度: {progress}% - {current_step_name}
✅ {平台名}爬取完成 ({数量}条)
🔄 正在进行{步骤名}...
```

### 完成预览消息
```
🎉 **分析完成！** 耗时 {duration} 分钟

📱 **小红书文案预览**

**标题**: {title}
**副标题**: {subtitle}

---
{content}
---

🏷️ **标签**: {tags}

🖼️ **配图**: {image_count} 张
{image_list}

---
有什么要修改的吗？没有的话回复"OK"我就发布了~
```

### 发布成功消息
```
✅ 发布成功！
📝 笔记链接: {note_url}
```

---

## ❌ 错误处理

| 错误 | 症状 | 解决方案 |
|------|------|---------|
| 后端服务不可用 | Connection refused | 提示用户运行 `./start.sh` |
| 已有任务在运行 | "已有任务在运行" | 等待当前任务完成或查询状态 |
| 任务不存在 | "任务不存在" | 检查 job_id 或留空查询最近任务 |
| 发布失败 | publish 返回 false | 检查 XHS MCP 服务是否运行 |
| **没有可发布素材** | `ai_images: []` 且卡片未就绪 | ⚠️ 见下方特别说明 |
| **重复发布** | `already_published: true` | ⚠️ 该任务已发布过，不要再次发布！ |

### 🚨 特别重要：重复发布的处理

当 `publish_to_xhs` 返回 `"already_published": true` 时：

**❌ 绝对错误的做法**:
```
收到 already_published → 再次调用 publish_to_xhs → 导致重复发布被风控
```

**✅ 正确的做法**:
```
助手: ⚠️ 该任务已经发布过了！

如需发布新内容，请重新分析话题。
```

### 🚨 特别重要：发布失败时的正确处理

当 `publish_to_xhs` 返回失败时：

**❌ 绝对错误的做法** (会浪费 10 分钟！):
```
发布失败 → 重新调用 analyze_topic → 再等 10 分钟
```

**✅ 正确的做法**:
```
助手: ❌ 发布失败：没有可发布素材

可能原因：
1. 分析时 image_count 设置为 0，且数据卡片未生成
2. 卡片渲染服务未启动，`generate_topic_cards` 未产出卡片
3. 图片 URL 已过期且卡片也不可用

建议：
• 先调用 `generate_topic_cards(job_id=...)`，确认 4 张核心卡就绪
• 确认发布模式为 `ai_and_cards`（默认）再调用 `publish_to_xhs`
• 文案内容已保存，无需重新分析
```

**⚠️ 记住**: 分析任务耗时 8-12 分钟，绝对不要因为发布失败就重跑！

---

## 🚀 前置条件

使用前确保服务已启动：

```bash
cd /Users/napstablook/Projects/GlobalInSight
./start.sh                        # 后端 API (端口 8000)
./scripts/start-opinion-mcp.sh    # Opinion MCP (端口 18061)
./scripts/start-xhs-mcp.sh        # 小红书发布 (端口 18060，可选)
./scripts/start-renderer.sh       # 卡片渲染 (端口 3001，可选)
```

检查服务状态：
```bash
curl http://localhost:8000/api/health
curl http://localhost:18061/health
curl http://localhost:3001/healthz   # 渲染服务
```

---

## 📌 服务端点

| 服务 | 端口 | 检查命令 |
|------|------|---------|
| 后端 API | 8000 | `curl http://localhost:8000/api/health` |
| Opinion MCP | 18061 | `curl http://localhost:18061/health` |
| XHS MCP | 18060 | `curl http://localhost:18060/mcp` |
| 卡片渲染 | 3001 | `curl http://localhost:3001/healthz` |

---

## 💬 完整对话示例 (FULL CONVERSATION EXAMPLE)

以下是一个完整的、正确的对话流程示例：

```
👤 用户: 帮我分析一下张学友拒四大天王合体

🤖 助手: 好的！在开始分析前，请确认以下配置：

📌 **话题**: 张学友拒四大天王合体

🌐 **选择爬取平台** (回复数字，用逗号分隔):
1️⃣ 微博   2️⃣ 抖音   3️⃣ 快手   4️⃣ B站
5️⃣ 贴吧   6️⃣ 知乎   7️⃣ 小红书
8️⃣ Hacker News   9️⃣ Reddit

🖼️ **AI 配图数量**: 0-9张

📝 回复示例: "默认" 或 "1,2,6 + 3张图"

👤 用户: 默认

🤖 助手: ✅ 配置确认：
📌 话题: 张学友拒四大天王合体
🌐 平台: 微博、抖音、快手、B站
🖼️ AI配图: 2张
⏱️ 预计耗时: 8-12 分钟

🔄 任务已启动 (job_id: job_20260128_164315_xxx)
正在爬取多平台数据...

[等待 60 秒后轮询]
→ get_analysis_status: progress=10, current_step_name="多平台数据爬取", current_platform="dy"

🤖 助手: 📊 进度: 10% — 🎵 开始爬取抖音

[等待 60 秒后轮询]
→ get_analysis_status: progress=20, current_step_name="多平台数据爬取", current_platform="ks"

🤖 助手: 📊 进度: 20% — 🎬 开始爬取快手

[等待 60 秒后轮询]
→ get_analysis_status: progress=40, current_step_name="事实提炼汇总"

🤖 助手: 📊 进度: 40% — 🤖 已开始 Multi-agent 推理（事实提炼汇总）

[等待 60 秒后轮询]
→ get_analysis_status: progress=60, current_step_name="多角度辩论分析"

🤖 助手: 📊 进度: 60% — 🗣️ Multi-agent 辩论分析进行中

[等待 60 秒后轮询]
→ get_analysis_status: progress=90, current_step_name="生成 AI 配图"

🤖 助手: 📊 进度: 90% — 🎨 正在生成 AI 配图

[任务完成]

[调用 generate_topic_cards(job_id=job_20260128_164315_xxx)]

🤖 助手: 📊 正在生成数据卡片...

[卡片生成完成]

🤖 助手: ✅ 数据卡片已生成（标题卡、洞察卡、平台热度、雷达图、核心发现）

[调用 get_analysis_result]
🤖 助手: 🎉 **分析完成！** 耗时 9.8 分钟

📱 **小红书文案预览**

**标题**: 张学友一句话，打碎了多少人的青春滤镜🍂
**副标题**: 怀旧情绪与个体发展的时代碰撞

---
四大天王合体？张学友直接说：别等了。

最近采访里，歌神聊到这个话题，态度很明确。👉 他说"四大天王"是特定时代的产物，大家早就各自精彩了。💡 他不想活在过去的标签里，更希望把那份美好留在回忆里，自己则专注未来的新作品。

说白了，经典之所以是经典，就是因为它定格在了最好的时候。强行"爷青回"，可能滤镜碎一地。

你支持他的决定吗？
---

🏷️ **标签**: #张学友 #四大天王 #爷青结 #娱乐圈 #经典回忆

🖼️ **配图**: 2 张 AI 生成图片
📊 **数据卡片**: 5 张（标题卡、洞察卡、平台热度、雷达图、核心发现）

---
有什么要修改的吗？没有的话回复"OK"我就发布了~

👤 用户: OK

🤖 助手: 🚀 正在发布到小红书...

✅ 发布成功！
📝 笔记链接: https://www.xiaohongshu.com/explore/xxx
```

---

**最后更新**: 2026-03-09
**维护者**: GlobalInSight 开发团队
