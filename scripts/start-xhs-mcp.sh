#!/bin/bash

# 小红书 MCP 服务启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  小红书 MCP 服务${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检测系统架构
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    ARCH_NAME="darwin-arm64"
else
    ARCH_NAME="darwin-amd64"
fi

XHS_DIR="XHS-MCP/xiaohongshu-mcp-$ARCH_NAME"
XHS_MCP="$XHS_DIR/xiaohongshu-mcp-$ARCH_NAME"
XHS_LOGIN="$XHS_DIR/xiaohongshu-login-$ARCH_NAME"

# 检查文件是否存在
if [ ! -f "$XHS_MCP" ]; then
    echo -e "${RED}错误: 未找到 MCP 服务文件${NC}"
    echo "请先运行主启动脚本: ./start.sh"
    read -p "按 Enter 键退出..."
    exit 1
fi

# 检查 MCP 服务登录状态（通过 API）
check_login_via_mcp() {
    # 尝试调用 MCP API 检查登录状态
    local response=$(curl -s -X POST http://localhost:18060/mcp \
        -H "Content-Type: application/json" \
        -d '[
            {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "startup-check", "version": "1.0"}
                },
                "id": 1
            },
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "check_login_status",
                    "arguments": {}
                },
                "id": 2
            }
        ]' 2>/dev/null)
    
    # 检查响应中是否包含"已登录"或"logged in"
    if echo "$response" | grep -q "已登录\|logged in"; then
        return 0
    else
        return 1
    fi
}

# 检查登录状态函数（先尝试 API，失败则检查文件）
check_login() {
    # 如果 MCP 服务已运行，使用 API 检查
    if curl -s http://localhost:18060/mcp > /dev/null 2>&1; then
        check_login_via_mcp
        return $?
    fi
    
    # 否则检查 cookies 文件
    if [ ! -f "$XHS_DIR/cookies.json" ]; then
        return 1
    fi
    
    if [ ! -s "$XHS_DIR/cookies.json" ]; then
        return 1
    fi
    
    if ! grep -q "web_session" "$XHS_DIR/cookies.json" 2>/dev/null; then
        return 1
    fi
    
    return 0
}

# 执行登录
do_login() {
    echo -e "${BLUE}启动登录工具...${NC}"
    echo "请在弹出的浏览器窗口中扫码登录"
    echo ""
    
    cd "$XHS_DIR"
    ./"xiaohongshu-login-$ARCH_NAME"
    LOGIN_RESULT=$?
    cd - > /dev/null
    
    if [ $LOGIN_RESULT -eq 0 ] && [ -f "$XHS_DIR/cookies.json" ]; then
        echo -e "${GREEN}登录成功 ✓${NC}"
        return 0
    else
        echo -e "${RED}登录失败或已取消${NC}"
        return 1
    fi
}

# 检查登录状态
echo -e "${BLUE}检查登录状态...${NC}"
check_login
LOGIN_STATUS=$?

if [ $LOGIN_STATUS -eq 0 ]; then
    echo -e "${GREEN}登录状态有效 ✓${NC}"
else
    echo -e "${YELLOW}警告: 未找到有效的登录信息${NC}"
    echo "小红书发布功能将不可用"
    echo ""
    read -p "是否现在登录？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! do_login; then
            echo -e "${YELLOW}跳过登录，服务将启动但发布功能不可用${NC}"
            echo "稍后可手动运行: cd $XHS_DIR && ./xiaohongshu-login-$ARCH_NAME"
            echo ""
            read -p "按 Enter 键继续启动服务..."
        fi
    else
        echo -e "${YELLOW}跳过登录，服务将启动但发布功能不可用${NC}"
        echo "稍后可手动运行: cd $XHS_DIR && ./xiaohongshu-login-$ARCH_NAME"
        echo ""
        read -p "按 Enter 键继续启动服务..."
    fi
fi

echo ""
echo -e "${GREEN}启动小红书 MCP 服务...${NC}"
echo "端口: 18060"
echo "验证: curl http://localhost:18060/mcp"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止服务${NC}"
echo ""

# 进入目录并启动服务
cd "$XHS_DIR"
./"xiaohongshu-mcp-$ARCH_NAME"
