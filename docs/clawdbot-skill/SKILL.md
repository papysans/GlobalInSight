---
name: opinion-analyzer
description: 舆论分析助手 - 分析多平台热点话题、生成小红书风格文案和配图、一键发布到小红书。当用户提到"分析话题"、"舆情分析"、"热榜"、"小红书发布"、"舆论"、"热点"时使用此技能。
homepage: https://github.com/user/GlobalInSight
metadata: { "clawdbot": { "emoji": "🔍", "os": ["darwin", "linux", "win32"] } }
---

# 🔍 Opinion Analyzer - 舆论分析助手

GlobalInSight 舆论分析系统。通过 REST API 调用本地服务，提供多平台舆情分析、热榜获取、AI 配图生成和小红书发布功能。

## 功能概述

- **多平台舆情分析**: 爬取微博、抖音、快手、B站、知乎、贴吧、小红书、Hacker News、Reddit
- **AI 深度解读**: LLM 多轮辩论分析，生成核心观点和深度洞察
- **小红书文案生成**: 自动生成标题、正文、标签
- **AI 配图生成**: 火山引擎生成高质量配图
- **一键发布**: 直接发布到小红书

## 前置条件

使用前确保服务已启动：

```bash
cd /Users/napstablook/Projects/GlobalInSight
./start.sh                        # 后端 API (端口 8000)
./scripts/start-opinion-mcp.sh    # Opinion MCP (端口 18061)
./scripts/start-xhs-mcp.sh        # 小红书发布 (端口 18060，可选)
```

检查服务状态：
```bash
curl http://localhost:8000/api/health
curl http://localhost:18061/health
```

## API 调用方式

⚠️ **重要**: 使用 REST API 直接调用，不使用 MCP 工具。

### 基础 URL
```
http://localhost:18061
```

### 1. 启动分析任务

```bash
curl -X POST http://localhost:18061/analyze_topic \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "话题内容",
    "platforms": ["wb", "zhihu", "bili"],
    "debate_rounds": 2,
    "image_count": 2
  }'
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | ✅ | - | 要分析的话题 |
| platforms | string[] | ❌ | ["wb", "dy", "ks", "bili"] | 平台代码列表 |
| debate_rounds | int | ❌ | 2 | 辩论轮数 (1-5) |
| image_count | int | ❌ | 2 | 配图数量 (0-9) |

**返回**:
```json
{
  "success": true,
  "job_id": "job_20260128_xxx",
  "message": "分析任务已启动"
}
```

### 2. 查询任务状态

```bash
curl http://localhost:18061/get_analysis_status/job_xxx
# 或
curl -X POST http://localhost:18061/get_analysis_status \
  -H "Content-Type: application/json" \
  -d '{"job_id": "job_xxx"}'
```

**返回**:
```json
{
  "success": true,
  "status": "running",
  "progress": 45,
  "current_step": "爬取微博数据..."
}
```

状态值: `pending` → `running` → `completed` / `failed`

### 3. 获取分析结果

```bash
curl http://localhost:18061/get_analysis_result/job_xxx
```

**返回内容**:
- `copywriting`: 小红书文案 (title, subtitle, content, tags)
- `ai_images`: AI 配图 URL 列表
- `summary`: 核心观点摘要
- `insight`: 深度洞察

### 4. 获取热榜

```bash
curl -X POST http://localhost:18061/get_hot_news \
  -H "Content-Type: application/json" \
  -d '{"limit": 20, "include_hn": true}'
```

### 5. 修改文案

```bash
curl -X POST http://localhost:18061/update_copywriting \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job_xxx",
    "title": "新标题",
    "content": "新内容"
  }'
```

### 6. 发布到小红书

```bash
curl -X POST http://localhost:18061/publish_to_xhs \
  -H "Content-Type: application/json" \
  -d '{"job_id": "job_xxx"}'
```

### 7. 获取配置

```bash
curl http://localhost:18061/get_settings
```

## 平台代码对照表

⚠️ **必须使用英文代码，不能用中文！**

| 代码 | 平台 |
|------|------|
| wb | 微博 |
| dy | 抖音 |
| ks | 快手 |
| bili | B站 |
| tieba | 贴吧 |
| zhihu | 知乎 |
| xhs | 小红书 |
| hn | Hacker News |
| reddit | Reddit |

✅ 正确: `["wb", "dy", "bili"]`  
❌ 错误: `["微博", "抖音"]`

## 推荐工作流程

### 分析话题
```
1. 调用 /analyze_topic 启动分析 → 获取 job_id
2. 每 60 秒调用 /get_analysis_status/{job_id} 查询进度
3. status="completed" 后调用 /get_analysis_result/{job_id}
4. 展示结果给用户
```

### 发现热点
```
1. 调用 /get_hot_news 获取热榜
2. 展示给用户选择
3. 用户选择后调用 /analyze_topic 分析
```

### 发布流程
```
1. 分析完成后展示文案
2. 用户确认或修改 (调用 /update_copywriting)
3. 调用 /publish_to_xhs 发布
```

## 使用示例

### 示例 1: 分析话题
```
用户: 分析一下 "DeepSeek R1 开源"

助手执行:
1. curl -X POST http://localhost:18061/analyze_topic \
     -H "Content-Type: application/json" \
     -d '{"topic": "DeepSeek R1 开源", "platforms": ["wb", "zhihu", "hn"]}'
   
   返回: {"success": true, "job_id": "job_20260128_xxx"}

2. 等待 60 秒后查询:
   curl http://localhost:18061/get_analysis_status/job_20260128_xxx
   
   返回: {"status": "running", "progress": 35}

3. 完成后获取结果:
   curl http://localhost:18061/get_analysis_result/job_20260128_xxx
```

### 示例 2: 查看热榜
```
用户: 今天有什么热点？

助手执行:
curl -X POST http://localhost:18061/get_hot_news \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

### 示例 3: 发布到小红书
```
用户: 把分析结果发到小红书

助手执行:
curl -X POST http://localhost:18061/publish_to_xhs \
  -H "Content-Type: application/json" \
  -d '{"job_id": "job_20260128_xxx"}'
```

## 注意事项

- 分析任务需要 10-20 分钟
- 同一时间只能运行一个分析任务
- 相同话题 60 秒内不能重复提交
- 发布需要 XHS MCP 服务运行且已登录
- 首次使用各平台可能需要扫码登录

## 错误处理

| 错误 | 解决方案 |
|------|---------|
| "已有任务在运行" | 等待当前任务完成 |
| "任务不存在" | 检查 job_id 或留空查询最近任务 |
| "后端服务不可用" | 运行 `./start.sh` |
| "Connection refused" | 检查服务是否启动 |

## 服务端点

| 服务 | 端口 | 检查命令 |
|------|------|---------|
| 后端 API | 8000 | `curl http://localhost:8000/api/health` |
| Opinion MCP | 18061 | `curl http://localhost:18061/health` |
| XHS MCP | 18060 | `curl http://localhost:18060/mcp` |
