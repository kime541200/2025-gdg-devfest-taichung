import requests
from datetime import timedelta
from agents.mcp import MCPServerStreamableHttp
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Union
from .ToolFilterStaticConfig import ToolFilterStaticConfig
from .ToolFilterDynamicConfig import ToolFilterDynamicConfig

class StreamableHttpParams(BaseModel):
    """Mirrors the params in `mcp.client.streamable_http.streamablehttp_client`."""
    url: str = Field(..., description="The URL of the server.")
    headers: Optional[Dict[str, str]] = Field(None, description="The headers to send to the server.")
    timeout: Optional[Union[timedelta, float]] = Field(None, description="The timeout for the HTTP request. Defaults to 5 seconds.")
    sse_read_timeout: Optional[Union[timedelta, float]] = Field(None, description="The timeout for the SSE connection, in seconds. Defaults to 5 minutes.")
    terminate_on_close: Optional[bool] = Field(None, description="Terminate on close")
    
    @model_validator(mode="after")
    def chk_values(self):
        """
        在 BaseModel(...) 建構完後立即呼叫 MCP initialize，
        並在完成後釋放所有 HTTP 連線。
        """
        url = self.url
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            **(self.headers or {}),
        }
        # 同步使用 requests.Session 管理連線
        session = requests.Session()  # 建立會話 :contentReference[oaicite:0]{index=0}
        resp = None
        try:
            # 構造 initialize payload
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "health-check", "version": "1.0"}
                }
            }
            # 處理 timedelta
            to = self.timeout
            timeout = to.total_seconds() if isinstance(to, timedelta) else to

            # 發送 POST initialize
            resp = session.post(url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                raise ValueError(f"initialize 呼叫失敗，HTTP {resp.status_code}")
            # 檢查 MCP-Session-Id header
            session_id = resp.headers.get("mcp-session-id")
            if not session_id:
                raise ValueError("initialize 回應缺少 Mcp-Session-Id header")
            return self

        finally:
            # 確保先關閉 response，再關閉 session，釋放所有底層 socket :contentReference[oaicite:1]{index=1}
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass
            session.close()
    

class MCPStremableHttpServerConfig(BaseModel):
    """Mirrors the params in `agents.mcp.MCPServerStreamableHttp`"""
    params: StreamableHttpParams = Field(..., description="The params that configure the server.")
    cache_tools_list: bool = Field(False, description="Whether to cache the tools list.")
    name: Optional[str] = Field(None, description="A readable name for the server. If not provided, we'll create one from the command.")
    client_session_timeout_seconds: Optional[float] = Field(5, description="the read timeout passed to the MCP ClientSession.")
    use_structured_content: bool = Field(False, description="Whether to use `tool_result.structured_content` when calling an MCP tool.")
    tool_filter_config: Optional[Union[ToolFilterStaticConfig, ToolFilterDynamicConfig]] = Field(None, description="The tool filter to use for filtering tools.")