from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Optional

from .Stdio import MCPStdioServerConfig
from .Sse import MCPSseServerConfig
from .StreamableHttp import MCPStremableHttpServerConfig


class MCPTransport(Enum):
    STDIO = 'stdio'
    SSE = 'sse'
    STREAMABLE_HTTP = 'streamable-http'


class MCPServerConfig(BaseModel):
    transport: MCPTransport = Field(MCPTransport.STDIO, description="The MCP server's transport mechanism")
    stdio_config: Optional[MCPStdioServerConfig] = Field(None, description="The config of STDIO MCP server")    
    sse_config: Optional[MCPSseServerConfig] = Field(None, description="The config for SSE MCP server")    
    streamable_http_config: Optional[MCPStremableHttpServerConfig] = Field(None, description="The config for Streamable HTTP MCP server")
    
    @model_validator(mode="after")
    def chk_values(self):
        if self.transport == MCPTransport.STDIO and not self.stdio_config:
            raise ValueError(f"Must set `stdio_config` if this is a STDIO MCP server")
        if self.transport == MCPTransport.SSE and not self.sse_config:
            raise ValueError(f"Must set `sse_config` if this is a SSE MCP server")
        if self.transport == MCPTransport.STREAMABLE_HTTP and not self.streamable_http_config:
            raise ValueError(f"Must set `streamable_http_config` if this is a STREAMABLE_HTTP MCP server")
        return self