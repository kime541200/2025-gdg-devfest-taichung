#!/bin/bash

# macOS 啟動腳本 - Lights MCP Server
# 此腳本會自動檢測 Arduino 裝置並啟動 socat 轉發

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Lights MCP Server (macOS) 啟動腳本 ===${NC}\n"

# 檢查 socat 是否已安裝
if ! command -v socat &> /dev/null; then
    echo -e "${RED}錯誤：未找到 socat 命令${NC}"
    echo "請先安裝 socat："
    echo "  brew install socat"
    exit 1
fi

# 檢查 Docker 是否在運行
if ! docker info &> /dev/null; then
    echo -e "${RED}錯誤：Docker 未運行${NC}"
    echo "請先啟動 Docker Desktop"
    exit 1
fi

# 尋找 Arduino 裝置
echo "正在尋找 Arduino 裝置..."
ARDUINO_PORT=""

# 尋找 cu.usbmodem* 或 cu.usbserial*
for port in /dev/cu.usbmodem* /dev/cu.usbserial*; do
    if [ -e "$port" ]; then
        ARDUINO_PORT="$port"
        break
    fi
done

if [ -z "$ARDUINO_PORT" ]; then
    echo -e "${RED}錯誤：未找到 Arduino 裝置${NC}"
    echo "請確保："
    echo "  1. Arduino 已連接到電腦"
    echo "  2. 必要的驅動程式已安裝"
    echo ""
    echo "可用的序列埠："
    ls -l /dev/cu.* 2>/dev/null || echo "  無"
    exit 1
fi

echo -e "${GREEN}✓ 找到 Arduino 裝置：${ARDUINO_PORT}${NC}\n"

# 設定 TCP 埠號
TCP_PORT=5555

# 檢查埠號是否已被佔用
if lsof -Pi :$TCP_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}警告：埠號 $TCP_PORT 已被佔用${NC}"
    echo "嘗試關閉現有連接..."
    pkill -f "socat.*$TCP_PORT" || true
    sleep 1
fi

# 啟動 socat（在背景執行）
echo "啟動 socat 轉發: $ARDUINO_PORT -> TCP:$TCP_PORT"
socat TCP-LISTEN:$TCP_PORT,reuseaddr,fork $ARDUINO_PORT,raw,echo=0 &
SOCAT_PID=$!

# 等待一秒確認 socat 成功啟動
sleep 1

if ! kill -0 $SOCAT_PID 2>/dev/null; then
    echo -e "${RED}錯誤：socat 啟動失敗${NC}"
    exit 1
fi

echo -e "${GREEN}✓ socat 已啟動 (PID: $SOCAT_PID)${NC}\n"

# 啟動 Docker Compose
echo "啟動 Docker 容器..."
docker-compose -f docker-compose.macos.yml up --build -d

# 等待容器啟動
sleep 2

# 顯示日誌
echo -e "\n${GREEN}=== 容器日誌 ===${NC}"
docker-compose -f docker-compose.macos.yml logs --tail=20

echo -e "\n${GREEN}=== 啟動完成 ===${NC}"
echo "MCP Server 正在運行於: http://localhost:2000"
echo ""
echo "查看即時日誌："
echo "  docker-compose -f docker-compose.macos.yml logs -f"
echo ""
echo "停止服務："
echo "  docker-compose -f docker-compose.macos.yml down"
echo "  pkill -f 'socat.*$TCP_PORT'"
echo ""
echo -e "${YELLOW}注意：請保持此終端視窗開啟，或按 Ctrl+Z 然後執行 'bg' 將 socat 置於背景${NC}"
echo ""

# 等待 socat 程序（會保持在前景）
wait $SOCAT_PID

