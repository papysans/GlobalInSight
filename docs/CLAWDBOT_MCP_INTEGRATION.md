# Opinion MCP 服务 - ClawdBot 集成指南

> ✅ **状态**: 已验证可用 (2026-01-28)  
> 🔧 **最近更新**: 修复 mcporter SSE 兼容性问题

## 服务概述

Opinion MCP 是 GlobalInSight 舆论分析系统的 MCP 服务封装，可与 ClawdBot 等 MCP 客户端集成。

**服务地址**: `http://localhost:18061`

### 运行时绑定方式

- `mcporter / ClawdBot` 使用 base URL: `http://localhost:18061`
- `原生 MCP SSE` 使用 URL: `http://localhost:18061/sse`
- 逻辑 server name 统一为 `opinion-analyzer`

最小配置示例：

```json
{
  "mcpServers": {
    "opinion-analyzer": {
      "url": "http://localhost:18061"
    }
  }
}
```

仓库内提供的原生 MCP 示例文件见 [docs/clawdbot-skill/mcp.json](/Volumes/Work/Projects/GlobalInSight/docs/clawdbot-skill/mcp.json)。

### 支持的端点

| 端点 | 用途 |
|------|------|
| `GET /sse` | SSE 连接（标准 MCP） |
| `POST /mcp` | JSON-RPC 请求 |
| `POST /message` | JSON-RPC 请求（带 sessionId） |
| `GET /` `POST /` | 根路径兼容（mcporter fallback） |
| `GET /health` | 健康检查 |
| `GET /docs` | API 文档 |

## 🎯 推荐：使用拆分后的 ClawdBot Skills

**不需要每次都喂文档！** 推荐把原来的单体 skill 拆成 3 个单一意图的 skill，避免“今日热点”误入深度分析流程。

原始单体版已归档到 `docs/clawdbot-skill/backups/20260310-143835-opinion-analyzer-original/`。

现在还额外提供一个兼容旧命令的总控 router skill：`opinion-analyzer`。它恢复原来的入口，但内部按原子步骤和状态总线执行。

### 安装方法

**方法一：复制到 skills 目录（推荐）**

```bash
# 安装 3 个技能
for skill in opinion-hot-news opinion-topic-analysis xhs-publisher; do
  mkdir -p ~/.clawdbot/skills/$skill
  cp docs/clawdbot-skill/$skill/SKILL.md ~/.clawdbot/skills/$skill/
done
```
这 3 个 skill 现在都是“单文件平铺版”，OpenClaw 不需要额外读取 `references/`。

**可选：安装兼容旧命令的 router skill**

```bash
mkdir -p ~/.clawdbot/skills/opinion-analyzer
cp docs/clawdbot-skill/SKILL.md ~/.clawdbot/skills/opinion-analyzer/
cp -R docs/clawdbot-skill/references ~/.clawdbot/skills/opinion-analyzer/
```

**方法二：使用 ClawdHub CLI**

```bash
# 如果已发布到 ClawdHub，可分别安装
npx clawdhub@latest install opinion-hot-news
npx clawdhub@latest install opinion-topic-analysis
npx clawdhub@latest install xhs-publisher
```

### Skills 加载优先级

| 位置 | 路径 | 优先级 |
|------|------|--------|
| 工作区 | `<project>/skills/` | ⭐⭐⭐ 最高 |
| 用户目录 | `~/.clawdbot/skills/` | ⭐⭐ 中等 |
| 内置 | (随安装包) | ⭐ 最低 |

### 验证安装

```bash
# 检查文件是否存在
ls ~/.clawdbot/skills/opinion-analyzer/SKILL.md
ls ~/.clawdbot/skills/opinion-hot-news/SKILL.md
ls ~/.clawdbot/skills/opinion-topic-analysis/SKILL.md
ls ~/.clawdbot/skills/xhs-publisher/SKILL.md

# 在 ClawdBot 中开始新会话
# 输入 /new 或重启 Gateway
```

### 使用方式

安装后，有两种调用方式：

**方式一：斜杠命令**
```
/opinion-analyzer 分析一下 DeepSeek R1 开源
/opinion-hot-news 看看今日热点
/opinion-topic-analysis 分析一下 DeepSeek R1 开源
/xhs-publisher 发布最近完成的任务
```

输入 `/` 后，ClawdBot 会自动显示可用技能列表。

**方式二：自然语言**
```
帮我分析一下大批中成药将退出市场这个话题
```

ClawdBot 会根据 description 自动识别并调用对应技能。

### Skill 激活触发词

推荐按意图拆分触发：
- `opinion-analyzer`: 兼容旧入口，先路由再执行原子步骤
- `opinion-hot-news`: “今日热点”“热榜”“榜单”“今天有什么值得关注的话题”
- `opinion-topic-analysis`: “分析一下 XXX”“做舆情分析”“分析这个话题”
- `xhs-publisher`: “发到小红书”“发布最近完成的任务”“改下标题再发”

### ⚠️ 常见问题

**Q: Skill 没有加载？**
1. 检查路径是否正确：
   - `~/.clawdbot/skills/opinion-analyzer/SKILL.md`
   - `~/.clawdbot/skills/opinion-hot-news/SKILL.md`
   - `~/.clawdbot/skills/opinion-topic-analysis/SKILL.md`
   - `~/.clawdbot/skills/xhs-publisher/SKILL.md`
2. 开始新会话：在 ClawdBot 中输入 `/new`
3. 检查 YAML 格式：metadata 必须是单行 JSON

**Q: 输入 `/` 没有显示技能？**
- 确保 Gateway 已重启
- 检查 skills 目录权限
- 查看 ClawdBot 日志确认技能是否加载

---

## ⚠️ 重要：调用方式说明

### 推荐方式：标准 MCP 协议

**ClawdBot 应该使用标准 MCP 协议连接**，而不是直接调用 REST API。

标准 MCP 协议通过 SSE + JSON-RPC 调用：

```
1. 建立 SSE 连接: GET /sse
   → 服务器返回 endpoint 事件，告知 POST 地址
   
2. 发送 JSON-RPC 请求: POST /message?sessionId=xxx
   → 请求体为 JSON-RPC 格式
   
3. 通过 SSE 接收响应
   → 响应通过 SSE 推送回来
```

**JSON-RPC 调用示例**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "analyze_topic",
    "arguments": {
      "topic": "DeepSeek R1 开源",
      "image_count": 3
    }
  },
  "id": 1
}
```

**可用的 JSON-RPC 方法**:
- `initialize` - 初始化连接
- `tools/list` - 列出所有可用工具
- `tools/call` - 调用工具（最常用）
- `ping` - 心跳检测

### 备用方式：直接 REST API

> ⚠️ **仅在 MCP 协议不可用时使用**
> 
> REST API 是为了兼容不支持标准 MCP 协议的客户端而提供的。
> 如果你的 MCP 客户端支持标准协议，请优先使用上面的方式。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/analyze_topic` | POST | 启动分析 |
| `/get_analysis_status` | POST/GET | 查询状态 |
| `/get_analysis_result` | POST/GET | 获取结果 |
| `/get_hot_news` | POST/GET | 获取热榜 |
| `/get_settings` | POST/GET | 获取设置 |
| `/publish_to_xhs` | POST | 发布小红书 |
| `/register_webhook` | POST | 注册回调 |
| `/update_copywriting` | POST | 更新文案 |

**REST 调用示例**:
```bash
curl -X POST http://localhost:18061/analyze_topic \
  -H "Content-Type: application/json" \
  -d '{"topic": "DeepSeek R1 开源", "image_count": 3}'
```

### 如何判断使用哪种方式？

| 场景 | 推荐方式 |
|------|---------|
| ClawdBot 通过 MCP 配置连接 | 标准 MCP 协议 (自动) |
| 手动测试/调试 | REST API |
| 其他程序集成 | REST API |
| MCP 协议连接失败 | REST API (降级) |

## ClawdBot 使用建议

### 1. 分析话题时的交互流程

当用户说"分析XXX话题"时，建议的交互流程：

```
用户: 分析一下大批中成药将退出市场

ClawdBot 应该:
1. 先询问用户偏好（可选）:
   - "需要生成几张配图？(0-9张，默认2张)"
   - "要爬取哪些平台？(默认: 微博、抖音、快手、B站)"
   
2. 或者直接使用默认参数启动分析:
   → 调用 analyze_topic(topic="大批中成药将退出市场")
   
3. 告知用户任务已启动，预计时间
```

### 2. 任务完成通知

MCP 支持 Webhook 推送，ClawdBot 可以注册回调来接收完成通知：

```
1. 启动分析后，调用 register_webhook:
   → register_webhook(callback_url="你的回调地址", job_id="任务ID")
   
2. 任务完成时，MCP 会推送事件到回调地址:
   {
     "event": "completed",
     "job_id": "xxx",
     "result": { ... }
   }
```

### 3. 推荐的对话模板

**简单模式（直接分析）**:
```
用户: 分析XXX
→ 直接调用 analyze_topic(topic="XXX", image_count=2)
→ 返回: "已启动分析，预计15分钟完成，完成后我会通知你"
```

**交互模式（询问偏好）**:
```
用户: 分析XXX
→ 询问: "好的，我来分析这个话题。请问：
   1. 需要生成几张配图？(默认2张)
   2. 要爬取哪些平台？(默认: 微博、抖音、快手、B站)"
   
用户: 3张图，加上知乎
→ 调用 analyze_topic(topic="XXX", image_count=3, platforms=["wb","dy","ks","bili","zhihu"])
```

## 可用工具 (8个)

### 1. analyze_topic
启动舆论分析任务，返回 job_id。

**参数**:
- `topic` (必填): 要分析的话题
- `platforms` (可选): 平台列表，如 `["wb", "dy", "bili"]`
- `debate_rounds` (可选): 辩论轮数 1-5，默认 2，轮数越多分析越深入
- `image_count` (可选): 生成图片数 0-9，默认 2

**示例**:
```json
{
  "topic": "DeepSeek R1 开源",
  "platforms": ["wb", "zhihu", "hn"],
  "debate_rounds": 3,
  "image_count": 3
}
```

### 2. get_analysis_status
查询任务进度。

**参数**:
- `job_id` (可选): 任务 ID，留空查询最近任务

**返回**:
```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": 45,
  "current_step": "crawling",
  "message": "正在爬取微博..."
}
```

### 3. get_analysis_result
获取分析结果，包含文案和配图。

**参数**:
- `job_id` (可选): 任务 ID

**返回**:
```json
{
  "job_id": "abc123",
  "status": "completed",
  "copywriting": {
    "title": "标题",
    "subtitle": "副标题",
    "content": "正文内容...",
    "tags": ["标签1", "标签2"]
  },
  "ai_images": ["https://...", "https://..."],
  "cards": [...]
}
```

### 4. get_hot_news
获取多平台热榜数据。

**参数**:
- `limit` (可选): 返回条数，默认 20
- `include_hn` (可选): 是否包含 Hacker News，默认 true

### 5. get_settings
获取当前配置（默认平台、图片数量等）。

### 6. update_copywriting
修改分析结果的文案。

**参数**:
- `job_id` (必填): 任务 ID
- `title` (可选): 新标题
- `content` (可选): 新正文
- `tags` (可选): 新标签列表

### 7. publish_to_xhs
发布到小红书。

**参数**:
- `job_id` (必填): 任务 ID
- `title` (可选): 自定义标题
- `tags` (可选): 自定义标签

**⚠️ 重要**: 每个 job_id 只能发布一次！如果返回 `already_published: true`，说明已发布过。

### 8. register_webhook
注册进度推送回调。

**参数**:
- `callback_url` (必填): 回调 URL
- `job_id` (必填): 任务 ID

**Webhook 事件类型**:
- `started` - 任务开始
- `progress` - 进度更新
- `platform_done` - 单个平台爬取完成
- `step_change` - 步骤变更
- `completed` - 任务完成（包含完整结果）
- `failed` - 任务失败

## ⚠️ 关键行为规则

### 必须遵守 (MUST DO)
| 规则 | 说明 |
|------|------|
| **M0** | 启动分析前必须询问平台、图片数量、辩论轮次 |
| **M1** | 启动任务后每 60 秒轮询状态 |
| **M2** | 任务完成后展示完整文案预览 |
| **M3** | 等待用户确认后才发布 |

### 禁止行为 (MUST NOT)
| 规则 | 说明 |
|------|------|
| **N5** | 🚨 发布失败时禁止重新分析（浪费 10 分钟！） |
| **N6** | 🚨 禁止重复发布同一任务（会被风控！） |

## 典型使用流程

```
1. 用户: "分析一下 DeepSeek R1"
   → 调用 analyze_topic(topic="DeepSeek R1")
   → 返回 job_id
   → 可选: 调用 register_webhook 注册完成通知

2. 轮询进度 (或等待 webhook)
   → 调用 get_analysis_status(job_id)
   → 返回 progress: 45%

3. 任务完成后获取结果
   → 调用 get_analysis_result(job_id)
   → 返回文案 + 配图

4. 用户确认后发布
   → 调用 publish_to_xhs(job_id)
```

## 支持的平台代码

| 代码 | 平台 | 说明 |
|------|------|------|
| wb | 微博 | 国内热门 |
| dy | 抖音 | 短视频 |
| ks | 快手 | 短视频 |
| bili | B站 | 视频社区 |
| tieba | 贴吧 | 论坛 |
| zhihu | 知乎 | 问答 |
| xhs | 小红书 | 生活分享 |
| hn | Hacker News | 科技新闻 |
| reddit | Reddit | 国外论坛 |

**默认平台**: wb, dy, ks, bili

## 状态码

| 状态 | 说明 |
|------|------|
| pending | 等待开始 |
| running | 执行中 |
| completed | 已完成 |
| failed | 失败 |

## 依赖服务

Opinion MCP 需要后端服务运行：
- 后端 API: `http://localhost:8000`
- 小红书 MCP (发布功能): `http://localhost:18060`

## 启动命令

```bash
# 启动所有服务
./start.sh

# 或单独启动 Opinion MCP
./scripts/start-opinion-mcp.sh
```

## 🔧 故障排除

### 问题 1: mcporter 显示 "tools unavailable"

**症状**:
```
opinion-analyzer
tools unavailable · 16ms · HTTP http://localhost:18061/
Tools: <timed out after 30000ms>
Reason: SSE error: Non-200 status code (404)
```

**原因**: mcporter 的 SSE 客户端会先尝试 `POST /` 和 `GET /`

**解决方案**: 已修复。服务器现在支持根路径请求，会自动路由到 MCP 处理器。

### 问题 2: 任务状态查询 404

**症状**:
```
GET /get_analysis_status/job_xxx HTTP/1.1" 404 Not Found
```

**原因**: ClawdBot 使用路径参数风格调用，但服务器只支持查询参数

**解决方案**: 已修复。现在同时支持两种风格：
- 路径参数: `GET /get_analysis_status/{job_id}`
- 查询参数: `GET /get_analysis_status?job_id=xxx`
- POST body: `POST /get_analysis_status` + `{"job_id": "xxx"}`

### 问题 3: Pydantic 警告

**症状**:
```
PydanticDeprecatedSince20: The `dict` method is deprecated
```

**解决方案**: 已修复。使用 `model_dump()` 替代 `dict()`。

### 问题 4: 分析任务卡在 0%

**可能原因**:
1. 后端服务 (8000) 未启动
2. MediaCrawler 爬虫配置问题
3. 平台 cookie 过期

**排查步骤**:
```bash
# 1. 检查后端服务
curl http://localhost:8000/health

# 2. 检查 Opinion MCP 日志
# 查看终端输出

# 3. 重启服务
./start.sh
```

### 问题 5: MCP 连接但工具调用失败

**排查**:
```bash
# 测试 MCP 端点
curl -X POST http://localhost:18061/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# 测试 REST 端点
curl http://localhost:18061/get_hot_news
```

## 📝 更新日志

### 2026-01-28 (最新)
- ✅ 新增防重复发布机制 (`already_published` 检测)
- ✅ 新增辩论轮次配置 (`debate_rounds` 参数)
- ✅ 更新 SKILL.md 添加 Phase 0 参数询问流程
- ✅ 添加 N5/N6 规则防止错误行为
- ✅ 修复 mcporter SSE 兼容性（添加根路径处理器）
- ✅ 添加路径参数支持 (`/get_analysis_status/{job_id}`)
- ✅ 修复 Pydantic v2 弃用警告
- ✅ 验证 MCP 协议完整工作流程

### 2026-01-27
- ✅ 修复 REST API 类型注解问题
- ✅ 创建 ClawdBot Skill 文档
