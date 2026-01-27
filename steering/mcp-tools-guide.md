---
inclusion: always
---

# MCP 工具完整使用指南

> 📅 创建日期: 2026-01-23  
> 🎯 目标: 为 Kiro AI 提供完整的 MCP 工具使用指南  
> 📌 类型: Always-included Steering

---

## 🔧 已配置的 MCP 工具概览

### 1. GitHub MCP ✅
**功能**: GitHub 仓库操作、代码搜索、Issues、PR 管理  
**状态**: 已启用  
**自动批准**: `search_code`, `get_file_contents`

### 2. Context7 MCP ✅
**功能**: 获取最新的技术文档和代码示例  
**状态**: 已启用  
**自动批准**: `resolve-library-id`, `query-docs`

### 3. Firecrawl MCP ✅
**功能**: 网页抓取和内容提取  
**状态**: 已启用  
**自动批准**: 无

---

## 📋 工具使用场景矩阵

| 用户需求 | 使用工具 | 触发关键词 | 优先级 |
|---------|---------|-----------|--------|
| 查看 GitHub 代码 | GitHub MCP | "GitHub", "仓库", "代码" | 高 |
| 搜索代码片段 | GitHub MCP | "搜索", "查找代码" | 高 |
| 技术文档查询 | Context7 | "怎么用", "文档", "API" | 高 |
| 代码示例 | Context7 | "示例", "example" | 高 |
| 网页内容抓取 | Firecrawl | "抓取", "爬取", "网页" | 中 |
| 最新版本信息 | Context7 | "最新", "版本" | 高 |

---

## 🎯 GitHub MCP 详细使用指南

### 核心功能

#### 1. 代码搜索 (search_code)
**使用场景**:
- 在 GitHub 上搜索特定代码片段
- 查找某个函数或类的实现
- 研究开源项目的实现方式

**触发条件**:
- 用户提到 "搜索 GitHub 代码"
- 需要查找某个技术的实现示例
- 研究开源项目

**使用示例**:
```
用户: "在 GitHub 上搜索 FastAPI JWT 认证的实现"
→ 调用 mcp_github_search_code
→ query: "FastAPI JWT authentication language:python"
```

**最佳实践**:
- 使用精确的搜索关键词
- 添加语言过滤器 (language:python)
- 添加组织过滤器 (org:fastapi)
- 限制结果数量 (perPage: 10)

#### 2. 获取文件内容 (get_file_contents)
**使用场景**:
- 查看 GitHub 仓库中的特定文件
- 读取配置文件
- 查看示例代码

**触发条件**:
- 用户提供 GitHub 文件链接
- 需要查看某个仓库的文件
- 研究项目结构

**使用示例**:
```
用户: "查看 fastapi/fastapi 仓库的 main.py"
→ 调用 mcp_github_get_file_contents
→ owner: "fastapi", repo: "fastapi", path: "main.py"
```

#### 3. 其他可用功能
- `list_issues` - 列出 Issues
- `list_pull_requests` - 列出 PR
- `create_pull_request` - 创建 PR
- `get_commit` - 获取提交详情
- `list_branches` - 列出分支
- `search_repositories` - 搜索仓库

### 使用限制
- 需要有效的 GitHub Token
- 遵守 GitHub API 速率限制
- 私有仓库需要相应权限

---

## 🎯 Context7 MCP 详细使用指南

### 核心功能

#### 1. 解析库 ID (resolve-library-id)
**使用场景**:
- 查找技术库的 Context7 ID
- 确认库是否在 Context7 中可用

**触发条件**:
- 用户询问某个技术库的使用方法
- 需要获取最新文档前

**使用示例**:
```
用户: "FastAPI 如何实现 JWT 认证？"
→ 步骤 1: 调用 mcp_context7_resolve_library_id
→ libraryName: "FastAPI"
→ query: "FastAPI JWT authentication"
→ 获取 libraryId: "/tiangolo/fastapi"
```

**最佳实践**:
- 使用准确的库名称
- 提供用户的原始问题作为 query
- 最多调用 3 次
- 选择最相关的结果

#### 2. 查询文档 (query-docs)
**使用场景**:
- 获取最新的 API 文档
- 查找代码示例
- 了解最佳实践

**触发条件**:
- 用户询问技术问题
- 需要代码示例
- 需要最新版本信息

**使用示例**:
```
用户: "FastAPI 如何实现 JWT 认证？"
→ 步骤 2: 调用 mcp_context7_query_docs
→ libraryId: "/tiangolo/fastapi"
→ query: "JWT authentication implementation"
→ 获取最新文档和示例
```

**最佳实践**:
- 先调用 resolve-library-id 获取 libraryId
- 使用具体的查询问题
- 最多调用 3 次
- 不要在 query 中包含敏感信息

### 支持的技术栈

#### 后端框架
- FastAPI (`/tiangolo/fastapi`)
- Django (`/django/django`)
- Flask (`/pallets/flask`)
- SQLAlchemy (`/sqlalchemy/sqlalchemy`)

#### 前端框架
- Next.js (`/vercel/next.js`)
- React (`/facebook/react`)
- Vue (`/vuejs/vue`)
- Tailwind CSS (`/tailwindlabs/tailwindcss`)

#### 云服务和 IaC
- Terraform (`/hashicorp/terraform`)
- Docker (`/docker/docker`)
- Kubernetes (`/kubernetes/kubernetes`)

#### AI/ML 框架
- LangChain (`/langchain-ai/langchain`)
- LangGraph (`/langchain-ai/langgraph`)
- OpenAI (`/openai/openai-python`)

### 使用限制
- 每次查询最多 3 次调用
- 不要包含敏感信息
- 优先使用官方库

---

## 🎯 Firecrawl MCP 详细使用指南

### 核心功能

#### 1. 网页抓取
**使用场景**:
- 抓取网页内容
- 提取结构化数据
- 获取网页截图

**触发条件**:
- 用户需要抓取网页
- 需要提取网页数据
- 用户提到 "抓取"、"爬取"

**使用示例**:
```
用户: "抓取这个网页的内容: https://example.com"
→ 调用 Firecrawl MCP 工具
→ 提取网页内容
```

**最佳实践**:
- 确保 URL 有效
- 遵守网站的 robots.txt
- 注意隐私和版权
- 处理可能的错误

### 使用限制
- 需要有效的 Firecrawl API Key
- 遵守目标网站的使用条款
- 注意 API 调用配额

---

## 🚀 自动触发规则

### 规则 1: 技术问题优先使用 Context7
**触发条件**:
- 用户询问 "如何..."、"怎么..."
- 提到技术库名称 (FastAPI, Next.js, React 等)
- 需要代码示例
- 询问最新版本

**行为**:
1. 自动调用 `mcp_context7_resolve_library_id`
2. 自动调用 `mcp_context7_query_docs`
3. 基于最新文档回答问题

**示例**:
```
用户: "Next.js 14 如何使用 Server Actions？"
→ 自动使用 Context7 获取 Next.js 14 最新文档
→ 不需要用户明确说 "use context7"
```

### 规则 2: GitHub 操作自动使用 GitHub MCP
**触发条件**:
- 用户提到 "GitHub"
- 需要搜索代码
- 需要查看仓库文件
- 提到 "开源项目"

**行为**:
1. 自动调用相应的 GitHub MCP 工具
2. 展示搜索结果或文件内容

**示例**:
```
用户: "搜索 GitHub 上 FastAPI 的 JWT 实现"
→ 自动使用 mcp_github_search_code
```

### 规则 3: 网页抓取使用 Firecrawl
**触发条件**:
- 用户提供网页 URL
- 提到 "抓取"、"爬取"
- 需要提取网页内容

**行为**:
1. 自动调用 Firecrawl MCP
2. 提取并展示内容

---

## 🎯 项目特定使用场景

### 场景 A: 后端开发 (FastAPI + Python)

#### 1. 实现新的 API 路由
```
用户: "创建一个获取对话历史的 API"

Kiro 行为:
1. 调用 Context7 查询 FastAPI 路由定义
   → libraryId: "/tiangolo/fastapi"
   → query: "API route definition with path parameters"
2. 调用 Context7 查询 SQLAlchemy 查询
   → libraryId: "/sqlalchemy/sqlalchemy"
   → query: "query with filters and pagination"
3. 生成代码并解释
```

#### 2. 实现 LLM Agent
```
用户: "如何使用 LangGraph 实现条件分支？"

Kiro 行为:
1. 调用 Context7 查询 LangGraph 文档
   → libraryId: "/langchain-ai/langgraph"
   → query: "conditional branching in graph"
2. 获取最新示例代码
3. 结合项目实际情况给出建议
```

### 场景 B: 前端开发 (Next.js + React)

#### 1. 创建 UI 组件
```
用户: "创建一个聊天消息组件"

Kiro 行为:
1. 调用 Context7 查询 React 组件最佳实践
   → libraryId: "/facebook/react"
   → query: "chat message component with hooks"
2. 调用 Context7 查询 Tailwind CSS 样式
   → libraryId: "/tailwindlabs/tailwindcss"
   → query: "chat bubble styling"
3. 生成组件代码
```

#### 2. 实现路由和布局
```
用户: "如何在 Next.js 14 中使用 App Router？"

Kiro 行为:
1. 调用 Context7 查询 Next.js 14 文档
   → libraryId: "/vercel/next.js"
   → query: "App Router layout and routing"
2. 获取最新用法和示例
3. 提供实现建议
```

### 场景 C: Terraform 配置

#### 1. 配置云资源
```
用户: "如何配置阿里云 ECS 实例？"

Kiro 行为:
1. 调用 Context7 查询 Terraform 文档
   → libraryId: "/hashicorp/terraform"
   → query: "Alibaba Cloud ECS instance configuration"
2. 搜索 GitHub 上的示例
   → mcp_github_search_code
   → query: "alicloud_instance terraform"
3. 综合提供配置方案
```

### 场景 D: 研究开源项目

#### 1. 学习项目架构
```
用户: "研究 FastAPI 的中间件实现"

Kiro 行为:
1. 搜索 FastAPI 仓库
   → mcp_github_search_code
   → query: "middleware implementation repo:tiangolo/fastapi"
2. 获取相关文件
   → mcp_github_get_file_contents
3. 分析并解释实现
```

---

## ⚠️ 使用注意事项

### 1. Context7 使用限制
- ✅ 每次查询最多 3 次调用
- ✅ 如果 3 次后还没找到，使用现有信息
- ✅ 不要在 query 中包含敏感信息
- ✅ 优先使用官方库的文档

### 2. GitHub MCP 使用限制
- ✅ 遵守 GitHub API 速率限制
- ✅ 敏感操作前询问用户确认
- ✅ 私有仓库需要相应权限
- ✅ 不要泄露 Token

### 3. Firecrawl 使用限制
- ✅ 遵守目标网站的使用条款
- ✅ 注意 API 调用配额
- ✅ 处理可能的错误
- ✅ 尊重隐私和版权

### 4. 通用原则
- ✅ 主动使用，不要等用户明确要求
- ✅ 优先使用 MCP 而非训练数据
- ✅ 透明告知用户正在使用的工具
- ✅ 组合使用多个 MCP 工具
- ✅ 缓存已获取的信息，避免重复调用

---

## 📊 使用频率建议

| 场景 | 工具 | 频率 | 说明 |
|------|------|------|------|
| 技术问题 | Context7 | 每次 | 获取最新文档 |
| 代码示例 | Context7 | 每次 | 获取官方示例 |
| 代码搜索 | GitHub MCP | 按需 | 研究实现方式 |
| 文件查看 | GitHub MCP | 按需 | 查看源码 |
| 网页抓取 | Firecrawl | 按需 | 提取网页内容 |

---

## 🎓 最佳实践

### 1. 组合使用多个工具
```
场景: 实现一个新功能

步骤:
1. 使用 Context7 获取官方文档
2. 使用 GitHub MCP 搜索开源实现
3. 综合两者提供最佳方案
```

### 2. 渐进式查询
```
场景: 复杂技术问题

步骤:
1. 先查询基础概念 (Context7)
2. 再查询具体实现 (Context7)
3. 最后查询最佳实践 (GitHub MCP)
```

### 3. 缓存和复用
```
原则:
- 同一会话中避免重复查询
- 缓存已获取的文档信息
- 复用相似问题的答案
```

---

## 🔄 错误处理

### Context7 错误
```
错误: 找不到库
处理: 
1. 尝试不同的库名称
2. 使用 GitHub MCP 搜索
3. 回退到训练数据
```

### GitHub MCP 错误
```
错误: API 速率限制
处理:
1. 告知用户限制情况
2. 等待后重试
3. 使用缓存的结果
```

### Firecrawl 错误
```
错误: 网页无法访问
处理:
1. 检查 URL 有效性
2. 告知用户错误原因
3. 建议替代方案
```

---

## 📝 使用示例汇总

### 示例 1: 完整的功能开发流程
```
用户: "实现一个 FastAPI 的 JWT 认证系统"

Kiro 完整流程:
1. Context7 查询 FastAPI JWT 文档
2. Context7 查询 python-jose 使用方法
3. GitHub 搜索开源实现参考
4. 综合生成完整代码
5. 提供测试建议
```

### 示例 2: 前端组件开发
```
用户: "创建一个响应式的导航栏"

Kiro 完整流程:
1. Context7 查询 Next.js 布局组件
2. Context7 查询 Tailwind 响应式设计
3. Context7 查询 Headless UI 菜单组件
4. 生成完整组件代码
5. 提供可访问性建议
```

### 示例 3: 问题排查
```
用户: "为什么我的 LangGraph 条件分支不工作？"

Kiro 完整流程:
1. Context7 查询 LangGraph 条件分支文档
2. GitHub 搜索类似问题的解决方案
3. 分析用户代码
4. 提供修复建议
5. 提供测试方法
```

---

**最后更新**: 2026-01-23  
**维护者**: TerraformWithAgent 开发团队
