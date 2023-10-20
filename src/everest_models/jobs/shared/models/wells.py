import datetime
from typing import Dict, Iterable, Iterator, Optional, Tuple

from pydantic import Field, validator

from everest_models.jobs.shared.models import BaseConfig
from everest_models.jobs.shared.models.operation import (
    Operation,
    OperationType,
    update_legacy_operations,
)


class Well(BaseConfig):
    readydate: Optional[datetime.date] = None
    completion_date: Optional[datetime.date] = None
    drill_time: Optional[int] = None
    name: str = Field(..., allow_mutation=False)
    ops: Tuple[OperationType, ...] = Field(default_factory=tuple)

    def missing_templates(self) -> Iterator[Operation]:
        return ((op.opname, op.date) for op in self.ops if op.template is None)

    def __hash__(self):
        return hash(self.name)

    @validator("drill_time")
    def is_positive_drill_time(cls, drill_time: Optional[int]) -> Optional[int]:
        if drill_time is not None and drill_time <= 0:
            ValueError("Drill_time must be greater than 0")
        return drill_time

    # remove ones deprecation event is over
    @validator("ops")
    def legacy_operations(cls, ops):
        return update_legacy_operations(ops)


class WellConfig(BaseConfig):
    __root__: Tuple[Well, ...]

    def __iter__(self) -> Iterator[Well]:
        return iter(self.__root__)

    def __getitem__(self, item) -> Well:
        return self.__root__[item]

    def to_dict(self) -> Dict[str, Well]:
        return {well.name: well for well in self}

    def set_wells(self, value: Iterable):
        self.__root__ = tuple(value)

    def __len__(self) -> int:
        return len(self.__root__)
