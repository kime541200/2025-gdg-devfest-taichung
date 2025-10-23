from pydantic import BaseModel, Field, PositiveInt
from typing import Optional
from enum import Enum
from ..openai.Openai import OpenaiConfig
from ..openai.Agents import AgentModelSettings


class BrainType(Enum):
    MAIN = "main"
    FAST = "fast"
    THINK = "think"


class AgentBrain(BaseModel):
    brain_type: BrainType = Field(default=BrainType.MAIN)
    llm_config: OpenaiConfig = Field(default_factory=OpenaiConfig, description="基本模型配置")
    model_settings: Optional[AgentModelSettings] = Field(None, description="額外參數設定，例如 temperature、max_tokens 等。")
    max_turn: PositiveInt = Field(10, description="Agent 重試次數上限")
    image_support: bool = Field(False, description="此模型是否能夠處理和理解影像")