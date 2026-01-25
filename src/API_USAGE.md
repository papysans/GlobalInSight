# 前端 API 使用说明

## 新增功能

### 1. API 服务 (`src/api/index.js`)
统一管理所有后端接口调用，包括：
- `analyze()` - 执行工作流分析
- `getConfig()` - 获取配置
- `updateConfig()` - 更新配置
- `getUserSettings()` - 获取用户设置
- `updateUserSettings()` - 更新用户设置
- `getModels()` - 获取所有提供商的模型列表
- `validateModel()` - 验证提供商-模型组合
- `getOutputFiles()` - 获取历史文件列表
- `getOutputFile()` - 获取文件内容
- `getWorkflowStatus()` - 获取工作流状态

### 2. Store 管理

#### `src/stores/config.js` - 配置管理
- `fetchConfig()` - 获取配置
- `updateConfig()` - 更新配置
- `getUserApis` - 获取用户配置的 API 列表
- `saveUserApis()` - 保存用户 API 配置
- `fetchModels()` - 获取模型列表（带缓存）
- `getModelsForProvider()` - 获取指定提供商的模型
- `getDefaultModel()` - 获取提供商的默认模型
- Getters: `llmProviders`, `crawlerLimits`, `debateMaxRounds`, `defaultPlatforms`

#### `src/stores/outputs.js` - 输出文件管理
- `fetchFiles()` - 获取文件列表
- `fetchFileContent()` - 获取文件内容
- `clearCurrentFile()` - 清除当前文件

#### `src/stores/workflow.js` - 工作流状态管理
- `fetchStatus()` - 获取状态
- `startPolling()` - 开始轮询
- `stopPolling()` - 停止轮询

#### `src/stores/analysis.js` - 分析工作流
- `selectedPlatforms` - 选中的平台
- `setSelectedPlatforms()` - 设置选中的平台
- `availablePlatforms` getter - 可用平台列表

### 3. 新增组件

#### `ConfigPanel.vue` - 配置面板
- 显示和编辑配置
- 支持更新辩论轮数、默认平台、爬虫限制

#### `OutputFiles.vue` - 历史文件列表
- 显示所有历史输出文件
- 支持分页浏览
- 点击文件可加载内容

#### `WorkflowStatus.vue` - 工作流状态
- 实时显示工作流执行状态
- 显示进度条和当前步骤
- 自动轮询更新

#### `NewsInput.vue` - 输入组件
- 平台选择功能
- 支持多选平台
- 选中的平台会传递给后端

## 用户设置 API

### 数据结构

#### LLM API 配置
```javascript
{
  id: 1234567890,           // 唯一标识
  provider: "Deepseek",     // 显示名称
  providerKey: "deepseek",  // 提供商标识
  model: "deepseek-chat",   // 模型 ID（可选，空则使用默认）
  key: "sk-xxx",            // API Key
  active: true              // 是否激活
}
```

#### Agent 绑定配置（新格式）
```javascript
{
  reporter: {
    provider: "deepseek",   // 提供商标识
    model: "deepseek-chat", // 模型 ID
    apiId: 1234567890       // 关联的 API 配置 ID
  },
  analyst: {
    provider: "gemini",
    model: "gemini-3-flash-preview",
    apiId: 9876543210
  }
}
```

**注意**：Agent 绑定只能选择已在"API 接口配置"中添加的 API。

### API 端点

#### `GET /api/user-settings`
获取用户设置

**响应**：
```json
{
  "llm_apis": [...],
  "volcengine": {...},
  "agent_llm_overrides": {...}
}
```

#### `PUT /api/user-settings`
更新用户设置（部分更新）

**请求体**：
```json
{
  "llm_apis": [...],           // 可选
  "volcengine": {...},         // 可选
  "agent_llm_overrides": {...} // 可选
}
```

#### `GET /api/models`
获取所有提供商的模型列表

**响应**：
```json
{
  "deepseek": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "description": "平衡的对话模型",
      "type": "chat",
      "is_default": true
    }
  ],
  "gemini": [...]
}
```

#### `POST /api/validate-model`
验证提供商-模型组合

**请求体**：
```json
{
  "provider": "deepseek",
  "model": "deepseek-chat"
}
```

**响应**：
```json
{
  "valid": true,
  "message": "模型有效"
}
```

## 使用示例

### 配置 API Key 和模型

```javascript
import { api } from '../api';
import { useConfigStore } from '../stores/config';

const configStore = useConfigStore();

// 1. 获取模型列表
await configStore.fetchModels();

// 2. 获取某个提供商的模型
const deepseekModels = configStore.getModelsForProvider('deepseek');

// 3. 获取默认模型
const defaultModel = configStore.getDefaultModel('deepseek');

// 4. 保存 API 配置
const newApi = {
  id: Date.now(),
  provider: 'Deepseek',
  providerKey: 'deepseek',
  model: 'deepseek-chat',
  key: 'sk-xxx',
  active: true
};

configStore.saveUserApis([...configStore.getUserApis, newApi]);

// 5. 同步到后端
await api.updateUserSettings({
  llm_apis: configStore.getUserApis
});
```

### 配置 Agent 绑定

```javascript
// 1. 获取已配置的 API 列表
const userApis = configStore.getUserApis;

// 2. 为 Agent 选择 API
const agentOverrides = {
  reporter: {
    provider: userApis[0].providerKey,
    model: userApis[0].model,
    apiId: userApis[0].id
  }
};

// 3. 保存到后端
await api.updateUserSettings({
  agent_llm_overrides: agentOverrides
});
```

### 在组件中使用

```javascript
import { api } from '../api';

// 获取配置
const config = await api.getConfig();

// 更新配置
await api.updateConfig({
  debate_max_rounds: 6,
  default_platforms: ['wb', 'xhs']
});

// 获取历史文件
const files = await api.getOutputFiles(20, 0);

// 获取工作流状态
const status = await api.getWorkflowStatus();
```

## 界面布局

新的界面布局：
```
┌─────────────────────────────────────────────┐
│  主工作区（3列）                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ NewsInput │ │Thinking  │ │Xiaohongshu│  │
│  │           │ │Chain     │ │Card      │   │
│  └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  管理和状态区（3列）                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │Workflow │ │Config    │ │Output    │   │
│  │Status   │ │Panel     │ │Files     │   │
│  └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────┘
```

## 设置页面功能

### API 接口配置
- 添加/编辑/删除 API Key
- 选择提供商和模型
- 支持多个同提供商配置（通过 Key 尾号区分）

### Agent 模型绑定
- 为每个 Agent 选择已配置的 API
- 显示格式：`提供商 - 模型名称 (...Key尾号)`
- 未选择则使用后端默认配置

### 向后兼容
- 自动迁移旧格式配置（model: null → 默认模型）
- 支持新旧格式的 agent_llm_overrides

## 平台选择功能

在 `NewsInput` 组件中：
- 用户可以通过勾选框选择要爬取的平台
- 如果未选择任何平台，将使用配置中的默认平台
- 选中的平台会通过 `platforms` 字段传递给后端

支持的平台代码：
- `wb` - 微博
- `bili` - B站
- `xhs` - 小红书
- `dy` - 抖音
- `ks` - 快手
- `tieba` - 贴吧
- `zhihu` - 知乎
