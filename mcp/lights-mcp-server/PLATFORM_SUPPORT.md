# 跨平台支援說明

## 問題背景

### Docker 在 macOS 上的架構限制

在 macOS 上使用 Docker 時，有一個重要的架構限制：**無法直接將 USB 裝置掛載到容器內**。

#### 為什麼會這樣？

1. **虛擬化層**：Docker 容器是基於 Linux 核心技術（cgroups, namespaces）的。macOS 使用的是 Darwin 核心，與 Linux 不同。

2. **Docker Desktop 的架構**：Docker Desktop for Mac 會在背景執行一個輕量級的 **Linux 虛擬機 (VM)**。

3. **隔離問題**：當你將 USB 裝置（如 Arduino）插入 Mac 時：
   - 裝置被 macOS 系統識別和管理
   - 這個裝置對於背後的 Linux VM 來說是**不可見**的
   - Docker Daemon（在 VM 內執行）找不到可以傳遞給容器的硬體裝置

**架構圖示**：
```
[Arduino USB 裝置]
        ↓
[macOS Host] ← 可以看到 /dev/cu.usbmodem3101
        ‖
    邊界 (無法直通)
        ‖
[Linux VM] ← 看不到 USB 裝置
        ↓
[Docker 容器]
```

### Linux 系統下的對比

在原生 Linux 系統上（或在 Linux VM 內直接運行 Docker Engine）：
```
[Arduino USB 裝置]
        ↓
[Linux Host] ← 看到 /dev/ttyACM0
        ↓ (可以使用 --device 掛載)
[Docker 容器] ← 直接訪問 /dev/ttyACM0
```

## 解決方案

### 使用 socat 進行網路轉發

我們採用的解決方案是將序列埠通訊轉換為網路通訊：

```
[Arduino USB]
      ↓
[macOS Host: /dev/cu.usbmodem3101]
      ↓
[socat] ← 監聽序列埠並轉發到 TCP port 5555
      ↓
[TCP: localhost:5555]
      ↓
[Docker 容器] ← 連接到 host.docker.internal:5555
      ↓
[MCP Server] ← 使用 pyserial 的 socket:// URL
```

### 技術實現細節

#### 1. socat 命令

```bash
socat TCP-LISTEN:5555,reuseaddr,fork /dev/cu.usbmodem3101,raw,echo=0
```

- `TCP-LISTEN:5555`: 監聽 TCP port 5555
- `reuseaddr`: 允許重複使用地址
- `fork`: 為每個連接創建新的進程
- `/dev/cu.usbmodem3101`: Arduino 序列埠
- `raw`: 原始模式（不進行任何轉換）
- `echo=0`: 禁用回顯

#### 2. pyserial 的 socket:// URL

pyserial 支援透過 socket URL 連接：

```python
import serial

# 傳統串口連接
ser = serial.Serial('/dev/ttyACM0', 9600)

# TCP 網路連接（透過 socat）
ser = serial.serial_for_url('socket://host.docker.internal:5555')
```

#### 3. 環境變數配置

透過環境變數來切換連接模式：

```yaml
# Linux 模式
environment:
  - SERIAL_USE_TCP=false
  - SERIAL_PORT=/dev/ttyACM0

# macOS 模式
environment:
  - SERIAL_USE_TCP=true
  - SERIAL_TCP_HOST=host.docker.internal
  - SERIAL_TCP_PORT=5555
```

## 程式碼修改說明

### 1. 自動偵測裝置

原本只支援 Linux 的 `ttyACM*`：

```python
def _find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "ttyACM" in port.device:
            return port.device
    return None
```

現在同時支援 macOS 的 `cu.usbmodem*` 和 `cu.usbserial*`：

```python
def _find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Linux
        if "ttyACM" in port.device:
            return port.device
        # macOS
        if "cu.usbmodem" in port.device or "cu.usbserial" in port.device:
            return port.device
    return None
```

### 2. 雙模式連接

```python
USE_TCP = os.getenv("SERIAL_USE_TCP", "false").lower() == "true"

if USE_TCP:
    # macOS + Docker: 透過 TCP 連接
    ser = serial.serial_for_url(f"socket://{TCP_HOST}:{TCP_PORT}", timeout=1)
else:
    # Linux + Docker 或直接運行: 直接串口連接
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
```

## 其他可能的解決方案

### 方案比較

| 解決方案 | 優點 | 缺點 | 適用場景 |
|---------|------|------|---------|
| **socat 網路轉發** | 簡單、可靠、性能好 | 需要額外運行 socat | ✅ 開發和生產環境 |
| **Lima (Linux VM)** | 支援 USB 直通 | 設定複雜、資源消耗高 | 需要多個 USB 裝置時 |
| **傳統虛擬機** | 完整的 USB 支援 | 非常重、設定複雜 | 需要低階硬體存取時 |
| **不使用 Docker** | 直接連接，簡單 | 失去容器化優勢 | 簡單開發環境 |

### 為什麼選擇 socat？

1. **輕量級**：只需要一個小工具，不需要額外的虛擬機
2. **性能好**：TCP 轉發的延遲幾乎可以忽略（< 1ms）
3. **可靠性高**：socat 是成熟穩定的工具
4. **易於自動化**：可以寫成腳本或服務
5. **保持容器化優勢**：仍然可以使用 Docker 的所有功能

## 使用場景

### Linux 生產環境

- 直接使用 `docker-compose.yml`
- USB 裝置直接掛載到容器
- 性能最佳，配置最簡單

### macOS 開發環境

- 使用 `docker-compose.macos.yml`
- 透過 socat 轉發
- 開發體驗與 Linux 一致

### 直接運行（不使用 Docker）

在 macOS 或 Linux 上都可以直接運行：

```bash
# 會自動偵測系統和串口
python -m src.server --host 0.0.0.0 --port 2828
```

## 潛在問題與解決

### 問題 1：socat 意外關閉

**現象**：容器無法連接到 Arduino

**解決**：
- 檢查 socat 是否還在運行：`ps aux | grep socat`
- 重新啟動 socat
- 考慮使用 launchd 將 socat 設為系統服務

### 問題 2：USB 裝置路徑變更

**現象**：重新插拔 Arduino 後路徑改變（如 `/dev/cu.usbmodem3101` → `/dev/cu.usbmodem3102`）

**解決**：
- 重新執行 `start-macos.sh` 腳本（會自動偵測新路徑）
- 或手動修改 socat 命令中的路徑

### 問題 3：端口被佔用

**現象**：`Address already in use`

**解決**：
```bash
# 找出佔用 5555 埠的程序
lsof -i :5555

# 終止舊的 socat 程序
pkill -f "socat.*5555"
```

## 測試驗證

### 驗證 socat 轉發

```bash
# 終端 1：啟動 socat
socat TCP-LISTEN:5555,reuseaddr,fork /dev/cu.usbmodem3101,raw,echo=0

# 終端 2：測試連接
nc localhost 5555
# 輸入任何內容，應該會發送到 Arduino
```

### 驗證容器連接

```bash
# 查看容器日誌
docker-compose -f docker-compose.macos.yml logs -f

# 應該看到：
# Connecting to Arduino via TCP: host.docker.internal:5555
# Connect to Arduino via TCP success: Arduino Ready.
```

## 參考資源

- [Docker Desktop for Mac 架構說明](https://docs.docker.com/desktop/install/mac-install/)
- [socat 官方文檔](http://www.dest-unreach.org/socat/)
- [pyserial URL handlers](https://pyserial.readthedocs.io/en/latest/url_handlers.html)
- [Docker host.docker.internal](https://docs.docker.com/desktop/networking/#i-want-to-connect-from-a-container-to-a-service-on-the-host)

