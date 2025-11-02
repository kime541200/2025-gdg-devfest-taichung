from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from agents import  ModelSettings
from typing import Optional

from ..models.openai.Agents import AgentModelSettings

class BaseAgent(ABC):
    def __init__(
        self, 
        name: str,
        client: AsyncOpenAI,
        model: str,
        model_settings: Optional[AgentModelSettings] = None,
        ):
        self.name = name
        self.client = client
        self.model = model
        self.model_settings = ModelSettings(**model_settings.model_dump()) if model_settings else None
        self._get_agent()
    
    @abstractmethod
    def _get_agent(self):
        pass