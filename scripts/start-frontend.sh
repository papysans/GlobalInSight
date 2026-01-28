#!/bin/bash

# 前端服务启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  前端开发服务器 (Vue 3 + Vite)${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}错误: node_modules 不存在${NC}"
    echo "请先运行主启动脚本: ./start.sh"
    exit 1
fi

echo -e "${GREEN}启动前端开发服务器...${NC}"
echo "端口: 5173"
echo "访问: http://localhost:5173"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止服务${NC}"
echo ""

# 启动服务
npm run dev
