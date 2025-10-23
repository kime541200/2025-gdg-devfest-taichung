import shutil, json, re
from rich import print as rprint
from typing import Optional


def print_centered_text(text: str, padding_char=' '):
    """
    在終端機中將文字水平置中並打印出來。

    Args:
        text (str): 要打印的文字。
        padding_char (str, optional): 用於填充的字符。預設為空格。

    Returns:
        None
    """
    # 取得終端機視窗尺寸
    terminal_width = shutil.get_terminal_size().columns
    # 計算讓印出文字"水平置中"所需的空格數
    padding = (terminal_width - len(text)) // 2
    # 印出"水平置中"的文字
    print(padding_char * max(padding, 0) + text + padding_char * max(padding, 0))


def print_detail(context, title: str = "", padding: str = "=", start_index: Optional[int] = None, end_index: Optional[int] = None, is_convo: bool = False):
    """
    打印詳細內容，可選擇顯示清單或對話，並在上下加上置中的標題與邊框。

    根據 `context` 的型別決定打印方式：
    - 如果是一般清單，可指定顯示的範圍（start_index 到 end_index）。
    - 如果是對話清單（清單中包含 dict，且有 'role' 和 'content'），會以對話形式顯示。
    - 若為其他資料型別，則直接以 rich 格式打印。

    Args:
        context (Any): 要打印的內容，可為清單（list）、對話清單（list of dict），或其他類型。
        title (str, optional): 置中顯示的標題文字，預設為空字串。
        padding (str, optional): 標題與底部分隔線用的填充字元，預設為 '='。
        start_index (Optional[int], optional): 要顯示清單的起始索引，預設為 None（從頭開始）。
        end_index (Optional[int], optional): 要顯示清單的結束索引，預設為 None（顯示到尾）。
        is_convo (bool, optional): 若設為 True，將清單內容視為對話並用對話格式打印，預設為 False。

    Returns:
        None
    """
    # Helper function to print list-type contexts.
    def _print_list(lst: list, start_index: Optional[int] = None, end_index: Optional[int] = None, is_convo: bool = False):
        total_len = len(lst)
        start = start_index if start_index is not None else 0
        end = end_index if end_index is not None else total_len
        sliced = lst[start:end]

        if start > 0:
            print(f"... ({start} items before)")

        if is_convo:
            _print_convo(sliced)
        else:
            rprint(sliced)

        if end < total_len:
            print(f"... ({total_len - end} items more)")

    # Helper function to print a conversation (list of dict items with "role" and "content").
    def _print_convo(convo: list):
        for c in convo:
            # Using single quotes outside so that inner double quotes work correctly.
            print(f'{c["role"]}>>> {c["content"]}\n')

    # Prepare and print header with the centered title.
    title_str = f" {title} " if title else ""
    print()
    print_centered_text(text=title_str, padding_char=padding)

    # Determine how to print the context depending on its type.
    if isinstance(context, list):
        _print_list(context, start_index, end_index, is_convo)
    else:
        rprint(context)

    # Print a footer border.
    print_centered_text(text="", padding_char=padding)
    print()


# ==================== Parse JSON ====================

def parse_json(text: str) -> str:
    """Extracts JSON content from a markdown-formatted string.

    This function takes a string that may contain markdown code blocks with JSON content
    and extracts just the JSON content. It specifically looks for code blocks that are
    marked with triple backticks and the 'json' language identifier.

    Args:
        text (str): A string that may contain markdown-formatted JSON content.

    Returns:
        str: The extracted JSON content as a string. If no JSON code block is found,
             returns the original input string.
    """
    if not "```json" in text:
        return text
    else:
        # Parsing out the markdown fencing
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line == "```json":
                json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
                json_output = json_output.split("```")[0]  # Remove everything after the closing "```"
                break  # Exit the loop once "```json" is found
        return json_output


def safe_json_loads(json_str: str) -> dict:
    """
    清理不合法的 JSON 字串內容，並轉換為 Python 字典。
    
    處理項目：
    - 移除非法控制字元（ASCII 0x00 ~ 0x1F，保留 \n, \r, \t）
    - 正確跳脫反斜線、雙引號
    """
    def _remove_illegal_control_chars(s: str) -> str:
        # 移除 JSON 不接受的控制字元（除了 \n \r \t）
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)

    def _escape_special_json_chars(s: str) -> str:
        # 注意：順序很重要，先跳脫反斜線，後處理其他
        s = s.replace('\\', '\\\\')  # 跳脫反斜線
        s = s.replace('"', '\\"')    # 跳脫雙引號
        s = s.replace('\b', '\\b')
        s = s.replace('\f', '\\f')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s

    try:
        # 嘗試直接解析（最理想）
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 清理並重試
        cleaned = _remove_illegal_control_chars(json_str)
        escaped = _escape_special_json_chars(cleaned)
        try:
            return json.loads(escaped)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON decoding still failed after cleaning: {e}") from e

# ====================================================