#!/bin/bash

# macOS 停止腳本 - Lights MCP Server
# 此腳本會停止 Docker 容器和 socat 轉發

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== 停止 Lights MCP Server (macOS) ===${NC}\n"

# 停止 Docker 容器
echo "停止 Docker 容器..."
if docker-compose -f docker-compose.macos.yml ps -q 2>/dev/null | grep -q .; then
    docker-compose -f docker-compose.macos.yml down
    echo -e "${GREEN}✓ Docker 容器已停止${NC}"
else
    echo "沒有運行中的容器"
fi

# 停止 socat
echo "停止 socat 轉發..."
TCP_PORT=5555
if pkill -f "socat.*$TCP_PORT" 2>/dev/null; then
    echo -e "${GREEN}✓ socat 已停止${NC}"
else
    echo "沒有運行中的 socat 程序"
fi

echo -e "\n${GREEN}=== 所有服務已停止 ===${NC}"

