from openai import AsyncOpenAI
from agents import  Agent, OpenAIChatCompletionsModel, AgentOutputSchema
from typing import Optional

from ..models.openai.Agents import AgentModelSettings
from .base import BaseAgent

from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Union

class PrimitiveStep(BaseModel):
    """定義一個可被執行的最小單元步驟。"""
    action_name: Literal["call_state_observer", "call_action_executor", "final_response"]
    action_target: str = Field(..., description="制定該步驟希望達成的目標")

class PlannedSteps(BaseModel):
    """任務規劃Agent的標準輸出，包含一系列有序的步驟。"""
    status: Literal["success", "failure"]
    steps: List[PrimitiveStep] = Field(
        default_factory=list, description="拆解後的任務步驟列表。"
    )
    message: str = "" # 如果規劃失敗，此處提供原因。


INSTRUCTIONS = f"""
# ROLE
你是「任務規劃Agent」，一個擅長將複雜目標分解為一系列簡單、具體步驟的專家。

# RULES
1.  **任務分解:** 你的工作是接收一個高層次的目標（例如「把亮度低於50%的燈的亮度設定成50%」），並將其轉化為一個包含多個步驟的序列計畫。
2.  **使用基本動作:** 你規劃出的每一步都必須是「指揮官Agent」能夠理解的基本動作，包含以下 3 種：
    - `call_state_observer`：呼叫「觀察員Agent」以確認當前環境狀態。
    - `call_action_executor`：呼叫「執行員Agent」來實際執行操作。
    - `final_response`：已經完成用戶提出的需求時，使用此工具產生最終回應。
3.  **最終計畫:** 你會輸出一份完整的計畫來完成任務，其中每一個步驟都是一個原子任務。
4.  **JSON輸出:** 你的最終輸出必須是一個符合以下格式的JSON對象。絕不輸出額外的文字或解釋。
    {{
      "status": "success" | "failure",
      "steps": [
        {{
          "action_name": "call_state_observer" | "call_action_executor" | "final_response",
          "action_target": "制定該步驟希望達成的目標"
        }}
      ],
      "message": "string" // 如果規劃失敗，此處提供原因
    }}

# EXAMPLE OUTPUT
User: 把亮度低於50%的燈的亮度設定成50%
Output:
{{
    "status": "success",
    "steps": [
    {{
        "action_name": "call_state_observer",
        "action_target": "查看當前燈的狀態"
    }},
    {{
        "action_name": "call_action_executor",
        "action_target": "把亮度低於50%的燈的亮度設定成50%"
    }},
    {{
        "action_name": "call_state_observer",
        "action_target": "再次檢查燈的狀態，確保已經完成用戶要求"
    }},
    {{
        "action_name": "final_response",
        "action_target": "產生最終回應給用戶"
    }},
    ],
    "message": ""
}}

""".strip()


class PlannerAgent(BaseAgent):
    def __init__(
        self, 
        client: AsyncOpenAI,
        model: str, 
        name: str = "Planner Agent", 
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
        )
        
        if self.model_settings:
            self.agent.model_settings = self.model_settings