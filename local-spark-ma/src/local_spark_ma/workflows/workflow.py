import contextlib, time, logging, traceback, json
from agents import Agent, Runner, gen_trace_id, trace, RawResponsesStreamEvent, RunResult
from openai.types.responses import ResponseCreatedEvent, ResponseTextDeltaEvent, ResponseCompletedEvent, ResponseReasoningSummaryTextDeltaEvent
from typing import List, Optional, AsyncGenerator, Dict
from enum import Enum

from ..models.chat.Chat import Message
from ..models.open_webui.models import OpenwebuiChatCompletionRequest, OpenwebuiChatCompletionChunk, OpenwebuiChatCompletionChunkChoice, OpenwebuiChatCompletionChunkChoiceDelta, SourceData
from ..helpers.helpers import print_detail, parse_json
from ..agents.observer import ObserverOutput
from .ooda_loop import OODALoop, AgentTypes

_logger = logging.getLogger(__name__)


def _get_oui_stream_chat_completion_chunk(
    stream_id: str, 
    created: float, 
    model: str, 
    delta: Optional[str] = None, 
    output_index: int = 0, 
    done: bool = False, 
    done_reason: Optional[str] = None,
    citation: Optional[SourceData] = None,
    ):
    if not delta:
        choice = None
    else:
        choice = OpenwebuiChatCompletionChunkChoice(
            index=output_index,
            delta=OpenwebuiChatCompletionChunkChoiceDelta(content=delta),
            finish_reason=done_reason
        )
    
    if not citation:
        chunk = OpenwebuiChatCompletionChunk(
            id=stream_id,
            choices=[choice] if choice else None,
            created=created,
            model=model,
            sources=None,
            done=done,
            done_reason=done_reason,
        )
        return f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
    else:
        chunk = OpenwebuiChatCompletionChunk(
            id=stream_id,
            choices=None,
            created=created,
            model=model,
            sources=[citation],
            done=done,
            done_reason=done_reason,
        )
        return f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"


async def _a_stream_to_oui(stream: Optional[AsyncGenerator]) -> AsyncGenerator[str, None]:
    stream_id=f"__fake_id__"
    created=int(time.time())
    model="__fake_model__"
    output_think_tag = False

    async for c in stream:
        if isinstance(c, str):
            yield _get_oui_stream_chat_completion_chunk(
                stream_id=stream_id, 
                created=created, 
                model=model, 
                delta=c,
                )
        elif isinstance(c, list) and len(c) > 0 and isinstance(c[0], SourceData):
            for citation in c:
                yield _get_oui_stream_chat_completion_chunk(
                    stream_id=stream_id, 
                    created=created, 
                    model=model, 
                    citation=citation
                    )
        elif isinstance(c, RawResponsesStreamEvent):
            if c.type == "raw_response_event":
                if isinstance(c.data, ResponseCreatedEvent):
                    stream_id = c.data.response.id
                    created = c.data.response.created_at
                    model = c.data.response.model
                elif isinstance(c.data, ResponseReasoningSummaryTextDeltaEvent):
                    # ----- 還沒輸出 <think> 標籤的話要先輸出一個 -----
                    if not output_think_tag:
                        yield _get_oui_stream_chat_completion_chunk(
                            stream_id=stream_id, 
                            created=created, 
                            model=model, 
                            output_index=c.data.output_index, 
                            delta="<think>\n", 
                            )
                        output_think_tag = True
                    yield _get_oui_stream_chat_completion_chunk(
                        stream_id=stream_id, 
                        created=created, 
                        model=model, 
                        output_index=c.data.output_index, 
                        delta=c.data.delta, 
                        )
                elif isinstance(c.data, ResponseTextDeltaEvent):
                    # ----- 已經輸出 <think> 標籤的話要先輸出一個 </thinkc> -----
                    if output_think_tag:
                        yield _get_oui_stream_chat_completion_chunk(
                            stream_id=stream_id, 
                            created=created, 
                            model=model, 
                            output_index=c.data.output_index, 
                            delta="</think>\n", 
                            )
                        output_think_tag = False
                    yield _get_oui_stream_chat_completion_chunk(
                        stream_id=stream_id, 
                        created=created, 
                        model=model, 
                        output_index=c.data.output_index, 
                        delta=c.data.delta, 
                        )
                elif isinstance(c.data, ResponseCompletedEvent):
                    yield _get_oui_stream_chat_completion_chunk(
                        stream_id=c.data.response.id, 
                        created=created,
                        model=model,
                        done=True if c.data.response.output[0].status == 'completed' else False,
                        done_reason=c.data.type
                        )


async def _a_run(convo: List[Message]) -> AsyncGenerator:
    ooda_loop = OODALoop()

    # ----- 設定 MCP server -----
    from ..server import flow_schema
    from ..utils.mcp.servers.utils import configure_mcp_server
    async with contextlib.AsyncExitStack() as stack:
        for mcp_server_config in flow_schema.mcp_server_configs:
            server = await stack.enter_async_context(configure_mcp_server(mcp_server_config))
            
            logging.info(f"Get MCP server:{server.name}")

            if server.name == "get_status":
                ooda_loop.agents[AgentTypes.OBSERVER].mcp_servers.append(server)
            
            elif server.name == "set_light":
                ooda_loop.agents[AgentTypes.EXECUTOR].mcp_servers.append(server)

        
        # ----- 實際開始串流 -----
        trace_id = gen_trace_id()
        yield '<think>\n'
        yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n"
        with trace(workflow_name="Local-spark-ma-demo", trace_id=trace_id):
            async for c in ooda_loop.a_run(convo=convo):
                yield c


async def a_workflow_agentic_chat(request: OpenwebuiChatCompletionRequest) -> AsyncGenerator[str, None]:
    try:
        result_stream = _a_run(convo=request.messages)
        async for c in _a_stream_to_oui(stream=result_stream):
            yield c

    except Exception as e:
        traceback.print_exc()
        _logger.error(f"Unexcepted error: {e}")
        return
