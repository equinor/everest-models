import sys
from typing import Any, Dict, Protocol, Tuple

from pydantic import Field, FilePath, root_validator

from spinningjenny.jobs.shared.models import BaseFrozenConfig, PhaseEnum
from spinningjenny.jobs.shared.models.operation import Tokens
from spinningjenny.jobs.shared.validators import validate_no_extra_fields

if sys.version_info.minor < 9:
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


class TemplateOpProtocol(Protocol):
    opname: str
    tokens: Tokens


class Keys(TypedDict, total=False):
    opname: str
    phase: PhaseEnum


class Template(BaseFrozenConfig):
    file: FilePath
    keys: Keys = Field(default_factory=dict)

    @root_validator(pre=True)
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
