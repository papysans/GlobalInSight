#!/bin/bash

# Opinion MCP 服务启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Opinion MCP 服务 (舆论分析 MCP)${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 激活虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
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

# 检查后端服务是否运行
echo -e "${BLUE}检查后端服务状态...${NC}"
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}后端服务运行中 ✓${NC}"
else
    echo -e "${YELLOW}警告: 后端服务未运行${NC}"
    echo "Opinion MCP 需要后端服务支持，请先启动后端服务"
    echo "运行: ./scripts/start-backend.sh"
    echo ""
    read -p "是否继续启动 MCP 服务？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}启动 Opinion MCP 服务...${NC}"
echo "端口: 18061"
echo "验证: curl http://localhost:18061/health"
if [ -z "${IMAGE_PUBLISH_MODE}" ]; then
    export IMAGE_PUBLISH_MODE=ai_and_cards
fi
echo "图片发布模式: ${IMAGE_PUBLISH_MODE}"
echo ""
echo -e "${BLUE}可用工具:${NC}"
echo "  • analyze_topic     - 启动舆论分析任务"
echo "  • get_analysis_status - 查询分析进度"
echo "  • get_analysis_result - 获取分析结果"
echo "  • get_hot_news      - 获取热榜数据"
echo "  • get_settings      - 获取配置信息"
echo "  • update_copywriting - 修改文案"
echo "  • publish_to_xhs    - 发布到小红书"
echo "  • register_webhook  - 注册进度推送"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止服务${NC}"
echo ""

# 启动服务
python3 -m opinion_mcp.server --port 18061
