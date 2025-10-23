from openai import AsyncOpenAI
from agents import  Agent, OpenAIChatCompletionsModel, AgentOutputSchema
from typing import Optional

from ..models.openai.Agents import AgentModelSettings
from .base import BaseAgent

from pydantic import BaseModel, Field, NonNegativeInt
from typing import Literal, Union, Dict, Any, List

class LightInfo(BaseModel):
    id: NonNegativeInt = Field(..., description="燈的編號")
    brightness: NonNegativeInt = Field(..., ge=0, le=255, description="目前的亮度(0-255)")

class ObserverOutput(BaseModel):
    """狀態觀察Agent的標準輸出格式。"""
    status: Literal["success", "failure"]
    light_states: List[LightInfo]
    message: str = "" # 用於回報錯誤訊息


INSTRUCTIONS = f"""
# ROLE
你是「狀態觀察Agent」，你的唯一職責是回報**燈的當前狀態**。

# RULES
1.  **唯讀:** 你絕對不能嘗試改變任何**燈的狀態**。
2.  **精確回報:** 你的回報必須是準確的JSON格式，其格式定義如下：
    {{
      "status": "success" | "failure",
      "light_states": [
        {{
          "id": integer,
          "brightness": integer // 亮度百分比 (0-100)
        }}
      ],
      "message": string // 用於回報錯誤訊息
    }}
3.  **拒絕無關請求:** 如果被要求執行非查詢任務，你必須回報錯誤並說明你的職責。
4.  **不與使用者對話:** 你的輸出是給指揮官Agent看的，不是給終端使用者。絕不輸出問候語或解釋。
""".strip()


class ObserverAgent(BaseAgent):
    def __init__(
        self, 
        client: AsyncOpenAI,
        model: str, 
        name: str = "Observer Agent", 
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