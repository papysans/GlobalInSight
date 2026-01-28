# GlobalInSight 快速启动指南

## 🚀 一键启动（推荐）

### macOS 用户

**方法 1：双击启动（最简单）**
1. 在 Finder 中找到项目根目录
2. 双击 `start.command` 文件
3. 如果提示"无法打开"，右键点击 → 选择"打开" → 点击"打开"
4. 按照提示完成环境检查和服务启动

**方法 2：终端启动**
```bash
# 在项目根目录执行
./start.sh
```

### 首次运行会自动完成

✅ 检查 Python 和 Node.js 环境  
✅ 创建 Python 虚拟环境  
✅ 安装所有依赖（Python + Node.js）  
✅ 下载小红书 MCP 服务  
✅ 配置环境变量（如果不存在）  
✅ 在 3 个新终端窗口中启动所有服务

### 启动后的服务

启动脚本会自动打开 3 个终端窗口：

1. **小红书 MCP 服务** - 端口 18060
   - 用于小红书内容发布
   - 首次使用需要扫码登录

2. **后端 API 服务** - 端口 8000
   - FastAPI 服务
   - API 文档: http://localhost:8000/docs

3. **前端开发服务器** - 端口 5173
   - Vue 3 应用
   - 访问: http://localhost:5173

## 📋 环境要求

启动脚本会自动检查以下环境：

- **Python**: 3.9+ (推荐 3.10 或 3.11)
- **Node.js**: 16+ (推荐 18+)
- **系统**: macOS (支持 Intel 和 Apple Silicon)

如果环境不满足，脚本会提示安装方法。

## 🔧 首次使用配置

### 1. 配置 API Keys（可选）

启动后访问 http://localhost:5173，进入"设置"页面：

- 添加至少一个 LLM 提供商的 API Key
- 支持：Moonshot、DeepSeek、Doubao、Gemini、Zhipu
- 配置火山引擎密钥（用于图片生成）

**注意**: 如果不在前端配置，系统会使用 `.env` 文件中的密钥。

### 2. 登录小红书（首次使用）

如果首次运行时跳过了登录，可以手动登录：

```bash
# Apple Silicon (M1/M2/M3)
cd XHS-MCP/xiaohongshu-mcp-darwin-arm64
./xiaohongshu-login-darwin-arm64

# Intel 芯片
cd XHS-MCP/xiaohongshu-mcp-darwin-amd64
./xiaohongshu-login-darwin-amd64
```

登录后重启 MCP 服务窗口即可。

## 🛠️ 手动启动（高级用户）

如果需要单独启动某个服务：

### 启动小红书 MCP
```bash
./scripts/start-xhs-mcp.sh
```

### 启动后端
```bash
./scripts/start-backend.sh
```

### 启动前端
```bash
./scripts/start-frontend.sh
```

## ❓ 常见问题

### Q: 双击 start.command 没反应？
A: 右键点击文件 → 选择"打开" → 在弹出的对话框中点击"打开"。macOS 首次运行未签名的脚本需要此操作。

### Q: 提示 Python 或 Node.js 版本过低？
A: 使用 Homebrew 安装最新版本：
```bash
# 安装 Python
brew install python@3.11

# 安装 Node.js
brew install node
```

### Q: 依赖安装失败？
A: 
1. 确保网络连接正常
2. 尝试清理缓存后重新运行：
```bash
rm -rf .venv node_modules
./start.sh
```

### Q: 小红书 MCP 服务连接失败？
A: 
1. 检查 MCP 服务窗口是否正常运行
2. 确认已完成小红书登录
3. 验证服务: `curl http://localhost:18060/mcp`

### Q: 端口被占用？
A: 检查并关闭占用端口的进程：
```bash
# 查看端口占用
lsof -i :8000
lsof -i :5173
lsof -i :18060

# 关闭进程
kill -9 <PID>
```

### Q: 如何停止所有服务？
A: 在每个终端窗口中按 `Ctrl+C`，或直接关闭终端窗口。

## 📁 脚本文件说明

```
start.sh                    # 主启动脚本（检查环境、安装依赖、启动服务）
start.command               # macOS 双击启动入口
scripts/
  ├── start-xhs-mcp.sh     # 小红书 MCP 服务启动脚本
  ├── start-backend.sh     # 后端服务启动脚本
  └── start-frontend.sh    # 前端服务启动脚本
```

## 🎯 下一步

启动成功后：

1. 访问 http://localhost:5173
2. 进入"设置"页面配置 API Keys
3. 测试小红书 MCP 连接
4. 在"首页"输入议题开始分析
5. 查看"热榜页"浏览热点数据
6. 在"数据页"查看可视化分析

## 📚 更多文档

- [完整 README](README.md)
- [小红书 MCP 设置指南](docs/XHS_SETUP.md)
- [API 使用文档](src/API_USAGE.md)
- [项目文档](Project_Documentation/)

---

**提示**: 如果遇到问题，请查看各个终端窗口的日志输出，通常会有详细的错误信息。
