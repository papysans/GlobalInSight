#!/bin/bash

# GlobalInSight 快速启动脚本
# 适用于 macOS 系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测系统架构
detect_arch() {
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        echo "darwin-arm64"
    else
        echo "darwin-amd64"
    fi
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python 版本
check_python() {
    print_info "检查 Python 环境..."
    
    if ! command_exists python3; then
        print_error "未找到 Python3，请先安装 Python 3.9+"
        print_info "推荐使用 Homebrew 安装: brew install python@3.11"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        print_error "Python 版本过低 ($PYTHON_VERSION)，需要 3.9+"
        exit 1
    fi
    
    print_success "Python 版本: $PYTHON_VERSION ✓"
}

# 检查 Node.js 版本
check_node() {
    print_info "检查 Node.js 环境..."
    
    if ! command_exists node; then
        print_error "未找到 Node.js，请先安装 Node.js 16+"
        print_info "推荐使用 Homebrew 安装: brew install node"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    
    if [ "$NODE_VERSION" -lt 16 ]; then
        print_error "Node.js 版本过低 (v$NODE_VERSION)，需要 16+"
        exit 1
    fi
    
    print_success "Node.js 版本: v$(node --version | cut -d'v' -f2) ✓"
}

# 设置虚拟环境
setup_venv() {
    print_info "设置 Python 虚拟环境..."
    
    if [ ! -d ".venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv .venv
    fi
    
    print_success "虚拟环境已就绪 ✓"
}

# 安装 Python 依赖
install_python_deps() {
    print_info "检查 Python 依赖..."
    
    source .venv/bin/activate
    
    # 检查是否需要安装依赖
    if ! python -c "import fastapi" 2>/dev/null; then
        print_info "安装 Python 依赖（首次运行可能需要几分钟）..."
        pip install --upgrade pip -q
        pip install -r requirements.txt -q
        print_success "Python 依赖安装完成 ✓"
    else
        print_success "Python 依赖已安装 ✓"
    fi
    
    # 检查 Playwright
    if ! python -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
        print_info "安装 Playwright 浏览器..."
        playwright install chromium
        print_success "Playwright 安装完成 ✓"
    fi
}

# 安装 Node.js 依赖
install_node_deps() {
    print_info "检查 Node.js 依赖..."
    
    if [ ! -d "node_modules" ]; then
        print_info "安装 Node.js 依赖（首次运行可能需要几分钟）..."
        npm install
        print_success "Node.js 依赖安装完成 ✓"
    else
        print_success "Node.js 依赖已安装 ✓"
    fi
}

# 检查环境变量
check_env() {
    print_info "检查环境变量配置..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，从 .env.example 复制..."
        cp .env.example .env
        print_warning "请编辑 .env 文件，填入你的 API Keys"
        print_info "至少需要配置一个 LLM 提供商的 API Key"
    else
        print_success "环境变量配置文件存在 ✓"
    fi
}

# 检查小红书登录状态
check_xhs_login() {
    local XHS_DIR=$1
    
    # 检查 cookies.json 是否存在且非空
    if [ ! -f "$XHS_DIR/cookies.json" ] || [ ! -s "$XHS_DIR/cookies.json" ]; then
        return 1
    fi
    
    # 检查是否包含必要字段
    if ! grep -q "web_session" "$XHS_DIR/cookies.json" 2>/dev/null; then
        return 1
    fi
    
    return 0
}

# 执行小红书登录
do_xhs_login() {
    local XHS_DIR=$1
    local ARCH=$2
    local XHS_LOGIN="$XHS_DIR/xiaohongshu-login-$ARCH"
    
    print_info "启动小红书登录工具..."
    print_info "请在弹出的浏览器窗口中扫码登录"
    echo ""
    
    cd "$XHS_DIR"
    ./"xiaohongshu-login-$ARCH"
    LOGIN_RESULT=$?
    cd - > /dev/null
    
    if [ $LOGIN_RESULT -eq 0 ] && [ -f "$XHS_DIR/cookies.json" ]; then
        print_success "登录成功 ✓"
        return 0
    else
        print_error "登录失败或已取消"
        return 1
    fi
}

# 设置小红书 MCP
setup_xhs_mcp() {
    print_info "检查小红书 MCP 服务..."
    
    ARCH=$(detect_arch)
    XHS_DIR="XHS-MCP/xiaohongshu-mcp-$ARCH"
    XHS_MCP="$XHS_DIR/xiaohongshu-mcp-$ARCH"
    XHS_LOGIN="$XHS_DIR/xiaohongshu-login-$ARCH"
    
    # 创建目录
    mkdir -p "$XHS_DIR"
    
    # 检查 MCP 可执行文件
    if [ ! -f "$XHS_MCP" ]; then
        print_warning "未找到小红书 MCP 服务，正在下载..."
        curl -L -o "$XHS_MCP" "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-$ARCH"
        curl -L -o "$XHS_LOGIN" "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-$ARCH"
        chmod +x "$XHS_MCP"
        chmod +x "$XHS_LOGIN"
        print_success "小红书 MCP 服务下载完成 ✓"
    else
        chmod +x "$XHS_MCP" 2>/dev/null || true
        chmod +x "$XHS_LOGIN" 2>/dev/null || true
        print_success "小红书 MCP 服务已存在 ✓"
    fi
    
    # 检查登录状态
    print_info "检查小红书登录状态..."
    check_xhs_login "$XHS_DIR"
    LOGIN_STATUS=$?
    
    if [ $LOGIN_STATUS -eq 0 ]; then
        print_success "小红书登录状态有效 ✓"
    else
        print_warning "未找到有效的小红书登录信息"
        print_info "首次使用需要登录小红书"
        read -p "是否现在登录？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if do_xhs_login "$XHS_DIR" "$ARCH"; then
                print_success "登录完成，可以使用小红书发布功能 ✓"
            else
                print_warning "登录失败，小红书发布功能将不可用"
                print_info "稍后可运行: cd $XHS_DIR && ./xiaohongshu-login-$ARCH"
            fi
        else
            print_warning "跳过登录，小红书发布功能将不可用"
            print_info "稍后可运行: cd $XHS_DIR && ./xiaohongshu-login-$ARCH"
        fi
    fi
}

# 主函数
main() {
    clear
    echo "================================================"
    echo "  GlobalInSight 快速启动脚本"
    echo "  Multi-Stage Public Opinion Interpretation"
    echo "================================================"
    echo ""
    
    # 检查环境
    check_python
    check_node
    
    # 设置环境
    setup_venv
    check_env
    install_python_deps
    install_node_deps
    setup_xhs_mcp
    
    echo ""
    print_success "环境检查完成！"
    echo ""
    print_info "准备启动服务..."
    echo ""
    
    # 询问是否启动 Opinion MCP 服务
    echo ""
    read -p "是否启动 Opinion MCP 服务（用于 ClawdBot 集成）？(y/n) " -n 1 -r START_OPINION_MCP
    echo ""
    
    # 询问是否启动卡片渲染服务
    read -p "是否启动卡片渲染服务（用于 OpenClaw 数据卡片生成）？(y/n) " -n 1 -r START_RENDERER
    echo ""
    
    # 启动服务
    SVC_COUNT=3
    [[ $START_OPINION_MCP =~ ^[Yy]$ ]] && SVC_COUNT=$((SVC_COUNT + 1))
    [[ $START_RENDERER =~ ^[Yy]$ ]] && SVC_COUNT=$((SVC_COUNT + 1))
    
    print_info "将在 $SVC_COUNT 个新终端窗口中启动服务："
    print_info "  1. 小红书 MCP 服务 (端口 18060)"
    print_info "  2. 后端 API 服务 (端口 8000)"
    print_info "  3. 前端开发服务器 (端口 5173)"
    [[ $START_OPINION_MCP =~ ^[Yy]$ ]] && print_info "  • Opinion MCP 服务 (端口 18061)"
    [[ $START_RENDERER =~ ^[Yy]$ ]] && print_info "  • 卡片渲染服务 (端口 3001)"
    echo ""
    
    read -p "按 Enter 键继续..." -r
    
    # 获取当前目录
    CURRENT_DIR=$(pwd)
    ARCH=$(detect_arch)
    
    # 启动小红书 MCP 服务
    osascript -e "tell application \"Terminal\" to do script \"cd '$CURRENT_DIR' && ./scripts/start-xhs-mcp.sh\""
    sleep 2
    
    # 启动后端服务
    osascript -e "tell application \"Terminal\" to do script \"cd '$CURRENT_DIR' && ./scripts/start-backend.sh\""
    sleep 2
    
    # 启动前端服务
    osascript -e "tell application \"Terminal\" to do script \"cd '$CURRENT_DIR' && ./scripts/start-frontend.sh\""
    
    # 启动 Opinion MCP 服务（如果用户选择）
    if [[ $START_OPINION_MCP =~ ^[Yy]$ ]]; then
        sleep 2
        osascript -e "tell application \"Terminal\" to do script \"cd '$CURRENT_DIR' && ./scripts/start-opinion-mcp.sh\""
    fi
    
    # 启动卡片渲染服务（如果用户选择）
    if [[ $START_RENDERER =~ ^[Yy]$ ]]; then
        sleep 2
        osascript -e "tell application \"Terminal\" to do script \"cd '$CURRENT_DIR' && ./scripts/start-renderer.sh\""
    fi
    
    echo ""
    print_success "所有服务已在新窗口中启动！"
    echo ""
    print_info "服务地址："
    print_info "  • 前端: http://localhost:5173"
    print_info "  • 后端 API: http://localhost:8000"
    print_info "  • API 文档: http://localhost:8000/docs"
    print_info "  • 小红书 MCP: http://localhost:18060/mcp"
    if [[ $START_OPINION_MCP =~ ^[Yy]$ ]]; then
        print_info "  • Opinion MCP: http://localhost:18061/health"
    fi
    if [[ $START_RENDERER =~ ^[Yy]$ ]]; then
        print_info "  • 卡片渲染: http://localhost:3001/healthz"
    fi
    echo ""
    print_info "首次使用请访问前端设置页面配置 API Keys"
    if [[ $START_OPINION_MCP =~ ^[Yy]$ ]]; then
        print_info "Opinion MCP 可用于 ClawdBot 集成，详见 README.md"
    fi
    echo ""
}

# 运行主函数
main
