from pydantic import BaseModel, Field, PositiveInt, PositiveFloat
from typing import List
from ..models.settings.SystemSettings import SystemSetting
from ..models.agent_brain.AgentBrain import AgentBrain
from ..models.mcp.MCP import MCPServerConfig


class AgentLoopConstrian(BaseModel):
    max_iteration: PositiveInt = Field(10, description="OODA循環最大迭代次數")
    max_time: PositiveFloat = Field(10.0, description="Maximum time in minutes for research")
    per_agent_retry_max: PositiveInt = Field(3, description="同一個Agent重試次數上限(為了確保能呼叫工具的Agent最終輸出符合指定的格式)")



class WorkflowSchema(BaseModel):
    system: SystemSetting
    agent_brains: List[AgentBrain] = Field(default_factory=list)
    loop_constrain: AgentLoopConstrian = Field(default_factory=AgentLoopConstrian)
    mcp_server_configs: List[MCPServerConfig] = Field(default_factory=list, description="Agent 可以使用的MCP servers的配置")