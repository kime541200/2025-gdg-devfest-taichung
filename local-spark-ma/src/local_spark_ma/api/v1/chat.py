import logging
import traceback
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ...models.open_webui.models import OpenwebuiChatCompletionRequest
from ...helpers.helpers import print_detail

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["Chat"])


@router.post("/completions", name="chat_completions", summary="完成對話", description="根據prompt完成對話")
async def a_chat_completions(oui_request: Request):
    request_json = await oui_request.json()
    print_detail(request_json)
    _logger.debug(f"Open-webui request detail: {request_json}")
    
    request = OpenwebuiChatCompletionRequest(**request_json)

    _logger.info(f"Got chat completion request: {request}")

    try:
        from ...workflows.workflow import a_workflow_agentic_chat
        if request.stream:
            generator = a_workflow_agentic_chat(request=request)
            return StreamingResponse(generator, media_type="text/event-stream")
        else:
            # TODO: 非串流輸出: 先把所有結果蒐集起來再一次回傳
            pass
                
    except Exception as e:
        traceback.print_exc()
        _logger.error(f"Fail to process the chat completion request: {str(e)}")