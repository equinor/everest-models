from typing import Any, Dict, Protocol, Tuple

from pydantic import Field, FilePath, model_validator
from typing_extensions import TypedDict

from everest_models.jobs.shared.models import BaseFrozenConfig, PhaseEnum
from everest_models.jobs.shared.models.operation import Tokens
from everest_models.jobs.shared.validators import validate_no_extra_fields


class TemplateOpProtocol(Protocol):
    opname: str
    tokens: Tokens


class Keys(TypedDict, total=False):
    opname: str
    phase: PhaseEnum


class Template(BaseFrozenConfig):
    file: FilePath
    keys: Keys = Field(default_factory=dict)

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


class TemplateConfig(BaseFrozenConfig):
    templates: Tuple[Template, ...]
