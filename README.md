# AgentPro - 多阶段舆情解读与热点对齐系统（Multi-Stage Public Opinion Interpretation Agent System）

## 项目名称
**AgentPro：多阶段舆情解读与热点对齐系统**

## 运行环境
- **Python**：3.9+（推荐 3.10 或 3.11）
- **Node.js**：16+（推荐 18+）
- **包管理**：pip / npm
- **依赖版本要求**：
  - fastapi >= 0.110.0
  - pydantic >= 2.5.0
  - uvicorn >= 0.27.0

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd AgentPro
```

### 2. 后端设置

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

**注意：如果遇到路径过长错误**

如果在 Windows 上使用 Microsoft Store 版 Python，可能会遇到路径过长的错误。这是因为 Microsoft Store 版 Python 的安装路径很长。

解决方法是启用 Windows 长路径支持：

1. **以管理员身份打开 PowerShell**
   - 按 `Win + X`
   - 选择 "Windows PowerShell (管理员)" 或 "终端 (管理员)"

2. **运行以下命令**
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```
   
   如果提示已存在，使用：
   ```powershell
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Force
   ```

3. **验证设置**
   ```powershell
   Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled"
   ```

4. **重启电脑** （必须）

5. **重启后重新安装**
   ```powershell
   pip uninstall volcengine-python-sdk -y
   pip cache purge
   pip install -r requirements.txt
   ```

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys

# 安装 Playwright 浏览器（用于爬虫）
playwright install chromium

# 启动后端服务
python -m app.main
```

后端服务将在 `http://localhost:8000` 启动
- API 文档：`http://localhost:8000/docs`
- API 前缀：`/api`

### 3. 前端设置

```bash
# 安装依赖（在项目根目录）
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 4. 首次使用配置

1. 打开浏览器访问 `http://localhost:5173`
2. 进入“设置”页面
3. 添加你的 LLM API Keys（可选，未配置则使用后端 .env 中的密钥）
4. 选择要启用的平台（可选，默认启用所有平台）
5. 配置热榜和图片生成服务（可选）

**注意**：
- API Keys 会保存在浏览器本地缓存和后端配置中
- 如需清除所有设置，点击设置页面右上角的“清除缓存”按钮
- 切换到新环境时，建议先清除缓存后重新配置

## 使用方式（推荐演示路径）

- **首页（Home）**：输入议题 → 启动分析 → 观察 SSE 实时日志
- **热榜页（HotView）**：刷新热榜 → 切换平台 → 点选单条热点生成“演化解读卡”
- **数据页（DataView）**：切换数据源（workflow/hotnews）→ 查看“平台热度对比 / 关键词 / 情感等”图表

## 部署生产环境

```bash
# 前端构建
npm run build

# 后端使用 gunicorn 部署
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 项目结构说明
- `app/`：后端（FastAPI、LLM Agent、爬虫/热榜、对齐聚类、缓存）
  - `services/`：核心服务（爬虫、LLM、热榜收集器等）
  - `api/`：API 端点定义
  - `config.py`：配置管理
- `src/`：前端（Vue3、Pinia、Tailwind、图表与可视化）
  - `views/`：页面组件
  - `stores/`：Pinia 状态管理
  - `api/`：API 调用封装
- `MediaCrawler/`：第三方爬虫库（项目内集成使用）
- `Project_Documentation/`：项目文档

## 常见问题

### Q: 依赖安装失败？
A: 确保 Python 版本 >= 3.9，并且已安装 fastapi >= 0.110.0 和 pydantic >= 2.5.0。如果还有问题，尝试升级 pip：`pip install --upgrade pip`

### Q: 更换设备后仍显示旧的 API Keys？
A: 这是浏览器缓存导致的。点击设置页面右上角的“清除缓存”按钮即可。

### Q: Playwright 安装失败？
A: 运行 `playwright install --with-deps chromium` 安装浏览器及其依赖。

### Q: 安装时出现"路径过长"错误？
A: Windows 默认有 260 字符的路径长度限制。解决方法：

**启用 Windows 长路径支持**（推荐）：
1. **以管理员身份打开 PowerShell**
   - 按 `Win + X` → 选择 "Windows PowerShell (管理员)" 或 "终端 (管理员)"

2. **运行命令**
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```
   
   如果提示已存在，使用：
   ```powershell
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Force
   ```

3. **验证设置**
   ```powershell
   Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled"
   ```

4. **重启电脑**（必须）

5. **重启后重新安装**
   ```powershell
   pip uninstall volcengine-python-sdk -y
   pip cache purge
   pip install -r requirements.txt
   ```

### Q: 端口被占用？
A: 修改 `app/main.py` 中的端口配置，或使用环境变量 `PORT=8080 python -m app.main`

## 交付物建议打包方式
- **Project_SourceCode**：直接将整个项目目录压缩为 zip（包含本 README）
- **Project_Documentation**：见 `Project_Documentation/` 目录（可导出为 PDF）

