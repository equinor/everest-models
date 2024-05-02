from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ConfigDict, Field, FilePath, PlainSerializer, model_validator
from typing_extensions import Annotated, TypedDict

from everest_models.jobs.shared.converters import path_to_str

from ..validators import validate_no_extra_fields
from .base_config import ModelConfig
from .phase import PhaseEnum


class Tokens(TypedDict, total=False):
    phase: PhaseEnum
    rate: float


class OperationDict(TypedDict):
    date: date
    name: str
    template: Optional[Path]
    tokens: Tokens


class Operation(ModelConfig):
    model_config = ConfigDict(extra="allow", frozen=False, validate_assignment=True)

    date: Annotated[date, Field(description="", frozen=True)]
    opname: Annotated[
        str,
        Field(description="Operation Name", frozen=True),
    ]
    template: Annotated[
        FilePath,
        PlainSerializer(path_to_str),
        Field(default=None, description="File path to jinja template"),
    ]

    tokens: Annotated[
        Tokens,
        Field(
            default_factory=dict,
            description="A <key:value> mapping, Note! 'phase' and 'rate' keys are preserved.",
            examples=[{"phase": "WATER", "rate": 0.35, "<token>": "<value>"}],
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def no_extra_based_fields(cls, values: Dict[str, Any]) -> OperationDict:
        for key in filter(lambda x: x in values, ("phase", "rate")):
            values.setdefault("tokens", {})[key] = values.pop(key)

        validate_no_extra_fields(
            "date", "opname", "template", "tokens", values=iter(values)
        )
        return OperationDict(**values)
