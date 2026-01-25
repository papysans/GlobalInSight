# GlobalInSight - 多阶段舆情解读与热点对齐系统（Multi-Stage Public Opinion Interpretation Agent System）

## 项目名称
**GlobalInSight：多阶段舆情解读与热点对齐系统**

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
cd GlobalInSight
```

### 2. 小红书 MCP 服务设置（必须）

本项目的小红书发布功能依赖外部 MCP 服务，请先完成以下设置：

#### 2.1 下载 MCP 服务程序

根据您的系统架构选择对应版本：

```bash
# macOS (Apple Silicon / M1/M2/M3)
curl -L -o XHS-MCP/xiaohongshu-mcp-darwin-arm64/xiaohongshu-mcp-darwin-arm64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-arm64
curl -L -o XHS-MCP/xiaohongshu-mcp-darwin-arm64/xiaohongshu-login-darwin-arm64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-darwin-arm64

# macOS (Intel)
curl -L -o XHS-MCP/xiaohongshu-mcp-darwin-amd64/xiaohongshu-mcp-darwin-amd64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-amd64
curl -L -o XHS-MCP/xiaohongshu-mcp-darwin-amd64/xiaohongshu-login-darwin-amd64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-darwin-amd64

# 设置可执行权限
chmod +x XHS-MCP/xiaohongshu-mcp-darwin-*/xiaohongshu-mcp-darwin-*
chmod +x XHS-MCP/xiaohongshu-mcp-darwin-*/xiaohongshu-login-darwin-*
```

#### 2.2 首次登录小红书（必须）

```bash
# 进入 XHS-MCP 目录
cd XHS-MCP/xiaohongshu-mcp-darwin-arm64

# 运行登录工具获取 cookie
# Apple Silicon:
./xiaohongshu-login-darwin-arm64

# Intel (如果是 Intel 芯片，请先 cd ../xiaohongshu-mcp-darwin-amd64):
./xiaohongshu-login-darwin-amd64

# 程序会打开浏览器窗口，扫码登录小红书
# 登录成功后关闭窗口，程序会自动保存登录状态到 cookies.json

# 返回项目根目录
cd ../..
```

#### 2.3 启动 MCP 服务（保持运行）

```bash
# 在新的终端窗口中启动服务（默认端口 18060）
cd XHS-MCP/xiaohongshu-mcp-darwin-arm64

# Apple Silicon:
./xiaohongshu-mcp-darwin-arm64

# Intel (如果是 Intel 芯片，请先 cd ../xiaohongshu-mcp-darwin-amd64):
./xiaohongshu-mcp-darwin-amd64

# 验证服务是否正常运行（在另一个终端窗口）
curl http://localhost:18060/mcp
```

**重要提示**：
- 首次运行时可能会自动下载无头浏览器（约 150MB），请耐心等待
- MCP 服务需要在后台保持运行，建议新开一个终端窗口
- 如果发布失败提示未登录，请重新运行步骤 2.2 的登录工具
- 详细文档：[XHS_SETUP.md](docs/XHS_SETUP.md)

### 3. 后端设置

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

# 配置环境变量(可选)
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

### 4. 前端设置

```bash
# 安装依赖（在项目根目录）
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 5. 首次使用配置

1. 打开浏览器访问 `http://localhost:5173`
2. 进入"设置"页面
3. 添加你的 LLM API Keys（可选，未配置则使用后端 .env 中的密钥）
4. 选择要启用的平台（可选，默认启用所有平台）
5. 配置热榜和图片生成服务（可选）
6. 点击"测试小红书 MCP 连接"按钮，确保 MCP 服务正常运行

**注意**：
- API Keys 会保存在浏览器本地缓存和后端配置中
- 如需清除所有设置，点击设置页面右上角的"清除缓存"按钮
- 切换到新环境时，建议先清除缓存后重新配置

## 使用方式（推荐演示路径）

- **首页（Home）**：输入议题 → 启动分析 → 观察 SSE 实时日志 → 查看预览页面 → 一键发布小红书
- **热榜页（HotView）**：刷新热榜 → 切换平台 → 点选单条热点生成"演化解读卡"
- **数据页（DataView）**：切换数据源（workflow/hotnews）→ 查看"平台热度对比 / 关键词 / 情感等"图表

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
- `MediaCrawler/`：第三方爬虫库（已集成到项目中）
- `XHS-MCP/`：小红书 MCP 服务二进制文件
- `Project_Documentation/`：项目文档

## 常见问题

### Q: 依赖安装失败？
A: 确保 Python 版本 >= 3.9，并且已安装 fastapi >= 0.110.0 和 pydantic >= 2.5.0。如果还有问题，尝试升级 pip：`pip install --upgrade pip`

### Q: 更换设备后仍显示旧的 API Keys？
A: 这是浏览器缓存导致的。点击设置页面右上角的"清除缓存"按钮即可。

### Q: Playwright 安装失败？
A: 运行 `playwright install --with-deps chromium` 安装浏览器及其依赖。

### Q: 小红书 MCP 服务连接失败？
A: 
1. 确保 MCP 服务正在运行（步骤 2.3）
2. 检查端口 18060 是否被占用
3. 重新运行登录工具（步骤 2.2）
4. 查看 MCP 服务的终端输出日志

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

---

## 📦 集成的开源项目

本项目集成了以下优秀的开源项目，在此表示衷心感谢：

### 1. MediaCrawler - 自媒体平台爬虫

**项目地址**：[https://github.com/NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)

**简介**：功能强大的多平台自媒体数据采集工具，支持小红书、抖音、快手、B站、微博、贴吧、知乎等主流平台的公开信息抓取。

**集成说明**：MediaCrawler 已完整集成到本项目的 `MediaCrawler/` 目录中，无需额外安装。项目启动时会自动使用集成的爬虫功能。

**如需单独使用 MediaCrawler**：

```bash
# 进入 MediaCrawler 目录
cd MediaCrawler

# 安装 uv（如果尚未安装）
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: 访问 https://docs.astral.sh/uv/getting-started/installation

# 使用 uv 同步依赖
uv sync

# 安装浏览器驱动
uv run playwright install

# 运行爬虫（以小红书为例）
uv run main.py --platform xhs --lt qrcode --type search

# 查看更多平台和选项
uv run main.py --help

# 启动 WebUI（可选）
uv run uvicorn api.main:app --port 8080 --reload
# 访问 http://localhost:8080
```

**配置说明**：
- 配置文件：`MediaCrawler/config/base_config.py`
- 支持数据存储：CSV、JSON、Excel、SQLite、MySQL
- 完整文档：[MediaCrawler 文档](https://nanmicoder.github.io/MediaCrawler/)

---

### 2. xiaohongshu-mcp - 小红书 MCP 服务

**项目地址**：[https://github.com/xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)

**简介**：基于 Model Context Protocol (MCP) 的小红书发布服务，支持自动发布内容到小红书平台。

**集成说明**：本项目依赖 xiaohongshu-mcp 服务实现小红书内容发布功能。该服务需要独立运行，请参考"快速开始"第 2 步完成设置。

**注意事项**：
- MCP 服务必须在后台保持运行
- 首次使用需要扫码登录小红书
- 登录状态保存在 `cookies.json` 文件中
- 详细文档：[XHS_SETUP.md](docs/XHS_SETUP.md)

---

## 🙏 鸣谢

感谢以下开源项目和开发者的贡献：

### 核心依赖项目
- **[MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)** by [@NanmiCoder](https://github.com/NanmiCoder) - 强大的多平台自媒体数据采集工具
- **[xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)** by [@xpzouying](https://github.com/xpzouying) - 小红书 MCP 发布服务

### 技术栈
- **[FastAPI](https://fastapi.tiangolo.com/)** - 现代化的 Python Web 框架
- **[Vue 3](https://vuejs.org/)** - 渐进式 JavaScript 框架
- **[Playwright](https://playwright.dev/)** - 浏览器自动化框架
- **[Pinia](https://pinia.vuejs.org/)** - Vue 状态管理库
- **[Tailwind CSS](https://tailwindcss.com/)** - 实用优先的 CSS 框架

### 特别感谢
- MediaCrawler 项目提供的稳定爬虫基础设施
- xiaohongshu-mcp 项目实现的小红书发布能力
- 所有为开源社区做出贡献的开发者们

---

## 📄 许可证

本项目采用 MIT 许可证。集成的开源项目遵循其各自的许可证：
- MediaCrawler: Apache License 2.0
- xiaohongshu-mcp: 请查看其项目仓库

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 Issue
- 发起 Pull Request
- 邮件联系项目维护者
