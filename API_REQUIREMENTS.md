# 观潮 GrandChart V22 - 后端接口需求文档

## 概述

本文档描述了基于多智能体协作的新闻舆情分析系统所需的后端接口规范。系统支持多平台数据爬取、智能体辩论、舆情洞察分析和爆款文案生成。

---

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **CORS**: 支持跨域请求

---

## 1. 舆情分析工作流接口

### 1.1 启动完整分析流程

**接口**: `POST /api/analyze`

**功能**: 执行完整的工作流（数据爬取 → 智能体辩论 → 洞察分析 → 文案生成）

**请求体**:
```json
{
  "topic": "议题主题（必填）",
  "urls": ["可选URL列表"],
  "platforms": ["wb", "bili", "xhs"],  // 可选：指定平台
  "debate_rounds": 2  // 可选：辩论轮数，默认2，范围1-5
}
```

**响应格式**: SSE (Server-Sent Events) 流式输出

**SSE 事件格式**:
```
data: {"agent_name": "Moderator", "step_content": "...", "status": "thinking", "model": "deepseek-chat"}
data: {"agent_name": "Pro", "step_content": "...", "status": "thinking", "model": "deepseek-chat"}
data: {"agent_name": "Con", "step_content": "...", "status": "thinking", "model": "deepseek-chat"}
data: {"agent_name": "Analyst", "step_content": "INSIGHT: ...\nTITLE: ...\nSUB: ...", "status": "thinking", "model": "deepseek-chat"}
data: {"agent_name": "Writer", "step_content": "TITLE: ...\nCONTENT: ...", "status": "thinking", "model": "deepseek-chat"}
data: {"agent_name": "System", "step_content": "Analysis Complete", "status": "finished"}
```

**字段说明**:
- `agent_name`: 智能体名称（Moderator, Pro, Con, Analyst, Writer, System）
- `step_content`: 步骤内容（支持Markdown格式）
- `status`: 状态（thinking, finished, error）
- `model`: 使用的模型名称（可选）

**特殊格式要求**:

1. **Analyst 输出格式**（必须包含以下标记）:
   ```
   INSIGHT: [100字左右的深度洞察]
   TITLE: [4-8字的吸睛主标题]
   SUB: [8-12字的补充副标题]
   ```

2. **Writer 输出格式**（必须包含以下标记）:
   ```
   TITLE: [小红书风格标题，可带Emoji]
   CONTENT: [正文内容，分段，口语化，文末加Tags]
   ```

**错误响应**:
```json
{
  "agent_name": "System",
  "step_content": "Error: 错误信息",
  "status": "error"
}
```

---

## 2. 数据生成接口

### 2.1 生成舆论对比数据

**接口**: `POST /api/generate-data/contrast`

**功能**: 基于分析结果生成"中外舆论温差"数据

**请求体**:
```json
{
  "topic": "议题主题",
  "insight": "核心洞察内容"
}
```

**响应**:
```json
{
  "domestic": [65, 20, 15],  // [支持%, 中立%, 反对%]
  "intl": [30, 40, 30]       // [支持%, 中立%, 反对%]
}
```

**说明**: 三个数值之和应约等于100

---

### 2.2 生成情感光谱数据

**接口**: `POST /api/generate-data/sentiment`

**功能**: 生成网民情感分布数据

**请求体**:
```json
{
  "topic": "议题主题",
  "insight": "核心洞察内容"
}
```

**响应**:
```json
{
  "emotions": [
    {"name": "愤怒", "value": 55},
    {"name": "嘲讽", "value": 25},
    {"name": "失望", "value": 12},
    {"name": "中立", "value": 8}
  ]
}
```

---

### 2.3 生成关键词数据

**接口**: `POST /api/generate-data/keywords`

**功能**: 生成高频关键词数据

**请求体**:
```json
{
  "topic": "议题主题",
  "crawler_data": []  // 可选：爬取的数据
}
```

**响应**:
```json
{
  "keywords": [
    {"word": "真相", "frequency": 1200},
    {"word": "反转", "frequency": 950},
    {"word": "烂尾", "frequency": 800},
    {"word": "公信力", "frequency": 600},
    {"word": "甚至", "frequency": 500}
  ]
}
```

---

## 3. 配置管理接口

### 3.1 获取配置

**接口**: `GET /api/config`

**响应**:
```json
{
  "llm_providers": {
    "reporter": [
      {"provider": "deepseek", "model": "deepseek-chat"},
      {"provider": "moonshot", "model": "kimi-k2-turbo-preview"}
    ],
    "analyst": [...],
    "debater": [...],
    "writer": [...]
  },
  "crawler_limits": {
    "wb": {"max_items": 5, "max_comments": 10},
    "bili": {"max_items": 5, "max_comments": 10},
    "xhs": {"max_items": 5, "max_comments": 10},
    "dy": {"max_items": 5, "max_comments": 10},
    "ks": {"max_items": 5, "max_comments": 10},
    "tieba": {"max_items": 5, "max_comments": 10},
    "zhihu": {"max_items": 5, "max_comments": 10}
  },
  "debate_max_rounds": 4,
  "default_platforms": ["wb", "bili"]
}
```

---

### 3.2 更新配置

**接口**: `PUT /api/config`

**请求体**:
```json
{
  "debate_max_rounds": 6,  // 可选
  "crawler_limits": {      // 可选
    "wb": {"max_items": 10, "max_comments": 20}
  },
  "default_platforms": ["wb", "xhs"]  // 可选
}
```

**响应**:
```json
{
  "success": true,
  "message": "配置已更新: debate_max_rounds, crawler_limits.wb",
  "updated_fields": ["debate_max_rounds", "crawler_limits.wb"]
}
```

---

## 4. 工作流状态接口

### 4.1 获取工作流状态

**接口**: `GET /api/workflow/status`

**响应（无运行任务）**:
```json
{
  "running": false,
  "current_step": null,
  "progress": 0,
  "started_at": null,
  "topic": null
}
```

**响应（有运行任务）**:
```json
{
  "running": true,
  "current_step": "analyst",
  "progress": 50,
  "started_at": "2025-12-30T20:00:00",
  "topic": "武汉大学图书馆"
}
```

**进度说明**:
- `crawler_agent`: 10%
- `reporter`: 30%
- `analyst`: 50%
- `debater`: 70%
- `writer`: 90%
- `finished`: 100%

---

## 5. 历史输出文件接口

### 5.1 获取文件列表

**接口**: `GET /api/outputs`

**查询参数**:
- `limit`: 返回数量限制（默认20）
- `offset`: 偏移量（默认0）

**响应**:
```json
{
  "files": [
    {
      "filename": "2025-12-30_17-57-36_武汉大学图书馆.md",
      "topic": "武汉大学图书馆",
      "created_at": "2025-12-30T17:57:36",
      "size": 12345
    }
  ],
  "total": 50
}
```

---

### 5.2 获取文件内容

**接口**: `GET /api/outputs/{filename}`

**路径参数**:
- `filename`: 文件名（如：`2025-12-30_17-57-36_武汉大学图书馆.md`）

**响应**:
```json
{
  "filename": "2025-12-30_17-57-36_武汉大学图书馆.md",
  "content": "# 武汉大学图书馆\n\n## 最终文案\n\n...",
  "created_at": "2025-12-30T17:57:36"
}
```

**错误响应**:
- `404`: 文件不存在
- `400`: 无效的文件名（包含路径遍历字符）

---

## 6. 前端API配置管理（本地存储）

**说明**: 前端API配置存储在浏览器 `localStorage` 中，键名为 `grandchart_user_apis_v2`

**数据结构**:
```json
[
  {
    "id": 1234567890,
    "provider": "Deepseek",
    "providerKey": "deepseek",
    "url": "https://api.deepseek.com",
    "key": "sk-...",
    "model": "deepseek-chat",
    "active": true
  }
]
```

**支持的厂商**:
- `deepseek`: Deepseek (深度求索)
- `gemini`: Gemini (Google)
- `doubao`: Doubao (字节豆包)
- `kimi`: Kimi (月之暗面)
- `zhipu`: Zhipu AI (智谱清言)
- `qwen`: Qwen (通义千问)
- `custom`: 自定义 / OpenAI Compatible

**默认Base URL映射**:
```javascript
{
  "deepseek": "https://api.deepseek.com",
  "gemini": "https://generativelanguage.googleapis.com/v1beta/models",
  "doubao": "https://ark.cn-beijing.volces.com/api/v3",
  "kimi": "https://api.moonshot.cn/v1",
  "zhipu": "https://open.bigmodel.cn/api/paas/v4",
  "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "custom": ""
}
```

---

## 7. 智能体工作流规范

### 7.1 工作流阶段

1. **Moderator（主持人）**
   - 启动议题扫描
   - 指出舆论场可能存在的2个主要矛盾点

2. **Debater（辩论者）**
   - 正方（Pro）：提出核心立场，反驳对方观点
   - 反方（Con）：指出逻辑漏洞，反驳正方观点
   - 轮数：根据 `debate_rounds` 参数执行（1-5轮）

3. **Analyst（分析师）**
   - 事实核查：指出逻辑谬误或情绪煽动
   - 深度洞察：分析事件背后的社会焦虑、群体心理或结构性矛盾
   - 数据海报文案：生成图表标题和副标题
   - **输出格式必须包含**: `INSIGHT:`, `TITLE:`, `SUB:`

4. **Writer（文案生成）**
   - 基于洞察生成小红书风格爆款文案
   - 标题带Emoji
   - 正文分段、口语化
   - 文末加Tags
   - **输出格式必须包含**: `TITLE:`, `CONTENT:`

---

## 8. 错误处理

### 8.1 HTTP状态码

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 8.2 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 8.3 SSE错误事件

```json
{
  "agent_name": "System",
  "step_content": "Error: 具体错误信息",
  "status": "error"
}
```

---

## 9. 接口使用示例

### 9.1 前端调用示例（JavaScript）

```javascript
// 1. 启动分析（支持辩论轮数）
const eventSource = new EventSource(
  'http://localhost:8000/api/analyze?' + 
  new URLSearchParams({
    topic: '测试主题',
    debate_rounds: 2,
    platforms: JSON.stringify(['wb', 'bili'])
  })
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.agent_name, data.step_content);
  
  // 处理Analyst输出
  if (data.agent_name === 'Analyst') {
    const insight = parseInsight(data.step_content);
    // insight.insight, insight.title, insight.subtitle
  }
  
  // 处理Writer输出
  if (data.agent_name === 'Writer') {
    const copy = parseCopy(data.step_content);
    // copy.title, copy.content
  }
};

// 2. 生成数据
const contrastData = await fetch('http://localhost:8000/api/generate-data/contrast', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: '测试主题',
    insight: '核心洞察内容'
  })
}).then(r => r.json());

// 3. 获取工作流状态
const status = await fetch('http://localhost:8000/api/workflow/status')
  .then(r => r.json());
```

---

## 10. 注意事项

1. **辩论轮数**: `debate_rounds` 参数范围1-5，建议默认2轮
2. **输出格式**: Analyst和Writer的输出必须严格按照指定格式，便于前端解析
3. **流式传输**: `/api/analyze` 接口必须使用SSE格式，支持实时更新
4. **数据生成**: 数据生成接口应在分析完成后调用，确保数据一致性
5. **配置持久化**: 配置更新目前是内存中的，如需持久化需要额外实现
6. **文件安全**: 文件接口已做路径遍历攻击防护
7. **平台支持**: 支持的平台包括：wb(微博), bili(B站), xhs(小红书), dy(抖音), ks(快手), tieba(贴吧), zhihu(知乎)

---

## 11. 待实现功能（可选）

1. **WebSocket支持**: 替代SSE实现双向通信
2. **配置持久化**: 将配置保存到数据库或配置文件
3. **用户认证**: 支持多用户配置管理
4. **API限流**: 防止接口滥用
5. **缓存机制**: 缓存分析结果，避免重复计算
6. **批量分析**: 支持批量处理多个议题

---

## 更新日志

- **2025-12-31**: 初始版本，包含基础工作流、配置管理、数据生成接口规范