from __future__ import annotations

from typing import Literal, Optional, Dict
from pydantic import BaseModel, Field

from openai.types.shared import Reasoning


class AgentModelSettings(BaseModel):
    """Settings to use when calling an LLM.

    This class holds optional model configuration parameters (e.g. temperature,
    top_p, penalties, truncation, etc.).
    Not all models/providers support all of these parameters,
    so please check the API documentation for the specific model and provider you are using.
    """

    temperature: Optional[float] = Field(None, description="The temperature to use when calling the model.")
    top_p: Optional[float] = Field(None, description="The top_p to use when calling the model.")
    frequency_penalty: Optional[float] = Field(None, description="The frequency penalty to use when calling the model.")
    presence_penalty: Optional[float] = Field(None, description="The presence penalty to use when calling the model.")
    tool_choice: Optional[Literal["auto", "required", "none"] | str] = Field(None, description="The tool choice to use when calling the model.")
    parallel_tool_calls: Optional[bool] = Field(None, description="Whether to use parallel tool calls when calling the model.")
    truncation: Optional[Literal["auto", "disabled"]] = Field(None, description="The truncation strategy to use when calling the model.")
    max_tokens: Optional[int] = Field(None, description="The maximum number of output tokens to generate.")
    reasoning: Optional[Reasoning] = Field(None, description="Configuration options for reasoning models.")
    metadata: Optional[Dict[str, str]] = Field(None, description="Metadata to include with the model response call.")
    store: Optional[bool] = Field(None, description="Whether to store the generated model response for later retrieval.")

    def resolve(self, override: AgentModelSettings | None) -> AgentModelSettings:
        """Produce a new ModelSettings by overlaying any non-None values from the
        override on top of this instance."""
        if override is None:
            return self

        # Use dict() to extract values while preserving field names
        current = self.model_dump(exclude_unset=True)
        overrides = override.model_dump(exclude_unset=True)

        # Merge overrides into current, preferring values from override
        merged = {**current, **{k: v for k, v in overrides.items() if v is not None}}
        return AgentModelSettings(**merged)
