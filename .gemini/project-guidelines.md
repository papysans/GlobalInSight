# GlobalInSight (AgentPro) 项目开发规范

> 多阶段舆情解读与热点对齐系统 - 项目开发指南

---

## 项目概述

**AgentPro** 是一个 AI 驱动的多阶段舆情解读与热点对齐系统，主要功能：
- **首页（Home）**：输入议题 → 启动分析 → SSE 实时日志
- **热榜页（HotView）**：刷新热榜 → 切换平台 → 生成"演化解读卡"
- **数据页（DataView）**：多数据源图表展示（平台热度对比、关键词、情感分析）
- **设置页（Settings）**：LLM API Keys、平台配置、热榜服务配置

---

## 技术架构

### 后端技术栈
```
核心框架:     FastAPI (Python 3.9+)
LLM 框架:     LangGraph + LangChain
LLM 提供商:   Deepseek / OpenAI / Google Gemini
数据库:       SQLite / MySQL (异步: aiosqlite, aiomysql)
ORM:          SQLAlchemy 2.0+
爬虫:         Playwright + BeautifulSoup + MediaCrawler
缓存:         Redis
任务调度:     APScheduler
日志:         Loguru
```

### 前端技术栈
```
框架:         Vue 3 (Composition API)
构建工具:     Vite 5
状态管理:     Pinia
样式:         Tailwind CSS 3 + @tailwindcss/typography
图表:         Chart.js
图标:         Lucide Vue Next
Markdown:     markdown-it / marked
```

---

## 目录结构

### 后端 (`app/`)
```
app/
├── main.py              # 应用入口 (Uvicorn 启动)
├── config.py            # 配置管理
├── llm.py               # LLM 客户端封装
├── schemas.py           # Pydantic 数据模型
├── api/                 # API 端点
│   └── ...
└── services/            # 核心服务
    ├── workflow.py              # 多阶段工作流 (LangGraph)
    ├── workflow_status.py       # 工作流状态管理
    ├── tophub_collector.py      # TopHub 热榜收集
    ├── hn_hot_collector.py      # Hacker News 热榜收集
    ├── hotnews_alignment.py     # 热点对齐聚类
    ├── hotnews_interpreter.py   # 热点解读服务
    ├── hotnews_llm_enricher.py  # LLM 热点增强
    ├── media_crawler_service.py # 媒体爬虫服务
    ├── foreign_news_crawler_service.py # 海外新闻爬虫
    ├── image_generator.py       # 图片/词云生成
    ├── hot_news_cache.py        # 热点缓存
    ├── hot_news_scheduler.py    # 定时任务调度
    └── user_settings.py         # 用户设置管理
```

### 前端 (`src/`)
```
src/
├── main.js              # 应用入口
├── App.vue              # 根组件 (路由配置)
├── style.css            # 全局样式
├── api/                 # API 调用封装
├── components/          # 公共组件
├── stores/              # Pinia 状态管理
│   ├── analysis.js      # 分析状态
│   ├── config.js        # 配置状态
│   ├── outputs.js       # 输出状态
│   └── workflow.js      # 工作流状态
└── views/               # 页面组件
    ├── HomeView.vue     # 首页 (议题分析)
    ├── HotView.vue      # 热榜页
    ├── DataView.vue     # 数据可视化页
    ├── SettingsView.vue # 设置页
    ├── ArchView.vue     # 架构展示页
    └── VisionView.vue   # 愿景页
```

---

## 开发规范

### API 规范
- **API 前缀**: `/api`
- **API 文档**: `http://localhost:8000/docs` (Swagger UI)
- **SSE 端点**: 使用 `text/event-stream` 实现实时日志推送

### 前端组件规范
- ✅ 使用 Vue 3 Composition API (`<script setup>`)
- ✅ 状态管理使用 Pinia stores
- ✅ 样式使用 Tailwind CSS 原子类
- ✅ 图标使用 Lucide Vue Next
- ❌ 避免使用 Options API
- ❌ 避免内联样式

### 后端服务规范
- ✅ 异步优先：使用 `async/await`
- ✅ 日志使用 Loguru
- ✅ 配置使用 `app/config.py` 统一管理
- ✅ LLM 调用使用 `app/llm.py` 封装
- ✅ 数据模型使用 Pydantic v2
- ✅ Git 提交信息必须使用**中文**

---

## 运行项目

### 后端
```bash
# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 启动服务
python -m app.main
# 服务运行在 http://localhost:8000
```

### 前端
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 服务运行在 http://localhost:5173
```

---

## 核心服务说明

### 1. 工作流服务 (`workflow.py`)
- 使用 LangGraph 实现多阶段分析流程
- 支持 SSE 实时状态推送
- 包含需求分析、信息收集、内容生成等阶段

### 2. 热榜收集器
- `tophub_collector.py`: 国内热榜聚合
- `hn_hot_collector.py`: Hacker News 热榜
- 支持多平台、定时刷新、缓存

### 3. 热点对齐 (`hotnews_alignment.py`)
- 跨平台热点聚类
- 话题相似度计算
- 热度排序和去重

### 4. 爬虫服务
- `media_crawler_service.py`: 社交媒体爬虫
- `foreign_news_crawler_service.py`: 海外新闻爬虫
- 使用 Playwright 处理动态页面

---

## 环境变量 (.env)

```bash
# LLM API Keys
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# 阿里云 (图片生成)
ALIYUN_ACCESS_KEY=your_access_key
ALIYUN_SECRET_KEY=your_secret_key

# 火山引擎 (可选)
VOLCENGINE_ACCESS_KEY=your_access_key
VOLCENGINE_SECRET_KEY=your_secret_key

# Redis (可选)
REDIS_URL=redis://localhost:6379
```

---

## 文档位置
- 项目文档: `Project_Documentation/`
- API 使用说明: `src/API_USAGE.md`
- README: 项目根目录 `README.md`
