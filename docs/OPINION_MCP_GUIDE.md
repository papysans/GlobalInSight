# Opinion MCP 服务使用指南

> 📅 创建日期: 2026-01-28  
> 🎯 目标: 提供 Opinion MCP 服务的完整使用指南  
> 📌 版本: 1.0.0

---

## 概述

Opinion MCP Server 是 GlobalInSight 舆论分析系统的 MCP (Model Context Protocol) 服务封装。它将舆论推理功能暴露为标准 MCP 工具，供 AI 助手（如 ClawdBot）调用，实现跨平台的智能舆情分析。

### 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 舆论分析 | 多平台数据爬取 + LLM 多阶段分析 |
| 📊 热榜获取 | 聚合多平台热点话题 |
| 📝 文案编辑 | 修改生成的小红书文案 |
| 📕 小红书发布 | 一键发布分析结果到小红书 |
| 🔔 进度推送 | Webhook 实时推送分析进度 |

### 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Telegram User                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ClawdBot (Moltbot Gateway)                        │
│                    - mcporter skill (MCP client)                     │
│                    - Telegram Bot interface                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │ MCP Protocol (HTTP)
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Opinion MCP Server (Port 18061)                   │
│                    - FastAPI + MCP 协议兼容                          │
│                    - 8 个 MCP 工具                                   │
│                    - 异步任务管理                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │ HTTP REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Existing FastAPI Backend (Port 8000)              │
│                    - /api/analyze (SSE streaming)                    │
│                    - /api/hotnews                                    │
│                    - /api/workflow/status                            │
│                    - /api/xhs/publish                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 运行时绑定

- `mcporter / ClawdBot`: server name=`opinion-analyzer`, URL=`http://localhost:18061`
- `原生 MCP SSE`: transport=`sse`, URL=`http://localhost:18061/sse`

最小 `mcporter` 配置示例：

```json
{
  "mcpServers": {
    "opinion-analyzer": {
      "url": "http://localhost:18061"
    }
  }
}
```

---

## 安装与启动

### 1. 环境要求

- Python 3.9+
- 已安装 GlobalInSight 后端依赖
- 后端服务运行在 `localhost:8000`

### 2. 安装依赖

```bash
# 进入项目目录
cd GlobalInSight

# 激活虚拟环境
source .venv/bin/activate

# 依赖已包含在 requirements.txt 中
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 方式 1: 使用启动脚本
./scripts/start-opinion-mcp.sh

# 方式 2: 直接运行
python -m opinion_mcp.server --port 18061

# 方式 3: 自定义配置
python -m opinion_mcp.server --host 0.0.0.0 --port 18062 --debug
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:18061/health

# MCP 服务信息
curl http://localhost:18061/mcp

# 获取工具列表
curl http://localhost:18061/mcp/tools
```

---

## 可用工具

Opinion MCP Server 提供 8 个 MCP 工具：

| 工具名称 | 功能 | 必需参数 |
|---------|------|---------|
| `analyze_topic` | 启动舆论分析任务 | `topic` |
| `get_analysis_status` | 查询分析进度 | - |
| `get_analysis_result` | 获取分析结果 | - |
| `update_copywriting` | 修改文案内容 | `job_id` |
| `get_hot_news` | 获取热榜数据 | - |
| `publish_to_xhs` | 发布到小红书 | `job_id` |
| `get_settings` | 获取配置信息 | - |
| `register_webhook` | 注册进度回调 | `callback_url`, `job_id` |

---

### Tool 1: `analyze_topic`

启动舆论分析任务。由于分析过程需要约 15 分钟，该工具会立即返回 `job_id`，分析在后台执行。

**参数:**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `topic` | string | ✅ | - | 要分析的话题/议题 |
| `platforms` | array | ❌ | 默认平台 | 爬取平台列表 |
| `debate_rounds` | integer | ❌ | 2 | 辩论轮数 (1-5) |
| `image_count` | integer | ❌ | 2 | AI 配图数量 (0-9) |

**可用平台代码:**

| 代码 | 平台 | Emoji |
|------|------|-------|
| `wb` | 微博 | 📱 |
| `dy` | 抖音 | 🎵 |
| `ks` | 快手 | 🎬 |
| `bili` | B站 | 📺 |
| `tieba` | 贴吧 | 💬 |
| `zhihu` | 知乎 | 🔍 |
| `xhs` | 小红书 | 📕 |
| `hn` | Hacker News | 💻 |
| `reddit` | Reddit | 🔴 |

**请求示例:**

```json
{
  "name": "analyze_topic",
  "arguments": {
    "topic": "DeepSeek开源",
    "platforms": ["wb", "dy", "bili", "zhihu"],
    "debate_rounds": 2,
    "image_count": 3
  }
}
```

**响应示例:**

```json
{
  "success": true,
  "job_id": "job_20260128_143052_abc123",
  "message": "分析任务已启动",
  "estimated_time_minutes": 15,
  "platforms": ["wb", "dy", "bili", "zhihu"],
  "hint": "请使用 get_analysis_status 查询进度"
}
```

---

### Tool 2: `get_analysis_status`

查询分析任务的当前状态和进度。

**参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `job_id` | string | ❌ | 任务 ID，留空查询最近任务 |

**响应示例:**

```json
{
  "success": true,
  "job_id": "job_20260128_143052_abc123",
  "running": true,
  "current_step": "debater",
  "current_step_name": "多角度辩论分析",
  "progress": 60,
  "topic": "DeepSeek开源",
  "current_platform": null,
  "started_at": "2026-01-28T14:30:52",
  "elapsed_minutes": 8.5,
  "estimated_remaining_minutes": 6.5
}
```

**进度步骤映射:**

| Step | 步骤名称 | 进度 |
|------|---------|------|
| `crawler_agent` | 多平台数据爬取 | 10% |
| `reporter` | 事实提炼汇总 | 25% |
| `analyst` | 舆论态势分析 | 40% |
| `debater` | 多角度辩论 | 60% |
| `writer` | 文案生成 | 80% |
| `image_generator` | 图片生成 | 95% |
| `finished` | 完成 | 100% |

---

### Tool 3: `get_analysis_result`

获取已完成的分析结果，包含文案和所有配图。

**参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `job_id` | string | ❌ | 任务 ID，留空获取最近完成的任务 |

**响应示例:**

```json
{
  "success": true,
  "job_id": "job_20260128_143052_abc123",
  "topic": "DeepSeek开源",
  "copywriting": {
    "title": "DeepSeek开源：中国AI的里程碑时刻",
    "subtitle": "全网热议，技术圈沸腾",
    "content": "完整文案内容...",
    "tags": ["DeepSeek", "AI开源", "人工智能"]
  },
  "cards": {
    "title_card": "https://...",
    "debate_timeline": "https://...",
    "trend_analysis": "https://...",
    "platform_radar": "https://..."
  },
  "ai_images": ["https://..."],
  "summary": "核心观点摘要...",
  "insight": "深度洞察分析...",
  "platforms_analyzed": ["微博", "抖音", "B站", "知乎"],
  "platform_stats": {
    "wb": 45,
    "dy": 32,
    "bili": 28,
    "zhihu": 22
  },
  "output_file": "outputs/2026-01-28_14-30-52_DeepSeek开源.md",
  "completed_at": "2026-01-28T14:45:30",
  "duration_minutes": 14.6
}
```

---

### Tool 4: `update_copywriting`

修改分析结果的文案内容（发布前编辑）。

**参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `job_id` | string | ✅ | 任务 ID |
| `title` | string | ❌ | 新标题 |
| `subtitle` | string | ❌ | 新副标题 |
| `content` | string | ❌ | 新正文内容 |
| `tags` | array | ❌ | 新标签列表 |

**请求示例:**

```json
{
  "name": "update_copywriting",
  "arguments": {
    "job_id": "job_20260128_143052_abc123",
    "title": "DeepSeek震撼开源"
  }
}
```

**响应示例:**

```json
{
  "success": true,
  "job_id": "job_20260128_143052_abc123",
  "updated_fields": ["title"],
  "copywriting": {
    "title": "DeepSeek震撼开源",
    "subtitle": "全网热议，技术圈沸腾",
    "content": "...",
    "tags": ["DeepSeek", "AI开源"]
  }
}
```

---

### Tool 5: `get_hot_news`

获取多平台热榜数据，用于发现热门话题。

**参数:**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `limit` | integer | ❌ | 20 | 返回条数 (1-100) |
| `platforms` | array | ❌ | 全部 | 筛选平台 |
| `include_hn` | boolean | ❌ | true | 是否包含 Hacker News |

**响应示例:**

```json
{
  "success": true,
  "items": [
    {
      "id": "cluster_001",
      "title": "DeepSeek开源引发全球关注",
      "hot_score": 9850,
      "platforms": ["微博", "知乎", "B站"],
      "growth": 15.2,
      "is_new": false
    }
  ],
  "total": 20,
  "collection_time": "2026-01-28T14:00:00",
  "from_cache": true
}
```

---

### Tool 6: `publish_to_xhs`

将分析结果发布到小红书。

**前置条件:**
- 小红书 MCP 服务运行在 `localhost:18060`
- 已完成小红书登录（参考 `docs/XHS_SETUP.md`）

**参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `job_id` | string | ✅ | 分析任务 ID |
| `title` | string | ❌ | 自定义标题 |
| `tags` | array | ❌ | 话题标签 |

**响应示例:**

```json
{
  "success": true,
  "job_id": "job_20260128_143052_abc123",
  "note_url": "https://www.xiaohongshu.com/explore/...",
  "message": "发布成功"
}
```

---

### Tool 7: `get_settings`

获取当前的分析配置信息。

**响应示例:**

```json
{
  "success": true,
  "default_platforms": ["wb", "dy", "ks", "bili"],
  "image_count": 2,
  "debate_rounds": 2,
  "available_platforms": [
    {"code": "wb", "name": "微博", "emoji": "📱"},
    {"code": "dy", "name": "抖音", "emoji": "🎵"},
    {"code": "ks", "name": "快手", "emoji": "🎬"},
    {"code": "bili", "name": "B站", "emoji": "📺"},
    {"code": "tieba", "name": "贴吧", "emoji": "💬"},
    {"code": "zhihu", "name": "知乎", "emoji": "🔍"},
    {"code": "xhs", "name": "小红书", "emoji": "📕"},
    {"code": "hn", "name": "Hacker News", "emoji": "💻"},
    {"code": "reddit", "name": "Reddit", "emoji": "🔴"}
  ]
}
```

---

### Tool 8: `register_webhook`

注册进度推送的 Webhook URL。MCP Server 会在关键节点主动推送进度到指定 URL。

**参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `callback_url` | string | ✅ | 接收进度推送的 URL |
| `job_id` | string | ✅ | 要监听的任务 ID |

**请求示例:**

```json
{
  "name": "register_webhook",
  "arguments": {
    "callback_url": "https://your-server.com/webhook",
    "job_id": "job_20260128_143052_abc123"
  }
}
```

**响应示例:**

```json
{
  "success": true,
  "message": "Webhook 注册成功"
}
```

---

## ClawdBot 集成

### 配置 ClawdBot

ClawdBot 使用 `mcporter` skill 连接 MCP 服务器。推荐把交互拆成 3 个 skills：

- `opinion-analyzer`（兼容旧入口的 router skill）
- `opinion-hot-news`
- `opinion-topic-analysis`
- `xhs-publisher`

其中 `opinion-hot-news`、`opinion-topic-analysis`、`xhs-publisher` 现在都采用“单文件平铺”的原子步骤结构，安装时只需要复制各自的 `SKILL.md`。

在 ClawdBot 配置文件中添加：

```yaml
# clawdbot-config.yaml
skills:
  - name: mcporter
    config:
      servers:
        - name: opinion-analyzer
          url: http://localhost:18061
          description: "GlobalInSight 舆论分析服务"
```

### 完整对话流程示例

```
用户: 帮我爬取"Deepseek开源"这个话题的热度

ClawdBot: 好的！你要爬取哪些平台？我们支持：
  📱 微博 (wb)
  🎵 抖音 (dy)  
  🎬 快手 (ks)
  📺 B站 (bili)
  💬 贴吧 (tieba)
  🔍 知乎 (zhihu)
  📕 小红书 (xhs)
  💻 Hacker News (hn)
  
  回复平台代码，或回复"全部"爬取所有平台

用户: 全部

ClawdBot: 要附上几张AI生图呢？(0-9张，默认2张)

用户: 1张

ClawdBot: 收到！任务配置：
  📌 话题: Deepseek开源
  🌐 平台: 全部 (8个)
  🖼️ AI配图: 1张
  
  开始分析，预计需要15分钟...

--- 进度推送 (Webhook) ---

ClawdBot: 🔄 开始多平台数据爬取...
ClawdBot: ✅ 微博爬取完成 (45条)
ClawdBot: ✅ 抖音爬取完成 (32条)
ClawdBot: ✅ B站爬取完成 (28条)
...
ClawdBot: 🔄 正在进行事实提炼汇总...
ClawdBot: 🔄 正在进行舆论态势分析...
ClawdBot: 🔄 正在进行多角度辩论 (第1轮/共2轮)...
ClawdBot: 🔄 正在进行多角度辩论 (第2轮/共2轮)...
ClawdBot: 🔄 正在生成小红书文案...
ClawdBot: 🔄 正在生成数据卡片...
ClawdBot: 🔄 正在生成AI配图 (1/1)...

--- 结果预览 ---

ClawdBot: 🎉 分析完成！耗时14分32秒

📱 **小红书文案预览**

**标题**: DeepSeek开源：中国AI的里程碑时刻
**副标题**: 全网热议，技术圈沸腾

---
{完整文案内容}
---

🖼️ **配图预览** (共5张)
1. 📊 标题卡片 [图片]
2. 📈 辩论演化时间线 [图片]
3. 📉 热度趋势分析 [图片]
4. 🎯 平台覆盖雷达图 [图片]
5. 🎨 AI配图 [图片]

有什么要修改的吗？没有的话我直接发布了哦~

用户: 标题改一下，改成"DeepSeek震撼开源"

ClawdBot: 好的，已修改标题。现在这样可以了吗？

**标题**: DeepSeek震撼开源
**副标题**: 全网热议，技术圈沸腾
...

用户: OK，发布吧

ClawdBot: 🚀 正在发布到小红书...
ClawdBot: ✅ 发布成功！
  📝 笔记链接: https://www.xiaohongshu.com/...
```

---

## Webhook 事件格式

### 事件类型

| event_type | 说明 | 触发时机 |
|------------|------|---------|
| `started` | 任务开始 | 分析任务启动时 |
| `progress` | 进度更新 | 进度变化时 |
| `platform_done` | 平台爬取完成 | 单个平台数据爬取完成 |
| `step_change` | 步骤变更 | 进入新的分析步骤 |
| `completed` | 任务完成 | 分析全部完成 |
| `failed` | 任务失败 | 分析过程出错 |

### Webhook 推送格式

```json
{
  "job_id": "job_20260128_143052_abc123",
  "event_type": "progress",
  "timestamp": "2026-01-28T14:35:00",
  "data": {
    "step": "crawler_agent",
    "step_name": "多平台数据爬取",
    "progress": 15,
    "message": "✅ 微博爬取完成 (45条)",
    "platform": "wb",
    "platform_count": 45
  }
}
```

### 各事件类型的 data 字段

#### `started` 事件
```json
{
  "step": "crawler_agent",
  "step_name": "多平台数据爬取",
  "progress": 0,
  "message": "🔄 分析任务已启动"
}
```

#### `platform_done` 事件
```json
{
  "step": "crawler_agent",
  "step_name": "多平台数据爬取",
  "progress": 15,
  "message": "✅ 微博爬取完成 (45条)",
  "platform": "wb",
  "platform_name": "微博",
  "platform_count": 45
}
```

#### `step_change` 事件
```json
{
  "step": "debater",
  "step_name": "多角度辩论分析",
  "progress": 60,
  "message": "🔄 正在进行多角度辩论 (第1轮/共2轮)..."
}
```

#### `completed` 事件
```json
{
  "step": "finished",
  "step_name": "完成",
  "progress": 100,
  "message": "🎉 分析完成！",
  "result": {
    "summary": "...",
    "insight": "...",
    "copywriting": {...},
    "cards": {...},
    "ai_images": [...]
  }
}
```

#### `failed` 事件
```json
{
  "step": "crawler_agent",
  "step_name": "多平台数据爬取",
  "progress": 10,
  "message": "❌ 分析失败",
  "error": "后端服务不可用"
}
```

### Webhook 重试机制

- 最多重试 3 次
- 使用指数退避策略：1s → 2s → 4s
- 所有重试失败后记录日志，不影响主流程

---

## 常见问题解答

### Q1: 服务启动失败，提示端口被占用

**解决方案:**

```bash
# 检查端口占用
lsof -i :18061

# 终止占用进程
kill -9 <PID>

# 或使用其他端口启动
python -m opinion_mcp.server --port 18062
```

### Q2: 分析任务一直卡在某个步骤

**可能原因:**
1. 后端服务 (localhost:8000) 未启动
2. 爬虫登录状态过期
3. 网络连接问题

**解决方案:**

```bash
# 检查后端服务
curl http://localhost:8000/health

# 重新登录爬虫平台
# 参考 MediaCrawler 文档

# 查看 MCP 服务日志
python -m opinion_mcp.server --debug
```

### Q3: 小红书发布失败

**可能原因:**
1. 小红书 MCP 服务未启动
2. 小红书登录状态过期

**解决方案:**

```bash
# 检查小红书 MCP 服务
curl http://localhost:18060/mcp

# 重新登录小红书
./xiaohongshu-login-darwin-arm64

# 参考 docs/XHS_SETUP.md
```

### Q4: Webhook 推送收不到

**检查项:**
1. 确认 `callback_url` 可访问
2. 确认在 `analyze_topic` 之后调用了 `register_webhook`
3. 检查防火墙设置

**调试方法:**

```bash
# 使用 ngrok 暴露本地端口测试
ngrok http 3000

# 使用 webhook.site 测试
# 访问 https://webhook.site 获取测试 URL
```

### Q5: 如何查看所有可用工具？

```bash
# 方式 1: 调用 MCP 端点
curl http://localhost:18061/mcp/tools

# 方式 2: 查看健康检查
curl http://localhost:18061/health
```

### Q6: 分析结果中没有图片

**可能原因:**
1. `image_count` 设置为 0
2. 火山引擎 API 配置错误
3. 图片生成超时

**解决方案:**

```bash
# 检查环境变量
echo $VOLC_ACCESS_KEY
echo $VOLC_SECRET_KEY

# 确认 image_count > 0
{
  "topic": "测试话题",
  "image_count": 2
}
```

### Q7: 如何同时运行多个分析任务？

当前版本**不支持**同时运行多个分析任务。如果已有任务在运行，`analyze_topic` 会返回错误：

```json
{
  "success": false,
  "error": "已有分析任务在运行",
  "current_job_id": "job_20260128_143052_abc123"
}
```

请等待当前任务完成后再启动新任务。

### Q8: 环境变量配置

Opinion MCP Server 支持以下环境变量：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OPINION_BACKEND_URL` | `http://localhost:8000` | 后端服务地址 |
| `OPINION_MCP_PORT` | `18061` | MCP 服务端口 |
| `OPINION_MCP_HOST` | `localhost` | MCP 服务主机 |
| `OPINION_REQUEST_TIMEOUT` | `300` | 请求超时（秒） |
| `OPINION_WEBHOOK_RETRY_COUNT` | `3` | Webhook 重试次数 |

---

## API 端点汇总

### MCP 协议端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/mcp` | GET | 服务信息 |
| `/mcp/initialize` | POST | 初始化 |
| `/mcp/tools` | GET | 工具列表 |
| `/mcp/tools/list` | POST | 工具列表 (MCP 标准) |
| `/mcp/tools/call` | POST | 调用工具 |

### 直接 API 端点 (便于测试)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/analyze` | POST | 启动分析 |
| `/api/status` | GET | 查询状态 |
| `/api/status/{job_id}` | GET | 查询指定任务状态 |
| `/api/result` | GET | 获取结果 |
| `/api/result/{job_id}` | GET | 获取指定任务结果 |
| `/api/hotnews` | GET | 获取热榜 |
| `/api/settings` | GET | 获取设置 |

---

## 相关文档

- [小红书 MCP 服务安装指南](./XHS_SETUP.md)
- [API 使用指南](../src/API_USAGE.md)
- [项目 README](../README.md)

---

**最后更新**: 2026-01-28  
**维护者**: GlobalInSight 开发团队
