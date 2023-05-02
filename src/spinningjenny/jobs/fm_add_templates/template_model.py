from typing import Optional, Protocol, Tuple

from pydantic import Field, FilePath

from spinningjenny.jobs.shared.models import BaseConfig, BaseFrozenConfig, PhaseEnum


class TemplateOpProtocol(Protocol):
    opname: str
    phase: Optional[PhaseEnum]


class Key(BaseFrozenConfig):
    opname: str
    phase: Optional[PhaseEnum] = None

    def __eq__(self, other: TemplateOpProtocol) -> bool:
        return other.opname == self.opname and other.phase == self.phase


class Template(BaseConfig):
    file: FilePath = Field(..., allow_mutation=False)
    keys: Key = Field(..., allow_mutation=False)
    is_utilized: bool = Field(default=False, allow_mutation=True, exclude=True)


class TemplateConfig(BaseFrozenConfig):
    templates: Tuple[Template, ...]
