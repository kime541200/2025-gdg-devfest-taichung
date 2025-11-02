# Build llama.cpp on macOS from scratch

這份筆記將引導您如何在搭載 Apple Silicon (M1, M2, M3, M4 等) 的 macOS 環境下，從零開始建置 (build) `llama.cpp`。

`llama.cpp` 專案近期已將其建置系統從 `make` 全面升級為 `CMake`。本手冊將採用最新的 `CMake` 流程，確保您能成功編譯並獲得針對硬體（特別是 Metal GPU）最佳化的版本。

## 1. 事前準備：安裝開發環境

在開始之前，我們需要安裝三個必要的工具：Xcode Command Line Tools、Homebrew 以及 CMake。

### 步驟 1.1：安裝 Xcode Command Line Tools

這是 Apple 官方的開發工具包，包含了編譯器等基礎工具。

打開「終端機」（Terminal）並執行：

```bash
xcode-select --install

```

- 如果系統跳出視窗，請點擊「安裝」。
- 如果系統顯示 `note: Command line tools are already installed`，則表示已安裝，可直接進行下一步。

### 步驟 1.2：安裝 Homebrew

Homebrew 是 macOS 上最強大的套件管理員，是安裝開發工具的首選。

首先，檢查是否已安裝 Homebrew：

```bash
brew --version

```

- 如果顯示版本號，請跳至步驟 1.3。
- 如果顯示 `command not found`，請執行以下指令安裝 Homebrew：
安裝過程會引導您操作，可能需要輸入您的 Mac 登入密碼。
    
    ```bash
    /bin/bash -c "$(curl -fsSL <https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh>)"
    
    ```
    

### 步驟 1.3：安裝 CMake

現在，我們使用 Homebrew 來安裝 `CMake` 這個建置工具。

```bash
brew install cmake

```

## 2. 建置 llama.cpp

完成事前準備後，就可以開始編譯 `llama.cpp`。

### 步驟 2.1：下載 llama.cpp 原始碼

使用 `git` 從 GitHub 複製最新的專案原始碼。

```bash
# 複製專案，這會建立一個名為 "llama.cpp" 的資料夾
git clone <https://github.com/ggml-org/llama.cpp>

# 進入該資料夾
cd llama.cpp

```

### 步驟 2.2：使用 CMake 設定專案並編譯

這是新的核心步驟。我們將在一個獨立的 `build` 目錄中進行所有編譯工作，以保持原始碼目錄的乾淨。

```bash
# 1. 建立一個名為 build 的資料夾
mkdir build

# 2. 進入這個新的 build 資料夾
cd build

# 3. 執行 CMake 進行設定，並明確啟用 Metal GPU 加速
#    ".." 代表原始碼在上一層目錄
#    "-DLLAMA_METAL=ON" 是啟用 Apple Metal 的關鍵參數
cmake .. -DLLAMA_METAL=ON

# 4. 執行 make 進行編譯
make

```

編譯過程會持續幾分鐘。只要最後沒有顯示 "error" 字樣，就代表成功了。

## 3. 檔案位置與執行

使用 `CMake` 編譯後，所有產生的執行檔都會被整齊地放在特定目錄中。

- **執行檔位置**：`llama.cpp/build/bin/`
- **主要程式**：`main`, `server`, `quantize` 等都在這裡。

**如何執行：**
所有建置好的應用都會放在 `llama.cpp/build/bin`，接下來就可以使用該目錄下的應用執行，例如：

```bash
# Use a local model file
llama-cli -m my_model.gguf

# Or download and run a model directly from Hugging Face
llama-cli -hf ggml-org/gemma-3-1b-it-GGUF

# Launch OpenAI-compatible API server
llama-server -hf ggml-org/gemma-3-1b-it-GGUF
```

## 4. 後續維護：更新與移除

### 如何更新版本？

若要將 `llama.cpp` 更新至最新版本，請依序執行以下指令：

```bash
# 1. 回到專案根目錄
cd ..

# 2. 從 GitHub 拉取最新的程式碼變更
git pull

# 3. 再次進入 build 目錄
cd build

# 4. 重新執行 cmake 和 make 來編譯新版本
cmake .. -DLLAMA_METAL=ON
make

```

### 如何完整移除？

由於所有編譯後的檔案都在 `llama.cpp` 資料夾內，移除它非常簡單。

**方法：使用 Finder (最安全)**

1. 找到 `llama.cpp` 資料夾。
2. 將它拖曳到「垃圾桶」並清空即可。

**或者，如果您想做一次乾淨的重新編譯**，只需刪除 `build` 資料夾即可：

```bash
# 1. 回到專案根目錄
cd ..

# 2. 刪除整個 build 資料夾
rm -rf build

# 3. 之後可以重新執行步驟 2.2 來建立一個全新的 build

```

## 總結

恭喜！您現在已經掌握了在 macOS 上使用最新 `CMake` 流程來建置、管理 `llama.cpp` 的完整方法。