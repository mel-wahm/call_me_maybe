from pydantic import BaseModel
from typing import Any


class Parameter(BaseModel):
    type: Any


class F_Definition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Parameter]
    returns: dict[str, str]


class Fc_Result(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, Any]
