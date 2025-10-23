from openai import AsyncOpenAI
from typing import Optional
from pydantic import BaseModel, Field

from ..openai.Agents import AgentModelSettings

class ModelSet(BaseModel):
    main_client: AsyncOpenAI = Field(
        ..., 
        description="AsyncOpenAI client for the main model, typically used for high-quality, final outputs."
    )
    main_model: str = Field(
        ..., 
        description="Name or ID of the main model used for primary reasoning and output generation."
    )
    main_model_settings: Optional[AgentModelSettings] = Field(
        None, 
        description="Optional configuration for the main model, including parameters like temperature, max tokens, etc."
    )
    fast_client: AsyncOpenAI = Field(
        ..., 
        description="AsyncOpenAI client for the fast model, optimized for quick, lower-cost responses."
    )
    fast_model: str = Field(
        ..., 
        description="Name or ID of the fast model used for rapid responses and lightweight tasks."
    )
    fast_model_settings: Optional[AgentModelSettings] = Field(
        None, 
        description="Optional configuration for the fast model, used to customize its behavior and output quality."
    )
    think_client: AsyncOpenAI = Field(
        ..., 
        description="AsyncOpenAI client for the think model, designed for deep reasoning and complex problem solving."
    )
    think_model: str = Field(
        ..., 
        description="Name or ID of the think model, typically used for tasks requiring extended analysis or planning."
    )
    think_model_settings: Optional[AgentModelSettings] = Field(
        None, 
        description="Optional configuration for the think model, allowing fine-tuning of behavior for advanced reasoning tasks."
    )
    
    class Config:
        arbitrary_types_allowed=True