#!/bin/bash

# 后端服务启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  后端 API 服务 (FastAPI)${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 激活虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}错误: 虚拟环境不存在${NC}"
    echo "请先运行主启动脚本: ./start.sh"
    exit 1
fi

echo -e "${GREEN}激活虚拟环境...${NC}"
source .venv/bin/activate

# 检查环境变量
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: .env 文件不存在${NC}"
    echo "将使用默认配置，部分功能可能不可用"
    echo ""
fi

echo -e "${GREEN}启动后端服务...${NC}"
echo "端口: 8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止服务${NC}"
echo ""

# 启动服务
python3 -m app.main
