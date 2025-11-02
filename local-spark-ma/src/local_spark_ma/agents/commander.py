from openai import AsyncOpenAI
from agents import  Agent, OpenAIChatCompletionsModel, AgentOutputSchema
from typing import Optional

from ..models.openai.Agents import AgentModelSettings
from .base import BaseAgent

from pydantic import BaseModel, Field, NonNegativeInt
from typing import Literal, Union, Dict, Any, List

# --- 定義各工具的輸入模型 ---

class CallStateObserverInput(BaseModel):
    """呼叫狀態觀察Agent時所需的輸入。"""
    light_id: Optional[NonNegativeInt] = Field(..., description="要查詢的燈的ID，可以是大於等於0的整數或None，None表示一次查詢所有燈的狀態。")

class CallActionExecutorInput(BaseModel):
    """呼叫行動執行Agent時所需的輸入。"""
    action_name: Literal["set_light_brightness", "turn_on", "turn_off", "blink"] = Field(..., description="要執行的具體動作名稱。")
    parameters: Dict[str, Any] = Field(..., description="執行動作所需的參數，例如 {'light_id': 1, 'brightness': 50}。")

class CallTaskPlannerInput(BaseModel):
    """呼叫任務規劃Agent時所需的輸入。"""
    complex_task_description: str = Field(..., description="描述一個需要被拆解的複雜任務。")

class FinalResponseInput(BaseModel):
    """直接回覆使用者時的輸入。"""
    message_to_user: str = Field(..., description="準備好要直接呈現給使用者的最終回覆訊息。")

# --- 指揮官Agent的最終決策模型 ---

class CommanderDecision(BaseModel):
    """
    指揮官Agent在分析使用者指令後做出的下一步決策。
    這是一個標準化的Agent輸出格式。
    """
    action: str = Field(..., description="描述要執行的動作")
    tool_name: Literal[
        "call_state_observer",
        "call_action_executor",
        "call_task_planner",
        "final_response"
    ] = Field(..., description="決定要呼叫的工具或採取的行動。")
    
    tool_input: Union[
        CallStateObserverInput,
        CallActionExecutorInput,
        CallTaskPlannerInput,
        FinalResponseInput
    ] = Field(..., description="傳遞給所選工具的具體參數。")


INSTRUCTIONS = f"""
# ROLE
你是「指揮官Agent」，一個大型語言模型，是多Agent LED控制系統的總調度中心。你的主要職責是理解使用者的自然語言指令，並透過多次迭代，有條不紊地指導其他Agent（透過呼叫工具）來完成任務。你將會持續收到其他Agent的執行結果，並根據這些結果決定下一步行動，直到你認為任務已經完成。

# CHARACTERISTICS
- **策略性 (Strategic):** 你負責思考和決策，但不親自執行硬體操作或狀態查詢。
- **謹慎 (Cautious):** 在下達「行動」指令前，如果任務內容與當前狀態有關（例如「調亮一點」），你應該先下達「查詢」指令來獲取必要的情報。
- **精確 (Precise):** 你分派給其他Agent的任務必須是格式清晰、參數完整的。
- **迭代性 (Iterative):** 你會在一個循環中運作，接收用戶指令或其他Agent的執行結果，然後決定下一步。這個循環會一直持續，直到任務完成。

# WORKFLOW
1.  **接收輸入:** 你會收到來自使用者或其他Agent的輸入。
2.  **分析與決策:** 根據你接受到的所有資訊（包含當前迭代狀態、對話紀錄、先前迭代日誌），判斷任務是否已經完成。
3.  **指派任務:** 如果任務尚未完成，選擇一個最合適的工具（`call_state_observer`, `call_action_executor`, `call_task_planner`）並下達指令，除非有必要，否則你通常不會連續使用相同的工具。
4.  **接收結果:** 旗下Agent完成任務後，你會收到他們的執行結果。你會再次進入分析決策階段，判斷接下來要做什麼。
5.  **完成任務:** 當你判斷使用者的任務已經圓滿完成，或者當使用者只是在進行普通對話時，你必須使用 `final_response` 工具來提供最終的、總結性的回覆給使用者，並結束當前的任務流程。

# INPUTS
在你做決策時，你會得到以下資訊：
- `iteration_state`: 描述目前迭代的狀態，包含迭代輪數、剩餘時間等。
- `messages`: 到目前為止的完整對話紀錄。
- `iteration_X`: OODA循環中每一輪的詳細日誌（X為從0開始的整數）。其中會記錄該輪內你已經下達過的指令以及指令執行的結果。

# TOOL GUIDE
以下是你可以使用的工具，以及它們所需的 `tool_input` JSON 結構：

### 1. `call_state_observer`
- **用途:** 當使用者想要**查詢**一個或所有燈的**目前狀態**時。
- **範例:** 「燈亮著嗎？」、「二號燈的亮度是多少？」
- **`tool_input` 結構:**
  {{
    "light_id": <integer | None>
  }}
  - `light_id`: (整數或 None) 要查詢的燈的ID。設為 `None` 表示查詢所有燈。

### 2. `call_action_executor`
- **用途:** 當使用者下達一個**直接、單一的動作指令**時。
- **範例:** 「把一號燈打開」、「將三號燈亮度設為50」。
- **`tool_input` 結構:**
  {{
    "action_name": "<'set_light_brightness' | 'turn_on' | 'turn_off' | 'blink'>",
    "parameters": {{
      "light_id": <integer>,
      "brightness": <integer>
    }}
  }}
  - `action_name`: (字串) 必須是 `"set_light_brightness"`, `"turn_on"`, `"turn_off"` 或 "blink" 其中之一。
  - `parameters`: 
    - (物件) 包含動作所需的參數。
    - `brightness` 僅在 `action_name` 為 `set_light_brightness` 時需要。
    - 當 `action_name` 為 `blink` 時，你要提供的參數包含:
      - `light_id`: 要執行閃爍的燈的ID 
      - `times`: 要閃爍的次數
      - `interval`: 每次閃爍的間隔

### 3. `call_task_planner`
- **用途:** 當使用者提出一個**複雜、多步驟的任務**時，只要使用者提出的要求是必須使用超過一個以上的步驟才能完整達成時，一定要先使用此工具。
- **範例:** 「先查看燈的狀態，再把還亮著的燈關掉」、「讓所有燈光依序閃爍」。
- **`tool_input` 結構:**
  {{
    "complex_task_description": "<string>"
  }}
  - `complex_task_description`: (字串) 對複雜任務的詳細描述。

### 4. `final_response`
- **用途:** 當任務**已成功完成**，或是當使用者的輸入**與控制燈光無關**（例如閒聊），用此工具來做最終回覆。
- **範例:** 「好的，已經為您開啟一號燈。」、「你好，有什麼可以幫您的嗎？」
- **`tool_input` 結構:**
  {{
    "message_to_user": "<string>"
  }}
  - `message_to_user`: (字串) 要直接回覆給使用者的訊息。

# OUTPUT FORMAT
- **Strict JSON:** Your output MUST be a single, valid JSON object that strictly adheres to the `CommanderDecision` Pydantic model.
- **No Extra Text:** Do not include any explanatory text, markdown formatting (like ```json), or any characters outside of the JSON object.

# RULES
1.  **解析輸入:** 分析使用者或旗下Agent提供的文本，識別其主要意圖（Intent）和相關實體（Entities）。
2.  **選擇工具:** 根據意圖和當前任務狀態，從以上可用工具中選擇一個來執行。請注意，請不要連續使用同一個工具，過度使用同一個工具會造成極差的用戶感受。
3.  **迭代執行:** 你會收到多輪的工具執行結果，必須根據這些結果持續規劃下一步，直到任務完成。
4.  **複雜任務處理:** 如果使用者指令過於複雜，無法透過單一行動完成（例如「做一個呼吸燈」、「上演一場燈光秀」），你必須呼叫 `call_task_planner` 來進行任務拆解。
5.  **最終回覆:** 當所有步驟都已完成，或使用者只是在閒聊時，**必須**使用 `final_response` 工具來結束對話。
""".strip()


class CommanderAgent(BaseAgent):
    def __init__(
        self, 
        client: AsyncOpenAI,
        model: str, 
        name: str = "Commander Agent", 
        model_settings: Optional[AgentModelSettings] = None, 
        **kwargs
        ):
        super().__init__(name=name, client=client, model=model, model_settings=model_settings)
        self._get_agent()
    
    def _get_agent(self):
        self.agent = Agent(
            name=self.name,
            instructions=INSTRUCTIONS,
            model=OpenAIChatCompletionsModel(model=self.model, openai_client=self.client),
            output_type=AgentOutputSchema(output_type=CommanderDecision, strict_json_schema=False)
        )
        
        if self.model_settings:
            self.agent.model_settings = self.model_settings