from pydantic import BaseModel, Field
from typing import Optional

class ToolFilterStaticConfig(BaseModel):
    """Mirrors `agents.mcp.ToolFilterStatic`"""
    allowed_tool_names: Optional[list[str]] = Field(None, description="Optional list of tool names to allow (whitelist).")
    blocked_tool_names: Optional[list[str]] = Field(None, description="Optional list of tool names to exclude (blacklist).")