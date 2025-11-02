from pydantic_settings import BaseSettings
from ..workflows.schema import WorkflowSchema

class Settings(BaseSettings):
    flow_schema: WorkflowSchema