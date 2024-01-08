import datetime
from typing import Dict, Iterable, Iterator, Optional, Tuple

from pydantic import Field, RootModel, field_validator

from everest_models.jobs.shared.models import BaseConfig
from everest_models.jobs.shared.models.operation import (
    Operation,
    OperationType,
    update_legacy_operations,
)


class Well(BaseConfig):
    completion_date: Optional[datetime.date] = None
    drill_time: Optional[int] = None
    name: str = Field(..., frozen=True)
    ops: Tuple[OperationType, ...] = Field(default_factory=tuple)
    readydate: Optional[datetime.date] = None

    def missing_templates(self) -> Iterator[Operation]:
        return ((op.opname, op.date) for op in self.ops if op.template is None)

    def __hash__(self):
        return hash(self.name)

    @field_validator("drill_time")
    @classmethod
    def is_positive_drill_time(cls, drill_time: Optional[int]) -> Optional[int]:
        if drill_time is not None and drill_time <= 0:
            ValueError("Drill_time must be greater than 0")
        return drill_time

    # remove ones deprecation event is over
    @field_validator("ops")
    @classmethod
    def legacy_operations(cls, ops):
        return update_legacy_operations(ops)


class WellConfig(BaseConfig, RootModel):
    root: Tuple[Well, ...]

    def __iter__(self) -> Iterator[Well]:
        return iter(self.root)

    def __getitem__(self, item) -> Well:
        return self.root[item]

    def to_dict(self) -> Dict[str, Well]:
        return {well.name: well for well in self}

    def set_wells(self, value: Iterable):
        self.root = tuple(value)

    def __len__(self) -> int:
        return len(self.root)
