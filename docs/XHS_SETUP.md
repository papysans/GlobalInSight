# 小红书 MCP 服务安装与用指南

本项目功能依赖于外部的 `xiaohongshu-mcp` 服务。请按照以下步骤在本地安装并启动该服务。

## 1. 下载服务程序

根据您的系统架构选择对应的版本：

### macOS (Apple Silicon / M1/M2/M3)
```bash
# 下载主程序
curl -L -o xiaohongshu-mcp-darwin-arm64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-arm64

# 下载登录工具
curl -L -o xiaohongshu-login-darwin-arm64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-darwin-arm64
```

### macOS (Intel)
```bash
# 下载主程序
curl -L -o xiaohongshu-mcp-darwin-amd64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-amd64

# 下载登录工具
curl -L -o xiaohongshu-login-darwin-amd64 https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-darwin-amd64
```

## 2. 设置权限

下载完成后，需要赋予可执行权限：

```bash
chmod +x xiaohongshu-mcp-darwin-*
chmod +x xiaohongshu-login-darwin-*
```

## 3. 首次登录 (关键步骤)

在启动 MCP 服务之前，必须先进行登录以获取 cookie：

```bash
# 运行登录工具 (Apple Silicon)
./xiaohongshu-login-darwin-arm64

# 或者 (Intel)
./xiaohongshu-login-darwin-amd64
```

程序会打开一个浏览器窗口，请在其中扫码登录小红书。登录成功后关闭窗口，程序会自动保存登录状态。

## 4. 启动 MCP 服务

保持该终端窗口开启（或在后台运行）：

```bash
# 启动服务 (默认端口 18060)
# (Apple Silicon)
./xiaohongshu-mcp-darwin-arm64

# 或者 (Intel)
./xiaohongshu-mcp-darwin-amd64
```

> **注意**：首次运行时可能会自动下载无头浏览器（约 150MB），请耐心等待。

## 5. 验证连接

服务启动后，您可以在 GlobalInSight 项目的「设置」页面点击「测试连接」按钮，或使用以下命令手动测试：

```bash
curl http://localhost:18060/mcp
```

## 常见问题

- **端口冲突**：默认端口为 18060。
- **登录失效**：如果发布失败提示未登录，请重新运行步骤 3 的登录工具。
- **文件位置**：建议将这两个二进制文件放在项目的根目录或专门的 `tools/` 目录下方便管理。
