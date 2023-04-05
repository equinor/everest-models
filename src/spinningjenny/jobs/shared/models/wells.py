import datetime
from typing import Dict, Iterable, Iterator, Optional, Tuple

from pydantic import Field, FilePath, ValidationError, validator

from spinningjenny.jobs.shared.models import BaseConfig, PhaseEnum


class Operation(BaseConfig):
    date: datetime.date
    opname: str
    phase: Optional[PhaseEnum] = None
    template: Optional[FilePath] = None
    rate: Optional[float] = None


class WellModel(BaseConfig):
    readydate: Optional[datetime.date] = None
    completion_date: Optional[datetime.date] = None
    drill_time: Optional[int] = None
    name: str = Field(..., allow_mutation=False)
    ops: Tuple[Operation, ...] = Field(default_factory=tuple)

    def missing_templates(self) -> Iterator[Operation]:
        return ((op.opname, op.date) for op in self.ops if op.template is None)

    def __hash__(self):
        return hash(self.name)

    @validator("drill_time")
    def is_positive_drill_time(cls, drill_time):
        if drill_time is not None and drill_time <= 0:
            ValidationError("Drill_time must be greater than 0")
        return drill_time


class WellListModel(BaseConfig):
    __root__: Tuple[WellModel, ...]

    def __iter__(self) -> Iterator[WellModel]:
        return iter(self.__root__)

    def __getitem__(self, item) -> WellModel:
        return self.__root__[item]

    def to_dict(self) -> Dict[str, WellModel]:
        return {well.name: well for well in self}

    def set_wells(self, value: Iterable):
        self.__root__ = tuple(value)

    def __len__(self) -> int:
        return len(self.__root__)
