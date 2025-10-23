from pydantic import BaseModel, Field

class ToolFilterDynamicConfig(BaseModel):
    """Define a dynamic tool filter function via module and function path."""
    module: str = Field(..., description="Module path, e.g., 'my_package.filters'")
    function: str = Field(..., description="Function name inside the module.")
