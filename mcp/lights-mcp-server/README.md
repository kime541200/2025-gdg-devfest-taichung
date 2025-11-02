# Lights MCP Server

這個專案是一個基於 Model Context Protocol (MCP) 的伺服器，用於透過序列埠 (Serial Port) 控制連接到 Arduino 的燈。它提供了一組工具，讓 AI 代理能夠查詢燈的狀態、設定亮度以及獲取燈的數量。

## 功能

* **查詢燈光資訊 (get_lights_statuses)**：獲取所有連接燈的當前亮度資訊。
* **設定燈光亮度 (set_light_brightness)**：設定指定燈的亮度（0-100%）。
* **獲取燈光數量 (get_light_count)**：獲取系統中連接的燈的總數量。
* **設定燈光亮度 (set_light_brightness)**：設定指定燈光的亮度百分比（0-100%，0 為關閉，100 為最亮），可精細控制每個燈的亮度。
* **關閉燈光 (turn_off_light)**：將指定燈光的亮度設為 0%，等同於關閉該燈。
* **燈光閃爍 (blink_light)**：讓指定的燈以自訂次數及間隔閃爍，可用於提示或吸引注意力。

## 專案結構

```
.
├── .dockerignore
├── .gitignore
├── docker-compose.yml         # Linux 系統用的 Docker Compose 配置
├── docker-compose.macos.yml   # macOS 系統用的 Docker Compose 配置
├── Dockerfile
├── requirements.txt
├── start-macos.sh             # macOS 自動啟動腳本
├── stop-macos.sh              # macOS 停止腳本
└── src/
    ├── server.py              # MCP 伺服器核心邏輯（支援串口和 TCP 連接）
    └── models/
        └── auduino.py         # Pydantic 模型定義，用於資料驗證和序列化
```

## 設定與運行

### 前置條件

*   已安裝 Docker 和 Docker Compose。
*   已連接 Arduino 板，並燒錄了相應的控制燈光的程式碼。
*   確保 Arduino 的序列埠在主機上可見 (例如 `/dev/ttyACM0`)。

### Docker Compose 部署

使用 Docker Compose 可以輕鬆地部署和運行此 MCP 伺服器。根據你的作業系統，需要使用不同的配置方式：

#### Linux 系統

在 Linux 系統上，可以直接將 USB 裝置掛載到容器內。

1.  **確認序列埠**：
    先確認你的 Arduino 連接的序列埠：
    ```bash
    ls /dev/ttyACM*
    ```
    通常會顯示 `/dev/ttyACM0`。

2.  **使用預設的 docker-compose.yml**：
    在 `mcp/lights-mcp-server/` 目錄下運行：
    ```bash
    docker-compose up --build -d
    ```

3.  **檢查日誌**：
    ```bash
    docker-compose logs -f lights-mcp-server
    ```
    如果連接成功，你應該會看到類似 `Connect to Arduino(/dev/ttyACM0) success: Arduino Ready.` 的訊息。

#### macOS 系統

在 macOS 上，由於 Docker Desktop 的架構限制，無法直接將 USB 裝置掛載到容器內。需要使用 **socat** 進行網路轉發。

##### 方法一：使用自動化腳本（推薦）

我們提供了自動化腳本來簡化啟動流程：

1.  **安裝 socat**：
    ```bash
    brew install socat
    ```

2.  **連接 Arduino 並執行啟動腳本**：
    ```bash
    cd mcp/lights-mcp-server/
    ./start-macos.sh
    ```
    腳本會自動：
    - 檢測 Arduino 裝置
    - 啟動 socat 轉發
    - 啟動 Docker 容器
    - 顯示連接狀態

3.  **停止服務**：
    ```bash
    ./stop-macos.sh
    ```

##### 方法二：手動啟動

1.  **安裝 socat**：
    ```bash
    brew install socat
    ```

2.  **找到你的 Arduino 序列埠**：
    ```bash
    ls /dev/cu.usbmodem*
    ```
    例如可能顯示 `/dev/cu.usbmodem3101`。

3.  **啟動 socat 轉發**：
    在一個終端視窗中執行（保持該視窗開啟）：
    ```bash
    # 請將 /dev/cu.usbmodem3101 替換成你的實際裝置路徑
    socat TCP-LISTEN:5555,reuseaddr,fork /dev/cu.usbmodem3101,raw,echo=0
    ```
    這個命令會將序列埠的資料轉發到本機的 5555 埠。

4.  **使用 macOS 專用的 docker-compose 檔案**：
    在另一個終端視窗中，於 `mcp/lights-mcp-server/` 目錄下運行：
    ```bash
    docker-compose -f docker-compose.macos.yml up --build -d
    ```

5.  **檢查日誌**：
    ```bash
    docker-compose -f docker-compose.macos.yml logs -f lights-mcp-server
    ```
    如果連接成功，你應該會看到類似 `Connecting to Arduino via TCP: host.docker.internal:5555` 和 `Connect to Arduino via TCP success: Arduino Ready.` 的訊息。

6.  **停止服務**：
    ```bash
    docker-compose -f docker-compose.macos.yml down
    pkill -f "socat.*5555"
    ```

**注意事項**：
- socat 轉發程式必須持續運行，關閉後容器將無法與 Arduino 通訊。
- 如果更換 USB 埠或重新插拔 Arduino，需要重新啟動 socat 命令。
- 你可以將 socat 命令寫成腳本或使用 `launchd` 設為開機自動啟動。

### 直接運行 (非 Docker)

如果你想在本地環境直接運行伺服器，請確保你已安裝 `requirements.txt` 中列出的所有依賴項。

1.  **安裝依賴**：
    ```bash
    pip install -r requirements.txt
    ```

2.  **運行伺服器**：
    ```bash
    python -m src.server --host 0.0.0.0 --port 2828
    ```

## MCP 工具

此 MCP 伺服器暴露了以下工具供 AI 代理使用：

### `get_lights_statuses(light_id: Optional[int] = None)`

* **描述**：獲取所有燈的狀態資訊，或是指定某一顆燈的狀態。
* **參數**：
    * `light_id` (Optional[int])：指定要查詢的燈的 ID，如未指定則回傳所有燈的狀態。ID 從 0 開始。
* **用途**：通常在調整燈光亮度後，使用此工具確認每個燈的實際狀態。
* **回傳**：JSON 格式的燈光資訊列表，包含每個燈的 `light_id` 及 `brightness`（0-100 之間），或是單一燈的資訊。
* **函式行為**：會從 Arduino 讀取燈光狀態，轉換後以友善格式回傳，若查詢不存在的 ID 則回傳錯誤資訊

### `set_light_brightness(light_id: int, brightness: int)`

* **描述**：設定指定燈光的亮度百分比。
* **參數**：
    * `light_id` (int)：要設定的燈的 ID，從 0 開始。
    * `brightness` (int)：預期設定的亮度百分比（0~100，0=關閉, 100=最亮）。
* **用途**：調整某一顆燈的亮度，可與 `get_lights_statuses()` 搭配確認結果。
* **回傳**：字串訊息，說明對應燈已被設定為多少百分比亮度。若傳入參數不符規定，會回傳說明錯誤的訊息。
* **函式行為**：會將百分比轉換為 Arduino 所需的 0~255 亮度值，發送控制命令至指定燈

### `get_light_count()`

* **描述**：取得目前系統連接的燈的數量。
* **參數**：無
* **用途**：當你發現錯誤訊息出現 `id` 可選範圍不正確時，例如 `[0-0]`，應先調用此工具確認實際燈數。
* **回傳**：整數，表示目前系統內燈的數量。例如 `3` 代表共 3 顆燈。
* **函式行為**：從 Arduino 查詢燈數並儲存於服務狀態，後續工具皆據此判斷 ID 合法範圍。若查詢失敗則回傳錯誤資訊。

### `turn_on_light(light_id: int)`

* **描述**：將指定燈打開（設為 100% 亮度）。
* **參數**：
    * `light_id` (int)：要打開的燈的 ID，從 0 開始。
* **回傳**：字串訊息，說明燈已被打開（亮度 100%），若錯誤則回傳錯誤說明。
* **函式行為**：向指定燈傳送 100% 亮度的命令。

### `turn_off_light(light_id: int)`

* **描述**：將指定燈關閉（設為 0% 亮度）。
* **參數**：
    * `light_id` (int)：要關閉的燈的 ID，從 0 開始。
* **回傳**：字串訊息，說明燈已被關閉（亮度 0%），若錯誤則回傳錯誤說明。
* **函式行為**：向指定燈傳送 0% 亮度的命令。

### `blink_light(light_id: int, times: int, interval: float = 0.5)`

* **描述**：讓指定的燈閃爍指定次數與間隔時間。
* **參數**：
    * `light_id` (int)：目標燈的 ID，從 0 開始。
    * `times` (int)：閃爍次數，必須為正整數。
    * `interval` (float)：每次亮滅的間隔秒數，預設為 0.5 秒。
* **回傳**：字串訊息，說明閃爍動作是否成功，或錯誤說明。
* **函式行為**：將燈打開及關閉依指定次數與間隔重複進行。