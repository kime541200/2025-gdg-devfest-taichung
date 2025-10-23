from openai import AsyncOpenAI
from agents import  Agent, OpenAIChatCompletionsModel, AgentOutputSchema
from typing import Optional

from ..models.openai.Agents import AgentModelSettings
from .base import BaseAgent

from pydantic import BaseModel, Field
from typing import Literal

class ExecutionResult(BaseModel):
    """行動執行Agent的標準輸出格式。"""
    status: Literal["success", "failure"]
    message: str = Field(
        default="", description="如果失敗，這裡會包含錯誤原因。"
    )


INSTRUCTIONS = f"""
# ROLE
你是「行動執行Agent」，一個只會嚴格執行命令的機器人。

# RULES
1. **絕對服從:** 你必須精確執行收到的指令，不要有任何自己的想法或變動。
2. **不思考:** 你不負責規劃或決策。
3. **回報結果:** 任務完成後，立即回報執行結果（成功或失敗），使用以下JSON格式：
   ```json
   {{
     "status": "success" | "failure",
     "message": "string" // 如果失敗，這裡會包含錯誤原因。
   }}
   ```
4. **不與使用者對話:** 你的輸出是給指揮官Agent看的，不是給終端使用者。
5. 每次只調用一個工具，每調用完一個工具會立刻將結果回報。 
""".strip()


class ExecutorAgent(BaseAgent):
    def __init__(
        self, 
        client: AsyncOpenAI,
        model: str, 
        name: str = "Executor Agent", 
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