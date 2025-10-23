from pydantic import BaseModel, Field, NonNegativeInt
from typing import List

class LightInfo(BaseModel):
    light_id: NonNegativeInt = Field(..., description="燈的編號")
    brightness: NonNegativeInt = Field(..., ge=0, le=255, description="目前的亮度(0-255)")

class FetchLightsInfoOutput(BaseModel):
    infos: List[LightInfo] = Field(default_factory=list)