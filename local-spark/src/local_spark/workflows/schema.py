from pydantic import BaseModel, Field
from typing import List
from ..models.settings.SystemSettings import SystemSetting
from ..models.agent_brain.AgentBrain import AgentBrain
from ..models.mcp.MCP import MCPServerConfig


class WorkflowSchema(BaseModel):
    system: SystemSetting
    agent_brains: List[AgentBrain] = Field(default_factory=list)
    mcp_server_configs: List[MCPServerConfig] = Field(default_factory=list, description="Agent 可以使用的MCP servers的配置")