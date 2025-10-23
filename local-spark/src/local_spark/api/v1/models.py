import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List

from ...models.open_webui.models import OpenWebUI_Model, OpenWebUI_ListModelsOutput

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/models", tags=["Models"])


@router.get("/", response_model=OpenWebUI_ListModelsOutput, name="list_models", summary="列出可用模型")
async def a_list_models():
    """
    List the available models
    """
    _logger.info("Got the request of model list")
    # Append the functions here
    models: List[OpenWebUI_Model] = [
        OpenWebUI_Model(
            id=f"LOCAL-SPARK:0.0.0",
            name=f"LOCAL-SPARK",
        )
    ]
    
    response=OpenWebUI_ListModelsOutput(data=models)

    _logger.info(f"Reply the model list: {response.model_dump()}")
    return JSONResponse(content=response.model_dump())