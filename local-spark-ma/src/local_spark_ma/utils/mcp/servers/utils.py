from agents.mcp import MCPServer, MCPServerStdio, MCPServerSse, MCPServerStreamableHttp, ToolFilter
from agents.mcp import create_static_tool_filter
from typing import Optional, Union

from ....models.mcp.MCP import MCPServerConfig, MCPTransport
from ....models.mcp.ToolFilterStaticConfig import ToolFilterStaticConfig
from ....models.mcp.ToolFilterDynamicConfig import ToolFilterDynamicConfig
from ....helpers.helpers import print_detail

def _set_tool_filter(tool_filter_config: Optional[Union[ToolFilterStaticConfig, ToolFilterDynamicConfig]] = None) -> ToolFilter:
    """設定 MCP server 的工具過濾器"""
    if isinstance(tool_filter_config, ToolFilterStaticConfig):
        return create_static_tool_filter(allowed_tool_names=tool_filter_config.allowed_tool_names, blocked_tool_names=tool_filter_config.blocked_tool_names)
    elif isinstance(tool_filter_config, ToolFilterDynamicConfig):   # TODO: 動態過濾器還沒測試過
        import importlib          
        module = importlib.import_module(tool_filter_config.module)
        filter_func = getattr(module, tool_filter_config.function)
        return filter_func
    else:
        return None


def configure_mcp_server(mcp_server_config: MCPServerConfig) -> MCPServer:
    """配置 MCP server"""
    if mcp_server_config.transport == MCPTransport.STDIO:            
        return MCPServerStdio(
            params=mcp_server_config.stdio_config.params.model_dump(),
            cache_tools_list=mcp_server_config.stdio_config.cache_tools_list,
            name=mcp_server_config.stdio_config.name,
            client_session_timeout_seconds=mcp_server_config.stdio_config.client_session_timeout_seconds,
            use_structured_content=mcp_server_config.stdio_config.use_structured_content,
            tool_filter=_set_tool_filter(mcp_server_config.stdio_config.tool_filter_config)
            )
    elif mcp_server_config.transport == MCPTransport.SSE:
        return MCPServerSse(
            params=mcp_server_config.sse_config.params.model_dump(),
            cache_tools_list=mcp_server_config.sse_config.cache_tools_list,
            name=mcp_server_config.sse_config.name,
            client_session_timeout_seconds=mcp_server_config.sse_config.client_session_timeout_seconds,
            use_structured_content=mcp_server_config.sse_config.use_structured_content,
            tool_filter=_set_tool_filter(mcp_server_config.sse_config.tool_filter_config)
            )
    elif mcp_server_config.transport == MCPTransport.STREAMABLE_HTTP:
        return MCPServerStreamableHttp(
            params=mcp_server_config.streamable_http_config.params.model_dump(),
            cache_tools_list=mcp_server_config.streamable_http_config.cache_tools_list,
            name=mcp_server_config.streamable_http_config.name,
            client_session_timeout_seconds=mcp_server_config.streamable_http_config.client_session_timeout_seconds,
            use_structured_content=mcp_server_config.streamable_http_config.use_structured_content,
            tool_filter=_set_tool_filter(mcp_server_config.streamable_http_config.tool_filter_config)
            )
    else:
        raise ValueError(f"Invalid MCP server transport: {mcp_server_config.transport}")