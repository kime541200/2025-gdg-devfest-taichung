import os, logging, traceback
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from .utils.config.util import load_configs
from .workflows.schema import WorkflowSchema

from .api.v1 import models as api_v1_models
from .api.v1 import chat as api_v1_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

flow_schema: Optional[WorkflowSchema] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = load_configs(config_file_path=os.getenv("FLOW_CONFIG"))

        from agents import  set_tracing_disabled
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY").startswith("sk-"):
            disabled_tracing = False
            logger.info("Enable OpenAI Agent Tracing")
        else:
            disabled_tracing = True
            logger.info("Disable OpenAI Agent Tracing")
        set_tracing_disabled(disabled=disabled_tracing)
        
        global flow_schema
        flow_schema = settings.flow_schema
        yield
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Initial FastAPI server error:\n{e}")
    finally:
        traceback.print_exc()
        logger.info(f"Shutdown FastAPI server")


app = FastAPI(
    lifespan=lifespan,
    title="local-spark",
    version="0.0.0",
    openapi_url="/openapi.json",
    docs_url=None,
    redoc_url=None,
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加入API路由
app.include_router(api_v1_models.router)
app.include_router(api_v1_chat.router)


@app.exception_handler(HTTPException)
async def a_http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

@app.get("/")
async def read_root():
    return {"message": "Welcome to `local-spark` API Server!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
