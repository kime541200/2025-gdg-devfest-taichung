import json
import requests
from agents.mcp import MCPServerSse, ToolFilter
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Union
from .ToolFilterStaticConfig import ToolFilterStaticConfig
from .ToolFilterDynamicConfig import ToolFilterDynamicConfig


class SseParams(BaseModel):
    """Mirrors the params in `mcp.client.sse.sse_client`."""
    url: str = Field(..., description="The URL of the server.")
    headers: Optional[Dict[str, str]] = Field(None, description="The headers to send to the server.")
    timeout: Optional[float] = Field(None, description="The timeout for the HTTP request. Defaults to 5 seconds.")
    sse_read_timeout: Optional[float] = Field(None, description="The timeout for the SSE connection, in seconds. Defaults to 5 minutes.")
    
    @model_validator(mode="after")
    def chk_sse_alive(self):
        url = self.url
        # 合併必要 headers
        hdrs = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            **(self.headers or {}),
        }
        session = requests.Session()
        resp = None
        try:
            # 初始化 payload
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
            # 發送 POST 並開啟 SSE 流
            resp = session.post(
                url,
                json=payload,
                headers=hdrs,
                timeout=self.timeout,
                stream=True
            )
            if resp.status_code != 200:
                raise ValueError(f"SSE initialize 失敗 HTTP {resp.status_code}")
            # 從 SSE 事件流中讀到第一筆帶 result 的 data
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                msg = json.loads(line[len("data:"):].strip())
                if "result" in msg:
                    break
            else:
                raise ValueError("未在 SSE 事件流中收到 initialize result")
            return self

        finally:
            # 先關 response，再關 session，確保所有 socket 釋放
            if resp is not None:
                try: resp.close()
                except: pass
            session.close()
    

class MCPSseServerConfig(BaseModel):
    """Mirrors the params in `agents.mcp.MCPServerSse`"""
    params: SseParams = Field(..., description="The params that configure the server.")
    cache_tools_list: bool = Field(False, description="Whether to cache the tools list.")
    name: Optional[str] = Field(None, description="A readable name for the server. If not provided, we'll create one from the command.")
    client_session_timeout_seconds: Optional[float] = Field(5, description="the read timeout passed to the MCP ClientSession.")
    use_structured_content: bool = Field(False, description="Whether to use `tool_result.structured_content` when calling an MCP tool.")
    tool_filter_config: Optional[Union[ToolFilterStaticConfig, ToolFilterDynamicConfig]] = Field(None, description="The tool filter to use for filtering tools.")