from typing import Any, Dict, Protocol, Tuple

from pydantic import ConfigDict, Field, FilePath, PlainSerializer, model_validator
from typing_extensions import Annotated, TypedDict

from everest_models.jobs.shared.converters import path_to_str
from everest_models.jobs.shared.models import ModelConfig, PhaseEnum, Tokens
from everest_models.jobs.shared.validators import validate_no_extra_fields


class TemplateOpProtocol(Protocol):
    opname: str
    tokens: Tokens


class Keys(TypedDict, total=False):
    opname: str
    phase: PhaseEnum


class Template(ModelConfig):
    model_config = ConfigDict(extra="allow")
    file: Annotated[
        FilePath,
        PlainSerializer(path_to_str),
        Field(description="File path to jinja template"),
    ]
    keys: Annotated[
        Keys,
        Field(
            default_factory=dict,
            description="",
            examples=["{opname: KBD, phase: WATER, <field>: <value>}"],
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def no_extra_based_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        validate_no_extra_fields("file", "keys", values=iter(values))
        return values

    def matching_keys(self, other: TemplateOpProtocol) -> bool:
        keys = {"opname": other.opname, **other.tokens}
        phase = "phase"
        if (phase in keys) ^ (phase in self.keys):
            return False
        return set(self.keys).issubset(keys) and all(
            value == keys[key] for key, value in self.keys.items()
        )


class TemplateConfig(ModelConfig):
    templates: Tuple[Template, ...]
