import time
import subprocess
from mcp.client.stdio import StdioServerParameters
from agents.mcp import MCPServerStdio
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from .ToolFilterStaticConfig import ToolFilterStaticConfig
from .ToolFilterDynamicConfig import ToolFilterDynamicConfig


class MCPStdioServerConfig(BaseModel):
    """Mirrors the params in `agents.mcp.MCPServerStdio`"""
    params: StdioServerParameters = Field(..., description="The parameters of STDIO MCP server")
    cache_tools_list: bool = Field(False, description="Whether to cache the tools list.")
    name: Optional[str] = Field(False, description="A readable name for the server. If not provided, we'll create one from the command.")
    client_session_timeout_seconds: Optional[float] = Field(5, description="the read timeout passed to the MCP ClientSession.")
    use_structured_content: bool = Field(False, description="Whether to use `tool_result.structured_content` when calling an MCP tool.")
    tool_filter_config: Optional[Union[ToolFilterStaticConfig, ToolFilterDynamicConfig]] = Field(None, description="The tool filter to use for filtering tools.")
    
    @field_validator("params")
    def chk_params(cls, value: StdioServerParameters) -> StdioServerParameters:
        # 1. 啟動子進程
        proc = subprocess.Popen(
            [value.command, *value.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=value.env,
            cwd=str(value.cwd) if value.cwd else None,
            text=True,
            encoding=value.encoding,
            errors=value.encoding_error_handler,
        )

        try:
            # 2. 等待短暫時間，讓服務啟動
            time.sleep(0.1)

            # 3. 確認進程還在跑
            if proc.poll() is not None:
                raise ValueError("STDIO MCP server 無法啟動或已提早退出")

        finally:
            # 4. 立即終止並清理
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        return value